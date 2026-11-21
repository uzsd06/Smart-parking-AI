
from parking_data import validate_parking_request
from hill_climbing import hill_climbing


def cancel_booking(
    request_id, requests, allocation, cancelled_ids
):

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
    request,
    requests,
    allocation,
    slots,
    cancelled_ids,
    locked_indices=None
):

    is_valid, message = validate_parking_request(request)

    if not is_valid:
        print("Request rejected:", message)
        return False

    existing_ids = [r.request_id for r in requests]

    if request.request_id in existing_ids:
        print("Booking ID already exists.")
        return False

    if len(requests) != len(allocation):
        print("Request and allocation data do not match.")
        return False

    requests.append(request)
    allocation.append(None)

    locked_indices = locked_indices or set()

    try:
        best_state, best_score, iterations = hill_climbing(
            requests,
            slots,
            initial_state=allocation.copy(),
            locked_indices=locked_indices
        )

    except ValueError as error:
        requests.pop()
        allocation.pop()
        print("Allocation failed:", error)
        return False

    allocation[:] = best_state

    new_index = len(requests) - 1

    if allocation[new_index] is not None:

        print(
            f"Vehicle {request.request_id} allocated to "
            f"{allocation[new_index]}."
        )

        print(
            f"Optimisation score: {best_score}, "
            f"iterations: {iterations}"
        )

        return True

    print(
        f"Vehicle {request.request_id} added to waiting list."
    )

    return False


def reallocate_waiting_vehicle(
    requests,
    allocation,
    slots,
    cancelled_ids,
    locked_indices=None
):

    if len(requests) != len(allocation):
        print("Request and allocation data do not match.")
        return False

    locked_indices = locked_indices or set()

    # Keep cancelled bookings unallocated.
    initial_state = allocation.copy()

    for i, request in enumerate(requests):

        if request.request_id in cancelled_ids:
            initial_state[i] = None

    try:
        best_state, best_score, iterations = hill_climbing(
            requests,
            slots,
            initial_state=initial_state,
            locked_indices=locked_indices
        )

    except ValueError as error:
        print("Reallocation failed:", error)
        return False

    # Update the in-memory allocation.
    allocation[:] = best_state

    print("Reallocation completed.")
    print("Optimisation score:", best_score)
    print("Iterations:", iterations)

    for request, slot_id in zip(requests, allocation):

        if slot_id is not None:
            print(
                f"Vehicle {request.request_id} -> {slot_id}"
            )
        else:
            print(
                f"Vehicle {request.request_id} -> Waiting list"
            )

    return True
