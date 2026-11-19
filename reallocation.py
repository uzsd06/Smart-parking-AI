
from parking_data import validate_parking_request
from hill_climbing import is_valid_assignment, fitness


def cancel_booking(request_id, requests, allocation, cancelled_ids):

    for i, request in enumerate(requests):

        if request.request_id == request_id:

            if request_id in cancelled_ids:
                print("Booking already cancelled.")
                return False

            cancelled_ids.add(request_id)
            allocation[i] = None

            print(f"Booking {request_id} cancelled.")
            return True

    print("Booking ID not found.")
    return False


def submit_parking_request(
    request, requests, allocation, slots, cancelled_ids
):

    # Validate the parking request
    is_valid, message = validate_parking_request(request)

    if not is_valid:
        print("Request rejected:", message)
        return False

    # Prevent duplicate booking IDs
    existing_ids = [r.request_id for r in requests]

    if request.request_id in existing_ids:
        print("Booking ID already exists.")
        return False

    # Add the new vehicle request
    requests.append(request)
    allocation.append(None)

    new_index = len(requests) - 1

    best_slot = None
    best_score = None

    # Search for a compatible and available slot
    for slot in slots:

        neighbour = allocation.copy()
        neighbour[new_index] = slot.slot_id

        if not is_valid_assignment(requests, slots, neighbour):
            continue

        score = fitness(requests, slots, neighbour)

        if best_score is None or score > best_score:
            best_score = score
            best_slot = slot.slot_id

    # Allocate or add to waiting list
    if best_slot is not None:

        allocation[new_index] = best_slot

        print(
            f"Vehicle {request.request_id} allocated to {best_slot}."
        )

        return True

    print(
        f"Vehicle {request.request_id} added to waiting list."
    )

    return False


def reallocate_waiting_vehicle(
    requests, allocation, slots, cancelled_ids
):

    waiting_indices = [
        i for i, slot_id in enumerate(allocation)
        if slot_id is None
        and requests[i].request_id not in cancelled_ids
    ]

    if not waiting_indices:
        print("No waiting vehicles available for reallocation.")
        return

    current_state = allocation.copy()

    for i in waiting_indices:

        best_slot = None
        best_score = None

        for slot in slots:

            neighbour = current_state.copy()
            neighbour[i] = slot.slot_id

            if not is_valid_assignment(
                requests, slots, neighbour
            ):
                continue

            score = fitness(requests, slots, neighbour)

            if best_score is None or score > best_score:
                best_score = score
                best_slot = slot.slot_id

        if best_slot is not None:
            current_state[i] = best_slot
            print(
                f"Vehicle {requests[i].request_id} "
                f"reallocated to {best_slot}."
            )

    allocation[:] = current_state

    print("Reallocation completed.")
