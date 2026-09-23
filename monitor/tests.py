import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from librouteros import connect
from monitor.crypto import decrypt_password
from monitor.models import AccessConcentrator

ac = AccessConcentrator.objects.get(name="calu-ac1 new")

password = decrypt_password(ac.encrypted_password)

api = connect(
    username=ac.username,
    password=password,
    host=ac.ip_address,
    port=8728,
)

username = "alangalang01nietoe"

results = list(
    api("/interface/pppoe-server/print",
        {
            "?user": username,
            ".proplist": "name,user,service,interface"
        }
    )
)

print("\nRESULT:")
for row in results:
    print(row)