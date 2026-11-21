from datetime import datetime
from uuid import uuid4

from database.db import get_connection
from parking_data import ParkingSlot, ParkingRequest
from reallocation import submit_parking_request, reallocate_waiting_vehicle


def load_slots_from_database():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT slot_id, slot_number, slot_type, gate, status
            FROM parking_slots
        """)

        rows = cursor.fetchall()

        slots = []

        for slot_id, slot_number, slot_type, gate, status in rows:

            # Ignore blocked and maintenance slots
            if status != "available":
                continue

            # Extract parking zone from slot number (A01 -> A)
            zone = slot_number[0]

            slots.append(
                ParkingSlot(
                    slot_id=slot_number,
                    zone=zone,
                    slot_type=slot_type,
                    gate_distances={
                        "North Gate": 10 if gate == "North Gate" else 30,
                        "South Gate": 10 if gate == "South Gate" else 30
                    }
                )
            )

        return slots

    finally:
        connection.close()


def load_active_bookings():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                b.booking_id,
                b.vehicle_id,
                p.slot_number,
                v.vehicle_type,
                b.arrival_time,
                b.duration,
                b.destination_gate,
                b.requires_charging,
                b.status
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            LEFT JOIN parking_slots p ON b.slot_id = p.slot_id
            WHERE b.status IN ('pending', 'allocated', 'checked-in')
            ORDER BY b.arrival_time
        """)

        rows = cursor.fetchall()

        requests = []
        allocation = []

        for row in rows:
            (
                booking_id,
                vehicle_id,
                slot_number,
                vehicle_type,
                arrival_time,
                duration,
                destination_gate,
                requires_charging,
                status
            ) = row

            request = ParkingRequest(
                request_id=str(booking_id),
                vehicle_type=vehicle_type,
                arrival_time=datetime.fromisoformat(arrival_time),
                duration_minutes=duration * 60,
                destination_gate=destination_gate,
                requires_charging=bool(requires_charging)
            )

            requests.append(request)
            allocation.append(slot_number)

        return requests, allocation

    finally:
        connection.close()


