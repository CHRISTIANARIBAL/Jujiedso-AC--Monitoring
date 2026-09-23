from django.utils import timezone
from .models import *
from .mikrotik_collector import get_connection_info


def sync_ac_sessions(ac, mikrotik_sessions=None, api=None):
    if mikrotik_sessions is None:
        raise ValueError("mikrotik_sessions is required")

    current_users = {}

    pppoe_interfaces = []

    if api is not None:
        pppoe_interfaces = list(
            api.path("interface", "pppoe-server").select(
                "name",
                "user",
                "service",
                "interface",
            )
        )

    connection_map = {}

    for row in pppoe_interfaces:
        username = row.get("user")
        interface = row.get("interface")

        if username and interface:
            connection_map[username] = interface

    for session in mikrotik_sessions:
        username = session.get("name")
        mac = session.get("caller-id")

        if not username:
            continue

        connection_interface = connection_map.get(username)
        connection_type, connection_name = get_connection_info(
            connection_interface
        )

        current_users[username] = {
            "ip_address": session.get("address"),
            "mac_address": mac,
            "connection_type": connection_type,
            "connection_name": connection_name,
            "connection_interface": connection_interface,
        }

    database_sessions = {
        session.username: session
        for session in PPPoESession.objects.filter(
            ac=ac,
            active=True,
        )
    }

    for username, data in current_users.items():
        if data["mac_address"]:
            client = (
                PPPoEClient.objects
                .filter(
                    username=username,
                    ac=ac,
                    mac_address=data["mac_address"].strip().upper(),
                )
                .order_by("-last_seen", "-id")
                .first()
            )

            if not client:
                client = PPPoEClient.objects.create(
                    username=username,
                    mac_address=data["mac_address"].strip().upper(),
                    ac=ac,
                    connection_type=data["connection_type"],
                    connection_name=data["connection_name"],
                    connection_interface=data["connection_interface"],
                )
            else:
                client.connection_type = data["connection_type"]
                client.connection_name = data["connection_name"]
                client.connection_interface = data["connection_interface"]
                client.last_seen = timezone.now()
                client.save(
                    update_fields=[
                        "connection_type",
                        "connection_name",
                        "connection_interface",
                        "last_seen",
                    ]
                )

        if username not in database_sessions:
            PPPoESession.objects.create(
                username=username,
                ac=ac,
                ip_address=data["ip_address"],
                mac_address=data["mac_address"],
                connected_at=timezone.now(),
                active=True,
            )
        else:
            session = database_sessions[username]
            session.ip_address = data["ip_address"]
            session.mac_address = data["mac_address"]
            session.save(update_fields=["ip_address", "mac_address"])

    for username, session in database_sessions.items():
        if username not in current_users:
            session.active = False
            session.disconnected_at = timezone.now()
            session.save(update_fields=["active", "disconnected_at"])

    return len(current_users)