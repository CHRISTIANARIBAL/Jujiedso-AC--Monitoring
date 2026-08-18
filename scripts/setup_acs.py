import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from monitor.models import AccessConcentrator
from monitor.crypto import encrypt_password
from getpass import getpass

password = getpass("Enter AC password: ")
encrypted_password = encrypt_password(password)


ACS = [
    {
        "name": "calu-ac1 new",
        "ip_address": "43.228.106.2",
        "username": "christian",
        # "password": "chr1st14n",
    },

    {
        "name": "calu-ac2",
        "ip_address": "43.228.106.3",
        "username": "christian",
        # "password": "chr1st14n",
    },

    {
        "name": "calu-ac3",
        "ip_address": "43.228.106.4",
        "username": "christian",
        # "password": "chr1st14n",
    },
]

for ac in ACS:
    obj, created = AccessConcentrator.objects.update_or_create(
        name=ac["name"],
        defaults={
            "ip_address": ac["ip_address"],
            "username": ac["username"],
            "encrypted_password": encrypted_password,
            "enabled": True,
        },
    )

    if created:
        print(f"Added: {obj.name}")
    else:
        print(f"Updated: {obj.name}")
# # Add or update configured ACs
# for ac in ACS:
#     obj, created = AccessConcentrator.objects.update_or_create(
#         name=ac["name"],
#         defaults={
#             "ip_address": ac["ip_address"],
#             "username": ac["username"],
#             "password": ac["password"],
#             "enabled": True,
#         },
#     )

#     if created:
#         print(f"Added: {obj.name}")
#     else:
#         print(f"Updated: {obj.name}")


# # Disable ACs that are not in the current ACS list
# active_names = [ac["name"] for ac in ACS]

# disabled_count = AccessConcentrator.objects.exclude(
#     name__in=active_names
# ).update(enabled=False)


# print(f"Disabled ACs: {disabled_count}")
# print("AC setup complete.")