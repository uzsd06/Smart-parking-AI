
def get_parking_status(slots, requests, allocation, check_time):

    occupied_slots = set()

    for request, slot_id in zip(requests, allocation):

        if slot_id is None:
            continue

        start_time = request.arrival_time

        from datetime import timedelta
        end_time = start_time + timedelta(
            minutes=request.duration_minutes
        )

        if start_time <= check_time < end_time:
            occupied_slots.add(slot_id)

    available_slots = [
        slot.slot_id
        for slot in slots
        if slot.slot_id not in occupied_slots
    ]

    return available_slots, list(occupied_slots)
