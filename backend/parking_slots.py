from database.db import get_connection


def add_slot(slot_number, slot_type, gate):
    """Add a new parking slot."""

    allowed_types = ["regular", "EV", "accessible"]

    if slot_type not in allowed_types:
        return False, "Invalid parking slot type."

    if not slot_number.strip() or not gate.strip():
        return False, "Slot number and gate are required."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO parking_slots (slot_number, slot_type, gate)
            VALUES (?, ?, ?)
        """, (slot_number.strip().upper(), slot_type, gate.strip()))

        connection.commit()

        return True, "Parking slot added successfully!"

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "Slot number already exists."

        return False, f"Error: {error}"

    finally:
        connection.close()


def get_all_slots():
    """Retrieve all parking slots."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT slot_id, slot_number, slot_type, gate, status
            FROM parking_slots
            ORDER BY slot_id
        """)

        return cursor.fetchall()

    finally:
        connection.close()


def update_slot_status(slot_id, new_status):
    """Update parking slot availability status."""

    allowed_statuses = ["available", "blocked", "maintenance"]

    if new_status not in allowed_statuses:
        return False, "Invalid slot status."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE parking_slots
            SET status = ?
            WHERE slot_id = ?
        """, (new_status, slot_id))

        connection.commit()

        if cursor.rowcount == 0:
            return False, "Parking slot not found."

        return True, "Parking slot status updated successfully!"

    finally:
        connection.close()
