from librouteros import connect
from monitor.crypto import decrypt_password
from monitor.models import PPPoEClient

TECHNICIAN_USERS = {
    "0912test",
    "bobot01",
    "jerald01",
    "joel01",
}

def normalize_mac(mac):
    if not mac:
        return None
    return mac.strip().upper()


def get_connection_info(interface):
    if not interface:
        return None, None

    interface_lower = interface.lower()

    if "media-con" in interface_lower:
        parts = interface.split("-media-con", 1)

        if len(parts) == 2:
            media_part = parts[1].strip()

            media_part = media_part.rstrip()
            media_part = media_part.replace(" olt", "")

            media_name = f"MEDIA-CON{media_part}".upper()

            return "MediaCon", media_name

        return "MediaCon", interface

    parts = interface.split("-", 2)

    if len(parts) >= 3:
        name = parts[2].upper()

        if "OLT" in name:
            return "OLT", name

    return "Unknown", interface


def get_active_sessions(ac):
    password = decrypt_password(ac.encrypted_password)

    api = connect(
        username=ac.username,
        password=password,
        host=ac.ip_address,
        port=8728,
    )

    sessions = list(api("/ppp/active/print"))

    pppoe_interfaces = list(
        api.path("interface", "pppoe-server").select(
            "name",
            "user",
            "service",
            "interface",
        )
    )

    olt_map = {}

    for row in pppoe_interfaces:
        username = row.get("user")
        interface = row.get("interface")

        if username and interface:
            olt_map[username] = interface

    for session in sessions:
        username = session.get("name")
        mac = normalize_mac(session.get("caller-id"))

        if not username or not mac:
            continue

        if username.lower() in TECHNICIAN_USERS:
            continue

        olt_interface = olt_map.get(username)
        olt_name = None
        connection_type, connection_name = get_connection_info(olt_interface)

        client = (
            PPPoEClient.objects
            .filter(
                username=username,
                ac=ac,
                mac_address=mac,
            )
            .order_by("-last_seen", "-id")
            .first()
        )

        created = False

        if not client:
            client = PPPoEClient.objects.create(
                username=username,
                mac_address=mac,
                ac=ac,
                olt_interface=olt_interface,
                olt_name=olt_name,
                connection_type=connection_type,
                connection_name=connection_name,
                connection_interface=olt_interface,
            )
            created = True

        if not created:
            changed = False

            if client.mac_address != mac:
                client.mac_address = mac
                changed = True

            if client.olt_interface != olt_interface:
                client.olt_interface = olt_interface
                changed = True

            if client.olt_name != olt_name:
                client.olt_name = olt_name
                changed = True

            if client.connection_type != connection_type:
                client.connection_type = connection_type
                changed = True

            if client.connection_name != connection_name:
                client.connection_name = connection_name
                changed = True

            if client.connection_interface != olt_interface:
                client.connection_interface = olt_interface
                changed = True

            if changed:
                client.save()
            else:
                client.save(update_fields=["last_seen"])

    return sessions