import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from monitor.models import AccessConcentrator
from librouteros import connect


ac = AccessConcentrator.objects.get(name="calu-ac2")

print(f"Connecting to {ac.name} ({ac.ip_address})...")

api = connect(
    username=ac.username,
    password=ac.password,
    host=ac.ip_address,
    port=8728,
)
active = list(
    api("/ppp/active/print")
)

for user in active[:5]:
    print(user)
# print("CONNECTED!")

# identity = list(api("/system/identity/print"))

# print("MikroTik identity:")
# print(identity)

# # Active PPPoE sessions
# sessions = list(api("/ppp/active/print"))

# print(f"\nActive PPPoE sessions: {len(sessions)}")

# for session in sessions:
#     print(
#         f"Username: {session.get('name')} | "
#         f"IP: {session.get('address')} | "
#         f"MAC: {session.get('caller-id')}"
#     )