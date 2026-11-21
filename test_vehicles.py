from backend.vehicles import (
    add_vehicle,
    get_user_vehicles,
    delete_vehicle
)

# User ID 1 is the user registered in our previous test
user_id = 1

# Add a regular vehicle
success, message = add_vehicle(
    user_id, "DL8CAB1234", "regular"
)
print("Regular vehicle:", message)

# Add an EV
success, message = add_vehicle(
    user_id, "DL8CAB5678", "EV"
)
print("Electric vehicle:", message)

# Display vehicles
print("\nUser's vehicles:")

vehicles = get_user_vehicles(user_id)

for vehicle in vehicles:
    print(vehicle)

# Test duplicate registration
success, message = add_vehicle(
    user_id, "DL8CAB1234", "regular"
)
print("\nDuplicate test:", message)
