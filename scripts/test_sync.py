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
from monitor.session_sync import sync_ac_sessions


ac = AccessConcentrator.objects.get(
    name="calu-ac2"
)

sync_ac_sessions(ac)