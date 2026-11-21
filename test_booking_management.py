
from backend.bookings import (
    get_user_bookings,
    cancel_booking,
    update_booking_status
)

# 1. Display all bookings of user 1
print("\n--- USER BOOKINGS ---")
bookings = get_user_bookings(1)

for booking in bookings:
    print(booking)

# 2. Update booking 3 from pending to allocated
print("\n--- UPDATE STATUS ---")
print(update_booking_status(1, "allocated"))

# 3. Cancel booking 4
print("\n--- CANCEL BOOKING ---")
print(cancel_booking(2, 1))

# 4. Display bookings again
print("\n--- UPDATED BOOKINGS ---")
for booking in get_user_bookings(1):
    print(booking)
