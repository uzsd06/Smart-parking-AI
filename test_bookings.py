from backend.bookings import create_booking

# User 1, Vehicle 1, Parking Slot 2
result1 = create_booking(
    1, 1, 2,
    "2026-11-20T10:00:00",
    2,
    "North Gate"
)

print("First booking:", result1)

# Try booking the same slot during overlapping time
result2 = create_booking(
    1, 1, 2,
    "2026-11-20T11:00:00",
    2,
    "North Gate"
)

print("Overlapping booking:", result2)

# Try booking after the first booking ends
result3 = create_booking(
    1, 1, 2,
    "2026-11-20T12:00:00",
    2,
    "North Gate"
)

print("Consecutive booking:", result3)
