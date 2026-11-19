from backend.parking_slots import (
    add_slot,
    get_all_slots,
    update_slot_status
)

# Add parking slots
print(add_slot("A01", "regular", "North Gate"))
print(add_slot("A02", "EV", "North Gate"))
print(add_slot("A03", "accessible", "South Gate"))

# Display all slots
print("\nAll Parking Slots:")

slots = get_all_slots()

for slot in slots:
    print(slot)

# Block a parking slot
print("\nUpdating slot status:")

print(update_slot_status(1, "blocked"))

# Display updated slots
print("\nUpdated Parking Slots:")

for slot in get_all_slots():
    print(slot)
