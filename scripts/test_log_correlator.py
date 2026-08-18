import os
import sys
import django

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from monitor.models import AccessConcentrator
from librouteros import connect


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

AC_NAME = "calu-ac2"


# ---------------------------------------------------------
# CONNECT TO AC
# ---------------------------------------------------------

ac = AccessConcentrator.objects.get(
    name=AC_NAME
)

print("=" * 60)
print(f"AC: {ac.name}")
print(f"IP: {ac.ip_address}")
print("=" * 60)

print("Connecting...")

api = connect(
    username=ac.username,
    password=ac.password,
    host=ac.ip_address,
    port=8728,
)

print("CONNECTED!\n")


# ---------------------------------------------------------
# GET ACTIVE PPPoE USERS
# ---------------------------------------------------------

active_users = list(
    api("/ppp/active/print")
)

print(
    f"Active PPPoE users: "
    f"{len(active_users)}"
)


# ---------------------------------------------------------
# BUILD MAC LOOKUP
# ---------------------------------------------------------

users_by_mac = {}

for user in active_users:

    mac = user.get("caller-id")

    if not mac:
        continue

    mac = mac.upper()

    users_by_mac[mac] = {
        "username": user.get("name"),
        "ip_address": user.get("address"),
        "session_id": user.get("session-id"),
    }


print(
    f"MAC lookup entries: "
    f"{len(users_by_mac)}"
)


# ---------------------------------------------------------
# GET MIKROTIK LOGS
# ---------------------------------------------------------

logs = list(
    api("/log/print")
)

print(
    f"MikroTik log entries: "
    f"{len(logs)}"
)

print()


# ---------------------------------------------------------
# PROCESS PPPoE LOGS
# ---------------------------------------------------------

print("=" * 60)
print("PPPoE LOG CORRELATION")
print("=" * 60)


for log in logs:

    topics = log.get("topics", "")
    message = log.get("message", "")
    timestamp = log.get("time")

    # Ignore everything that isn't PPPoE-related
    if "pppoe" not in topics.lower():
        continue

    matched_user = None
    matched_mac = None

    # -----------------------------------------------------
    # Try to match a MAC address from the log
    # -----------------------------------------------------

    message_upper = message.upper()

    for mac, user in users_by_mac.items():

        if mac in message_upper:

            matched_user = user
            matched_mac = mac
            break


    # -----------------------------------------------------
    # Determine event type
    # -----------------------------------------------------

    if "authentication failed" in message.lower():

        event_type = "AUTH_FAILURE"

    elif "connection established" in message.lower():

        event_type = "CONNECTION"

    elif "logged out" in message.lower():

        event_type = "LOGOUT"

    elif "logged in" in message.lower():

        event_type = "LOGIN"

    else:

        event_type = "OTHER"


    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print()

    print(f"TIME:    {timestamp}")
    print(f"TOPICS:  {topics}")
    print(f"MESSAGE: {message}")
    print(f"EVENT:   {event_type}")

    if matched_user:

        print("MATCH:   YES")

        print(
            f"USER:    "
            f"{matched_user['username']}"
        )

        print(
            f"IP:      "
            f"{matched_user['ip_address']}"
        )

        print(
            f"MAC:     "
            f"{matched_mac}"
        )

        print(
            f"SESSION: "
            f"{matched_user['session_id']}"
        )

    else:

        print("MATCH:   NO")