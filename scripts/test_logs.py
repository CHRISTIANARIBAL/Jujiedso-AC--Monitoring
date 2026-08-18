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


ac = AccessConcentrator.objects.get(
    name="calu-ac2"
)

print(
    f"Connecting to {ac.name} "
    f"({ac.ip_address})..."
)

api = connect(
    username=ac.username,
    password=ac.password,
    host=ac.ip_address,
    port=8728,
)

print("CONNECTED!")

logs = list(
    api("/log/print")
)

print(
    f"\nTotal log entries returned: "
    f"{len(logs)}"
)

print("\nLast 30 log entries:\n")

for log in logs[-30:]:

    print(
        f"{log.get('time')} | "
        f"{log.get('topics')} | "
        f"{log.get('message')}"
    )