from database.db import get_connection
from backend.auth import hash_password, verify_password


def register_user(name, email, password, phone=None):
    """Register a new SmartPark AI user."""

    name = name.strip()
    email = email.strip().lower()

    if not name or not email or not password:
        return False, "All required fields must be filled."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    connection = get_connection()

    try:
        hashed_password = hash_password(password)

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (name, email, password_hash, phone)
            VALUES (?, ?, ?, ?)
        """, (name, email, hashed_password, phone))

        connection.commit()

        return True, "Registration successful!"

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "Email is already registered."

        return False, f"Registration failed: {error}"

    finally:
        connection.close()


def login_user(email, password):
    """Authenticate an existing user."""

    email = email.strip().lower()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT user_id, name, email, password_hash
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        if user is None:
            return None

        user_id, name, email, stored_hash = user

        if verify_password(password, stored_hash):

            return {
                "user_id": user_id,
                "name": name,
                "email": email
            }

        return None

    finally:
        connection.close()
