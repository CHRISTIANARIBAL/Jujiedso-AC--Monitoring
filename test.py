import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from librouteros import connect
from monitor.crypto import decrypt_password
from monitor.models import AccessConcentrator

ac = AccessConcentrator.objects.get(name="calu-ac1 new")

password = decrypt_password(ac.encrypted_password)

print("Connecting to:", ac.ip_address)
print("API username:", ac.username)

api = connect(
    username=ac.username,
    password=password,
    host=ac.ip_address,
    port=8728,
)

print("Connected!")

username = "alangalang01nietoe"

results = list(
    api.path("interface", "pppoe-server").select(
        "name",
        "user",
        "service",
        "interface"
    )
)

print("\nRESULT:")

for row in results:
    if row.get("user") == username:
        print(row)