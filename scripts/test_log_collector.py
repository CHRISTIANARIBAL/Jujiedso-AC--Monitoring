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
from monitor.log_collector import (
    build_active_lookup,
    process_logs,
)

from librouteros import connect


AC_NAME = "calu-ac2"


# ---------------------------------------------------------
# GET AC
# ---------------------------------------------------------

ac = AccessConcentrator.objects.get(
    name=AC_NAME
)

print("=" * 60)
print(f"AC: {ac.name}")
print(f"IP: {ac.ip_address}")
print("=" * 60)


# ---------------------------------------------------------
# CONNECT
# ---------------------------------------------------------

print("Connecting...")

api = connect(
    username=ac.username,
    password=ac.password,
    host=ac.ip_address,
    port=8728,
)

print("CONNECTED!")


# ---------------------------------------------------------
# ACTIVE USERS
# ---------------------------------------------------------

active_users = list(
    api("/ppp/active/print")
)

print(
    f"Active users: "
    f"{len(active_users)}"
)


# ---------------------------------------------------------
# BUILD LOOKUP
# ---------------------------------------------------------

active_lookup = build_active_lookup(
    active_users
)

print(
    f"MAC lookup: "
    f"{len(active_lookup)}"
)


# ---------------------------------------------------------
# LOGS
# ---------------------------------------------------------

logs = list(
    api("/log/print")
)

print(
    f"Logs returned: "
    f"{len(logs)}"
)


# ---------------------------------------------------------
# PROCESS
# ---------------------------------------------------------

print("\nProcessing logs...\n")

created = process_logs(
    ac,
    logs,
    active_lookup
)

print()
print("=" * 60)
print(
    f"New events saved: {created}"
)
print("=" * 60)