def allocate_new_booking(
    user_id,
    vehicle_id,
    arrival_time,
    duration,
    destination_gate,
    requires_charging=False
):
    """
    Create a booking and allocate a suitable parking slot.
    Duration is in hours, as stored in the database.
    """

    if type(duration) is not int or duration <= 0:
        return False, "Duration must be a positive number of hours."

    try:
        arrival = datetime.fromisoformat(arrival_time)
    except (ValueError, TypeError):
        return False, "Invalid arrival time."

    if destination_gate not in ("North Gate", "South Gate"):
        return False, "Invalid destination gate."

    if not isinstance(requires_charging, bool):
        return False, "Invalid charging preference."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Verify that the user exists
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )
        if cursor.fetchone() is None:
            return False, "User not found."

        # Verify vehicle ownership and get vehicle type
        cursor.execute("""
            SELECT vehicle_type
            FROM vehicles
            WHERE vehicle_id = ? AND user_id = ?
        """, (vehicle_id, user_id))

        vehicle = cursor.fetchone()

        if vehicle is None:
            return False, "Vehicle does not belong to this user."

        vehicle_type = vehicle[0]

        if requires_charging and vehicle_type != "EV":
            return False, "Only EV vehicles can request charging."

        # Load currently usable parking slots
        slots = load_slots_from_database()

        # Load existing active bookings
        requests, allocation = load_active_bookings()

        # Create a unique temporary request ID
        request_id = "NEW-" + str(uuid4())

        new_request = ParkingRequest(
            request_id=request_id,
            vehicle_type=vehicle_type,
            arrival_time=arrival,
            duration_minutes=duration * 60,
            destination_gate=destination_gate,
            requires_charging=requires_charging
        )

        # Keep existing assignments fixed while checking a new request
        cancelled_ids = set()

        allocated = submit_parking_request(
            new_request,
            requests,
            allocation,
            slots,
            cancelled_ids
        )

        # Find the new request's allocated slot
        slot_number = allocation[-1] if allocated else None

        slot_db_id = None

        if slot_number is not None:
            cursor.execute("""
                SELECT slot_id
                FROM parking_slots
                WHERE slot_number = ?
                  AND status = 'available'
            """, (slot_number,))

            slot_row = cursor.fetchone()

            if slot_row is None:
                return False, "Selected parking slot is no longer available."

            slot_db_id = slot_row[0]

        # Insert the booking
        status = "allocated" if slot_db_id is not None else "pending"

        cursor.execute("""
            INSERT INTO bookings (
                user_id,
                vehicle_id,
                slot_id,
                arrival_time,
                duration,
                destination_gate,
                requires_charging,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            vehicle_id,
            slot_db_id,
            arrival_time,
            duration,
            destination_gate,
            int(requires_charging),
            status
        ))

        booking_id = cursor.lastrowid
        connection.commit()

        if status == "allocated":
            return True, (
                f"Booking {booking_id} created successfully! "
                f"Allocated slot: {slot_number}"
            )

        return True, (
            f"Booking {booking_id} created successfully. "
            "No suitable slot is currently available; "
            "booking added to the waiting list."
        )

    except Exception as error:
        connection.rollback()
        return False, f"Booking allocation failed: {error}"

    finally:
        connection.close()


def reallocate_waiting_bookings():
    """Allocate newly freed slots to eligible waiting bookings."""

    slots = load_slots_from_database()
    requests, allocation = load_active_bookings()

    if not requests:
        return True, "No active bookings found."

    old_allocation = allocation.copy()

    reallocate_waiting_vehicle(
        requests, allocation, slots, set()
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()
        updated_count = 0

        for request, old_slot, new_slot in zip(
            requests, old_allocation, allocation
        ):
            # Only update bookings that were waiting before.
            if old_slot is not None or new_slot is None:
                continue

            cursor.execute("""
                SELECT slot_id FROM parking_slots
                WHERE slot_number = ?
                  AND status = 'available'
            """, (new_slot,))

            slot_row = cursor.fetchone()

            if slot_row is None:
                continue

            cursor.execute("""
                UPDATE bookings
                SET slot_id = ?, status = 'allocated'
                WHERE booking_id = ?
                  AND status = 'pending'
                  AND slot_id IS NULL
            """, (slot_row[0], int(request.request_id)))

            updated_count += cursor.rowcount

        connection.commit()

        return True, (
            f"Waiting-list reallocation completed. "
            f"{updated_count} booking(s) allocated."
        )

    except Exception as error:
        connection.rollback()
        return False, f"Reallocation failed: {error}"

    finally:
        connection.close()


def cancel_booking_and_reallocate(booking_id, user_id):
    """Cancel a booking and attempt waiting-list reallocation."""

    from backend.bookings import cancel_booking

    success, message = cancel_booking(booking_id, user_id)

    if not success:
        return False, message

    reallocation_success, reallocation_message = (
        reallocate_waiting_bookings()
    )

    if not reallocation_success:
        return True, (
            message + " However, " + reallocation_message
        )

    return True, message + " " + reallocation_message



if __name__ == "__main__":
    slots = load_slots_from_database()

    print("AVAILABLE PARKING SLOTS:")
    for slot in slots:
        print(slot)

    requests, allocation = load_active_bookings()

    print("\nACTIVE BOOKINGS:")
    for request, slot_id in zip(requests, allocation):
        print(request, "Allocated slot:", slot_id)

    from hill_climbing import is_compatible

    print("\nCOMPATIBILITY CHECK:")

    for request, slot_id in zip(requests, allocation):
        slot = next(
            (s for s in slots if s.slot_id == slot_id),
            None
        )

        if slot:
            print(
                f"Booking {request.request_id}:",
                is_compatible(request, slot)
            )
        else:
            print(
                f"Booking {request.request_id}:",
                "Assigned slot not available in slot list"
            )
