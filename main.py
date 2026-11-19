
from reallocation import (
    cancel_booking,
    reallocate_waiting_vehicle,
    submit_parking_request
)
from datetime import timedelta
from parking_data import ParkingRequest
from availability import get_parking_status
from parking_data import (
    create_parking_slots,
    create_demo_requests,
)
from hill_climbing import hill_climbing


def main():

    print("\n========== SMARTPARK AI ==========")
    print("Intelligent Parking Allocation System")
    print("==================================\n")

    slots = create_parking_slots()
    requests = create_demo_requests()

    print("Total Parking Slots:", len(slots))
    print("Total Vehicle Requests:", len(requests))

    print("\nOptimising parking allocation...\n")

    allocation, score, iterations = hill_climbing(
        requests, slots
    )

    cancelled_ids = set()

    print("========== ALLOCATION RESULTS ==========")

    for request, slot_id in zip(requests, allocation):

        if slot_id is not None:
            print(
                f"{request.request_id} | "
                f"{request.vehicle_type} | "
                f"Gate {request.destination_gate} | "
                f"Parking Slot: {slot_id}"
            )

        else:
            print(
                f"{request.request_id} | "
                f"Parking Slot: NOT AVAILABLE"
            )

    allocated = sum(
        1 for slot in allocation if slot is not None
    )

    print("\n========== PERFORMANCE ==========")
    print("Successfully Allocated:", allocated)
    print("Unallocated Vehicles:", len(requests) - allocated)
    print("Optimisation Score:", score)
    print("Hill Climbing Iterations:", iterations)

    print("\nSmartPark AI execution completed!")

    print("\n========== PARKING AVAILABILITY ==========")

    first_arrival = requests[0].arrival_time

    for minutes in [60, 150]:

        check_time = first_arrival + timedelta(
            minutes=minutes
        )

        available, occupied = get_parking_status(
            slots, requests, allocation, check_time
        )

        print(f"\nAfter {minutes} minutes:")
        print("Occupied Spaces:", len(occupied))
        print("Available Spaces:", len(available))
        print("Occupied Slot IDs:", occupied)

    print("\n========== CANCELLATION TEST ==========")

    cancel_booking(
        "V001",
        requests,
        allocation,
        cancelled_ids
    )

    print("\n========== AUTOMATIC REALLOCATION ==========")

    reallocate_waiting_vehicle(
        requests,
        allocation,
        slots,
        cancelled_ids
    )

    print("\n========== UPDATED ALLOCATION ==========")

    for request, slot_id in zip(requests, allocation):

        if request.request_id in cancelled_ids:
            status = "CANCELLED"
        elif slot_id is None:
            status = "WAITING"
        else:
            status = slot_id

        print(request.request_id, "| Parking Slot:", status)

    print("\n========== AVAILABILITY AFTER REALLOCATION ==========")

    check_time = requests[0].arrival_time + timedelta(minutes=20)

    available, occupied = get_parking_status(
        slots, requests, allocation, check_time
    )

    print("Checking availability after 20 minutes...")
    print("Occupied Spaces:", len(occupied))
    print("Available Spaces:", len(available))
    print("Is A06 occupied?", "A06" in occupied)

    print("\n========== WAITING LIST & REALLOCATION TEST ==========")

    # Create a separate test with only one parking slot
    test_slots = [
        next(slot for slot in slots if slot.slot_id == "A06")
    ]

    test_requests = [
        ParkingRequest(
            "T001",
            "regular",
            requests[0].arrival_time,
            120,
            "A"
        )
    ]

    test_allocation = ["A06"]
    test_cancelled_ids = set()

    # Submit a second vehicle
    second_vehicle = ParkingRequest(
        "T002",
        "regular",
        requests[0].arrival_time + timedelta(minutes=10),
        60,
        "A"
    )

    print("\n...Submitting second vehicle...")

    submit_parking_request(
        second_vehicle,
        test_requests,
        test_allocation,
        test_slots,
        test_cancelled_ids
    )

    # Cancel the first vehicle's booking
    print("\nCancelling first vehicle...")

    cancel_booking(
        "T001",
        test_requests,
        test_allocation,
        test_cancelled_ids
    )

    # Reallocate the freed parking slot
    print("\nReallocating waiting vehicles...")

    reallocate_waiting_vehicle(
        test_requests,
        test_allocation,
        test_slots,
        test_cancelled_ids
    )

    # Display final results
    print("\nFinal Test Results:")

    for request, slot_id in zip(test_requests, test_allocation):

        if request.request_id in test_cancelled_ids:
            status = "CANCELLED"
        elif slot_id is None:
            status = "WAITING"
        else:
            status = slot_id

        print(request.request_id, "| Parking Slot:", status)

    print("\n========== NEW PARKING REQUEST ==========")

    waiting_vehicle = ParkingRequest(
        "V012",
        "regular",
        requests[0].arrival_time + timedelta(minutes=10),
        60,
        "A"
    )

    submit_parking_request(
        waiting_vehicle,
        requests,
        allocation,
        slots,
        cancelled_ids
    )

    # Input validation test
    print("\n========== INPUT VALIDATION TEST ==========")

    invalid_request = ParkingRequest(
        "V013",
        "bike",
        requests[0].arrival_time,
        60,
        "A"
    )

    submit_parking_request(
        invalid_request,
        requests,
        allocation,
        slots,
        cancelled_ids
    )


if __name__ == "__main__":
    main()
