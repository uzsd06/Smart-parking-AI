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

    return request_start < other_end and other_start < request_end

def is_valid_assignment(requests, slots, state):

    assigned = {}

    for i, slot_id in enumerate(state):

        if slot_id is None:
            continue

        slot = next(
            (s for s in slots if s.slot_id == slot_id),
            None
        )

        if slot is None:
            return False

        if not is_compatible(requests[i], slot):
            return False

        if slot_id not in assigned:
            assigned[slot_id] = []

        for previous_index in assigned[slot_id]:

            if has_time_conflict(
                requests[i], requests[previous_index]
            ):
                return False

        assigned[slot_id].append(i)

    return True

def fitness(requests, slots, state):

    score = 0

    for i, slot_id in enumerate(state):

        if slot_id is None:
            continue

        request = requests[i]

        slot = next(
            s for s in slots if s.slot_id == slot_id
        )

        # Every successfully allocated vehicle
        # receives a major score.
        score += 1000

        # Prefer parking spaces near the destination gate.
        distance = slot.gate_distances[
            request.destination_gate
        ]

        score -= distance * 10

        # Reward suitable parking-space preferences.
        if request.vehicle_type == "EV" and slot.slot_type == "EV":
            score += 40

        elif request.vehicle_type == "regular" and slot.slot_type == "regular":
            score += 20

        elif request.vehicle_type == "accessible":
            score += 40

    return score

def hill_climbing(requests, slots):

    # Initially, no vehicle has a parking slot.
    current_state = [None] * len(requests)

    current_score = fitness(
        requests, slots, current_state
    )

    iterations = 0

    while True:

        best_state = current_state.copy()
        best_score = current_score

        # Explore neighbouring solutions.
        for i in range(len(requests)):

            for slot in slots:

                neighbour = current_state.copy()
                neighbour[i] = slot.slot_id

                if not is_valid_assignment(
                    requests, slots, neighbour
                ):
                    continue

                neighbour_score = fitness(
                    requests, slots, neighbour
                )

                if neighbour_score > best_score:

                    best_score = neighbour_score
                    best_state = neighbour

        # No better neighbouring solution exists.
        if best_score <= current_score:
            break

        current_state = best_state
        current_score = best_score

        iterations += 1

    return current_state, current_score, iterations