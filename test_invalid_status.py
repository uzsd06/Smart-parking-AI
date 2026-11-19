
from backend.bookings import (
    update_booking_status,
    cancel_booking
)

# Booking 1 is currently allocated
print("Allocated to completed:")
print(update_booking_status(1, "completed"))

# Booking 2 is currently cancelled
print("\nCancelled to allocated:")
print(update_booking_status(2, "allocated"))

# Try cancelling an already cancelled booking
print("\nCancel again:")
print(cancel_booking(2, 1))

