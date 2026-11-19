from backend.auth import hash_password, verify_password

password = "SmartPark123"

# Generate password hash
hashed = hash_password(password)

print("Password hashed successfully!")

# Verify correct password
print("Correct password:", verify_password(password, hashed))

# Verify incorrect password
print("Wrong password:", verify_password("wrong123", hashed))