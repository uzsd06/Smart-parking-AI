
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ParkingSlot:
    slot_id: str
    zone: str
    slot_type: str
    gate_distances: dict


@dataclass
class ParkingRequest:
    request_id: str
    vehicle_type: str
    arrival_time: datetime
    duration_minutes: int
    destination_gate: str
    requires_charging: bool = False


def create_parking_slots():
    slots = []

    for zone in ["A", "B", "C"]:
        distances = {
            "A": {"A": 10, "B": 30, "C": 50},
            "B": {"A": 30, "B": 10, "C": 30},
            "C": {"A": 50, "B": 30, "C": 10}
        }[zone]

        for number in range(1, 11):

            if number <= 2:
                slot_type = "accessible"
            elif number <= 5:
                slot_type = "EV"
            else:
                slot_type = "regular"

            slots.append(
                ParkingSlot(
                    slot_id=f"{zone}{number:02d}",
                    zone=zone,
                    slot_type=slot_type,
                    gate_distances=distances.copy()
                )
            )

    return slots


def create_demo_requests():

    now = datetime.now().replace(second=0, microsecond=0)

    requests = [
        ParkingRequest("V001", "regular", now, 120, "A"),
        ParkingRequest("V002", "EV", now, 90, "B", True),
        ParkingRequest("V003", "regular", now + timedelta(minutes=15), 60, "C"),
        ParkingRequest("V004", "accessible", now + timedelta(minutes=5), 120, "A"),
        ParkingRequest("V005", "EV", now + timedelta(minutes=30), 90, "C", True),
        ParkingRequest("V006", "regular", now + timedelta(minutes=20), 45, "B"),
        ParkingRequest("V007", "regular", now + timedelta(minutes=60), 60, "A"),
        ParkingRequest("V008", "EV", now + timedelta(minutes=10), 120, "B"),
        ParkingRequest(
            "V009", "regular",
            now + timedelta(minutes=130),
            60, "A"
        ),

        ParkingRequest(
            "V010", "regular",
            now + timedelta(minutes=30),
            90, "A"
        ),

        ParkingRequest(
            "V011", "regular",
            now + timedelta(minutes=10),
            60, "A"
        )
    ]
    return requests
def validate_parking_request(request):

    # Check booking ID
    if not isinstance(request.request_id, str) or not request.request_id.strip():
        return False, "Booking ID cannot be empty."

    # Check vehicle type
    if request.vehicle_type not in ("regular", "EV", "accessible"):
        return False, "Invalid vehicle type."

    # Check parking duration
    if type(request.duration_minutes) is not int or request.duration_minutes <= 0:
        return False, "Parking duration must be a positive integer."

    # Check destination gate
    if request.destination_gate not in ("A", "B", "C"):
        return False, "Invalid destination gate."

    # Check arrival time
    if not isinstance(request.arrival_time, datetime):
        return False, "Invalid arrival time."

    # Check charging preference
    if not isinstance(request.requires_charging, bool):
        return False, "Charging preference must be True or False."

    if request.requires_charging and request.vehicle_type != "EV":
        return False, "Only EV vehicles can request charging."

    return True, "Parking request is valid."

