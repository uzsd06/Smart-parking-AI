from backend.users import register_user, login_user

# Register a new user
success, message = register_user(
    "Vidhi",
    "vidhi@example.com",
    "SmartPark123",
    "9876543210"
)

print("Registration:", message)

# Test correct login
user = login_user("vidhi@example.com", "SmartPark123")

if user:
    print("Login successful!")
    print("Welcome,", user["name"])
else:
    print("Login failed!")

# Test incorrect password
wrong_user = login_user("vidhi@example.com", "WrongPassword")

print("Wrong password rejected:", wrong_user is None)

# Test duplicate registration
success, message = register_user(
    "Vidhi",
    "vidhi@example.com",
    "AnotherPassword123"
)

print("Duplicate registration:", message)
