
from datetime import timedelta


def is_compatible(request, slot):

    if request.vehicle_type == "accessible":
        return slot.slot_type == "accessible"

    if request.vehicle_type == "EV":
        if request.requires_charging:
            return slot.slot_type == "EV"

        return slot.slot_type in ("EV", "regular")

    if request.vehicle_type == "regular":
        return slot.slot_type in ("regular", "EV")

    return False


def has_time_conflict(request, other_request):

    request_start = request.arrival_time
    request_end = request_start + timedelta(
        minutes=request.duration_minutes
    )

    other_start = other_request.arrival_time
    other_end = other_start + timedelta(
        minutes=other_request.duration_minutes
    )

    return (
        request_start < other_end
        and other_start < request_end
    )


def has_overlapping_charging_request(request, requests):

    for other_request in requests:

        if other_request is request:
            continue

        if (
            other_request.vehicle_type == "EV"
            and other_request.requires_charging
            and has_time_conflict(request, other_request)
        ):
            return True

    return False





def is_valid_assignment(
    requests, slots, state, locked_indices=None
):
    if len(requests) != len(state):
        return False

    locked_indices = locked_indices or set()
    slot_lookup = {slot.slot_id: slot for slot in slots}

    # Identify slots occupied by checked-in bookings.
    locked_slot_ids = {
        state[i]
        for i in locked_indices
        if i < len(state) and state[i] is not None
    }

    assigned = {}

    for i, slot_id in enumerate(state):

        if slot_id is None:
            if i in locked_indices:
                return False
            continue

        slot = slot_lookup.get(slot_id)

        if slot is None:
            return False

        # Never assign a checked-in booking's slot to another request.
        if slot_id in locked_slot_ids and i not in locked_indices:
            return False

        request = requests[i]

        if not is_compatible(request, slot):
            return False

        if slot_id not in assigned:
            assigned[slot_id] = []

        for previous_index in assigned[slot_id]:
            if has_time_conflict(
                request, requests[previous_index]
            ):
                return False

        assigned[slot_id].append(i)

    return True





def fitness(requests, slots, state):

    score = 0
    slot_lookup = {slot.slot_id: slot for slot in slots}

    for i, slot_id in enumerate(state):

        if slot_id is None:
            continue

        request = requests[i]
        slot = slot_lookup[slot_id]

        score += 1000

        if request.requires_charging:
            score += 500

        distance = slot.gate_distances.get(
            request.destination_gate, 30
        )
        score -= distance * 10

        if request.vehicle_type == "accessible":
            score += 40
        elif request.vehicle_type == "EV" and slot.slot_type == "EV":
            score += 40
        elif request.vehicle_type == "regular" and slot.slot_type == "regular":
            score += 20

        # Prioritise a waiting charging EV.
        if (
            request.vehicle_type != "accessible"
            and not request.requires_charging
            and slot.slot_type == "EV"
        ):

            for j, waiting_request in enumerate(requests):

                if (
                    state[j] is None
                    and waiting_request.requires_charging
                    and has_time_conflict(request, waiting_request)
                    and is_compatible(waiting_request, slot)
                ):

                    # Check whether the current vehicle can move elsewhere.
                    alternative_available = False

                    for alternative_slot in slots:

                        if alternative_slot.slot_id == slot_id:
                            continue

                        if not is_compatible(request, alternative_slot):
                            continue

                        occupied = False

                        for k, assigned_slot in enumerate(state):

                            if k == i or assigned_slot != alternative_slot.slot_id:
                                continue

                            if has_time_conflict(request, requests[k]):
                                occupied = True
                                break

                        if not occupied:
                            alternative_available = True
                            break

                    if alternative_available:
                        score -= 600
                        break

    return score


def hill_climbing(
    requests,
    slots,
    initial_state=None,
    locked_indices=None
):

    locked_indices = locked_indices or set()

    # Start from existing allocations when provided.
    if initial_state is None:
        current_state = [None] * len(requests)
    else:
        current_state = initial_state.copy()

    if len(current_state) != len(requests):
        raise ValueError(
            "Initial allocation must match the number of requests."
        )

    if not is_valid_assignment(
        requests, slots, current_state, locked_indices
    ):
        raise ValueError(
            "Initial allocation contains invalid assignments."
        )

    current_score = fitness(
        requests, slots, current_state
    )

    iterations = 0

    while True:

        best_state = current_state.copy()
        best_score = current_score

        # Explore neighbouring allocation states.
        for i in range(len(requests)):

            # Never move a checked-in booking.
            if i in locked_indices:
                continue

            # Try every available slot.
            for slot in slots:

                neighbour = current_state.copy()
                neighbour[i] = slot.slot_id

                if not is_valid_assignment(
                    requests,
                    slots,
                    neighbour,
                    locked_indices
                ):
                    continue

                neighbour_score = fitness(
                    requests, slots, neighbour
                )

                if neighbour_score > best_score:
                    best_score = neighbour_score
                    best_state = neighbour

            # Also explore leaving this vehicle unallocated.
            neighbour = current_state.copy()
            neighbour[i] = None

            if is_valid_assignment(
                requests,
                slots,
                neighbour,
                locked_indices
            ):

                neighbour_score = fitness(
                    requests, slots, neighbour
                )

                if neighbour_score > best_score:
                    best_score = neighbour_score
                    best_state = neighbour

        # Stop when no better neighbour exists.
        if best_score <= current_score:
            break

        current_state = best_state
        current_score = best_score
        iterations += 1

    return current_state, current_score, iterations
