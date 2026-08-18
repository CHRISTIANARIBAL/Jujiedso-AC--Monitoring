import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from monitor.models import AccessConcentrator
from monitor.mikrotik_collector import get_active_sessions


acs = AccessConcentrator.objects.filter(enabled=True)

for ac in acs:

    print("=" * 60)
    print(f"AC: {ac.name}")
    print(f"IP: {ac.ip_address}")

    try:
        sessions = get_active_sessions(ac)

        print(f"Active PPPoE users: {len(sessions)}")

        # Only display first 5
        for session in sessions[:5]:
            print(
                f"  {session.get('name')} | "
                f"{session.get('address')} | "
                f"{session.get('caller-id')}"
            )

    except Exception as e:
        print(f"ERROR: {e}")