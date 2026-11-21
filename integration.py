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
            WHERE status = 'available'
               OR slot_id IN (
                    SELECT DISTINCT slot_id
                    FROM bookings
                    WHERE status = 'checked-in'
                      AND slot_id IS NOT NULL
               )
        """)

        rows = cursor.fetchall()

        slots = []

        for slot_id, slot_number, slot_type, gate, status in rows:

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
              AND (
                  b.status = 'checked-in'
                  OR datetime(
                      b.arrival_time,
                      '+' || b.duration || ' hours'
                  ) > datetime('now', 'localtime')
              )
            ORDER BY b.arrival_time
        """)

        rows = cursor.fetchall()

        requests = []
        allocation = []
        statuses = []

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
            statuses.append(status)

        return requests, allocation, statuses

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
    """Create a booking using Hill Climbing optimisation."""

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

        # Verify user
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )

        if cursor.fetchone() is None:
            return False, "User not found."

        # Verify vehicle ownership
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

        # Load slots and active bookings
        slots = load_slots_from_database()

        requests, allocation, statuses = load_active_bookings()

        # Lock checked-in bookings
        locked_indices = {
            i for i, status in enumerate(statuses)
            if status == "checked-in"
        }

        previous_count = len(requests)

        # Create new request
        request_id = "NEW-" + str(uuid4())

        new_request = ParkingRequest(
            request_id=request_id,
            vehicle_type=vehicle_type,
            arrival_time=arrival,
            duration_minutes=duration * 60,
            destination_gate=destination_gate,
            requires_charging=requires_charging
        )

        # Run Hill Climbing through the reallocation module
        allocated = submit_parking_request(
            new_request,
            requests,
            allocation,
            slots,
            set(),
            locked_indices
        )

        # Confirm the request was actually added
        if len(requests) != previous_count + 1:
            return False, "Parking request could not be processed."

        # Resolve all allocated slot numbers to database IDs
        slot_id_lookup = {}

        for slot in slots:

            cursor.execute("""
                SELECT slot_id
                FROM parking_slots
                WHERE slot_number = ?
                  AND status = 'available'
            """, (slot.slot_id,))

            row = cursor.fetchone()

            if row is not None:
                slot_id_lookup[slot.slot_id] = row[0]

        # Save changes to existing bookings.
        for i in range(previous_count):

            if i in locked_indices:
                continue

            new_slot = allocation[i]

            if new_slot is None:
                new_db_slot_id = None
                new_status = "pending"

            else:
                new_db_slot_id = slot_id_lookup.get(new_slot)

                if new_db_slot_id is None:
                    raise ValueError(
                        f"Parking slot {new_slot} is unavailable."
                    )

                new_status = "allocated"

            cursor.execute("""
                UPDATE bookings
                SET slot_id = ?, status = ?
                WHERE booking_id = ?
                  AND status IN ('pending', 'allocated')
            """, (
                new_db_slot_id,
                new_status,
                int(requests[i].request_id)
            ))

        # Determine the new booking's allocation
        new_slot = allocation[-1]

        if new_slot is not None:
            slot_db_id = slot_id_lookup.get(new_slot)

            if slot_db_id is None:
                raise ValueError(
                    "Selected parking slot is no longer available."
                )

            status = "allocated"

        else:
            slot_db_id = None
            status = "pending"

        # Insert the new booking
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

        if allocated:
            return True, (
                f"Booking {booking_id} created successfully! "
                f"Allocated slot: {new_slot}. "
                "Existing allocations optimised successfully."
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
    """Optimise allocations and update all affected bookings."""

    slots = load_slots_from_database()

    requests, allocation, statuses = load_active_bookings()

    if not requests:
        return True, "No active bookings found."

    old_allocation = allocation.copy()

    # Never move bookings that have already checked in.
    locked_indices = {
        i for i, status in enumerate(statuses)
        if status == "checked-in"
    }

    # Run Hill Climbing optimisation.
    success = reallocate_waiting_vehicle(
        requests,
        allocation,
        slots,
        set(),
        locked_indices
    )

    if not success:
        return False, "Hill Climbing reallocation failed."

    slot_id_lookup = {}

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Get database IDs for available slots.
        for slot in slots:

            cursor.execute("""
               SELECT slot_id
               FROM parking_slots
               WHERE slot_number = ?
            """, (slot.slot_id,))

            row = cursor.fetchone()

            if row is not None:
                slot_id_lookup[slot.slot_id] = row[0]

        updated_count = 0

        # Save every changed booking.
        for i, request in enumerate(requests):

            if i in locked_indices:
                continue

            old_slot = old_allocation[i]
            new_slot = allocation[i]

            if old_slot == new_slot:
                continue

            if new_slot is None:
                new_db_slot_id = None
                new_status = "pending"

            else:
                new_db_slot_id = slot_id_lookup.get(new_slot)

                if new_db_slot_id is None:
                    raise ValueError(
                        f"Parking slot {new_slot} is unavailable."
                    )

                new_status = "allocated"

            cursor.execute("""
                UPDATE bookings
                SET slot_id = ?, status = ?
                WHERE booking_id = ?
                  AND status IN ('pending', 'allocated')
            """, (
                new_db_slot_id,
                new_status,
                int(request.request_id)
            ))

            updated_count += cursor.rowcount

        connection.commit()

        return True, (
            "Hill Climbing reallocation completed. "
            f"{updated_count} booking(s) updated."
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

    requests, allocation, statuses = load_active_bookings()

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
