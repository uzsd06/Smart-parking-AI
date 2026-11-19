from database.db import get_connection


def add_vehicle(user_id, registration_number, vehicle_type):
    """Register a vehicle for an existing user."""

    registration_number = registration_number.strip().upper()

    allowed_types = ["regular", "EV", "accessible"]

    if vehicle_type not in allowed_types:
        return False, "Invalid vehicle type."

    if not registration_number:
        return False, "Registration number is required."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO vehicles (user_id, registration_number, vehicle_type)
            VALUES (?, ?, ?)
        """, (user_id, registration_number, vehicle_type))

        connection.commit()

        return True, "Vehicle registered successfully!"

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "Vehicle is already registered."

        return False, f"Vehicle registration failed: {error}"

    finally:
        connection.close()


def get_user_vehicles(user_id):
    """Retrieve all vehicles belonging to a user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT vehicle_id, registration_number, vehicle_type
            FROM vehicles
            WHERE user_id = ?
        """, (user_id,))

        return cursor.fetchall()

    finally:
        connection.close()


def delete_vehicle(vehicle_id, user_id):
    """Delete a vehicle belonging to the specified user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM vehicles
            WHERE vehicle_id = ? AND user_id = ?
        """, (vehicle_id, user_id))

        connection.commit()

        if cursor.rowcount == 0:
            return False, "Vehicle not found."

        return True, "Vehicle deleted successfully!"

    except Exception as error:
        return False, f"Vehicle deletion failed: {error}"

    finally:
        connection.close()
