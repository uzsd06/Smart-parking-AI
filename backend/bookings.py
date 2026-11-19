from datetime import datetime, timedelta
from database.db import get_connection


def create_booking(user_id, vehicle_id, slot_id,
                  arrival_time, duration, destination_gate):
    """Create a parking booking after checking availability."""

    try:
        arrival = datetime.fromisoformat(arrival_time)

        if duration <= 0:
            return False, "Duration must be greater than zero."

        end_time = arrival + timedelta(hours=duration)

    except (ValueError, TypeError):
        return False, "Invalid arrival time or duration."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Check whether the slot exists and is usable
        cursor.execute("""
            SELECT status FROM parking_slots
            WHERE slot_id = ?
        """, (slot_id,))

        slot = cursor.fetchone()

        if slot is None:
            return False, "Parking slot does not exist."

        if slot[0] != "available":
            return False, "Parking slot is blocked or under maintenance."

        # Check whether the vehicle belongs to the user
        cursor.execute("""
            SELECT vehicle_id FROM vehicles
            WHERE vehicle_id = ? AND user_id = ?
        """, (vehicle_id, user_id))

        if cursor.fetchone() is None:
            return False, "Vehicle does not belong to this user."

        # Check overlapping active bookings
        cursor.execute("""
            SELECT arrival_time, duration
            FROM bookings
            WHERE slot_id = ?
            AND status IN ('pending', 'allocated', 'checked-in')
        """, (slot_id,))

        existing_bookings = cursor.fetchall()

        for existing_arrival, existing_duration in existing_bookings:
            old_start = datetime.fromisoformat(existing_arrival)
            old_end = old_start + timedelta(hours=existing_duration)

            if arrival < old_end and old_start < end_time:
                return False, "Parking slot is already booked during this time."

        # Create booking
        cursor.execute("""
            INSERT INTO bookings (
                user_id, vehicle_id, slot_id,
                arrival_time, duration, destination_gate, status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (
            user_id, vehicle_id, slot_id,
            arrival_time, duration, destination_gate
        ))

        connection.commit()

        return True, f"Booking created! Booking ID: {cursor.lastrowid}"

    except Exception as error:
        return False, f"Booking failed: {error}"

    finally:
        connection.close()


def get_user_bookings(user_id):
    """Fetch all bookings belonging to a user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                booking_id,
                vehicle_id,
                slot_id,
                arrival_time,
                duration,
                destination_gate,
                status
            FROM bookings
            WHERE user_id = ?
            ORDER BY booking_id DESC
        """, (user_id,))

        return cursor.fetchall()

    finally:
        connection.close()


def cancel_booking(booking_id, user_id):
    """Cancel a booking belonging to a user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT status FROM bookings
            WHERE booking_id = ? AND user_id = ?
        """, (booking_id, user_id))

        booking = cursor.fetchone()

        if booking is None:
            return False, "Booking not found."

        if booking[0] in ("cancelled", "completed"):
            return False, "This booking cannot be cancelled."

        cursor.execute("""
            UPDATE bookings
            SET status = 'cancelled'
            WHERE booking_id = ? AND user_id = ?
        """, (booking_id, user_id))

        connection.commit()

        return True, "Booking cancelled successfully!"

    finally:
        connection.close()


def update_booking_status(booking_id, new_status):
    """Update the status of a booking."""

    allowed_statuses = [
        "pending",
        "allocated",
        "checked-in",
        "completed",
        "cancelled"
    ]

    if new_status not in allowed_statuses:
        return False, "Invalid booking status."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT status FROM bookings
            WHERE booking_id = ?
        """, (booking_id,))

        booking = cursor.fetchone()

        if booking is None:
            return False, "Booking not found."

        current_status = booking[0]

        valid_transitions = {
            "pending": ["allocated", "cancelled"],
            "allocated": ["checked-in", "cancelled"],
            "checked-in": ["completed"],
            "completed": [],
            "cancelled": []
        }

        if new_status not in valid_transitions[current_status]:
            return False, "Invalid booking status transition."

        cursor.execute("""
            UPDATE bookings
            SET status = ?
            WHERE booking_id = ?
        """, (new_status, booking_id))

        connection.commit()

        return True, "Booking status updated successfully!"

    finally:
        connection.close()

