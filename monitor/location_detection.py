
import re
from collections import defaultdict

from .models import PPPoEClient, PPPoESession


USERNAME_PATTERN = re.compile(r"^([a-zA-Z-]+)(\d{2})(.+)$")


def detect_location(username):
    username = (username or "").strip().lower()
    match = USERNAME_PATTERN.fullmatch(username)

    if not match:
        return None, None

    location, nap, customer = match.groups()

    if not customer:
        return None, None

    return location, nap


def get_location_summary():
    clients = list(
        PPPoEClient.objects
        .select_related("ac")
        .order_by("username", "-last_seen", "-id")
    )

    active_usernames = {
        username.strip().lower()
        for username in PPPoESession.objects.filter(
            active=True
        ).values_list("username", flat=True)
        if username
    }

    # One summary entry per unique PPPoE username.
    unique_clients = {}

    for client in clients:
        username = (client.username or "").strip().lower()
        if not username:
            continue

        location, nap = detect_location(username)
        if not location:
            location = "no location"
            nap = None

        # Keep the newest client record for the details modal.
        if username not in unique_clients:
            unique_clients[username] = {
                "client": client,
                "location": location,
                "nap": nap,
            }

    locations = defaultdict(
        lambda: {
            "total": 0,
            "online": 0,
            "down": 0,
            "clients": [],
        }
    )

    for username, entry in unique_clients.items():
        client = entry["client"]
        location = entry["location"]
        nap = entry["nap"]
        is_online = username in active_usernames

        item = locations[location]
        item["total"] += 1

        if is_online:
            item["online"] += 1
        else:
            item["down"] += 1

        item["clients"].append({
            "id": client.id,
            "username": client.username,
            "mac": client.mac_address,
            "ac": client.ac.name if client.ac else "Unknown AC",
            "nap": nap,
            "status": "Online" if is_online else "Down",
        })

    return [
        {"name": name, **data}
        for name, data in sorted(locations.items())
    ]
