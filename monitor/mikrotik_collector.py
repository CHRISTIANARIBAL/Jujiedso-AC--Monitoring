from librouteros import connect
from monitor.crypto import decrypt_password
from monitor.models import PPPoEClient

def normalize_mac(mac):
    """Normalize MAC address for reliable database matching."""

    if not mac:
        return None

    return mac.strip().upper()


def get_active_sessions(ac):
    """
    Connect to a MikroTik AC and return
    its currently active PPPoE sessions.

    Also learns/updates:
        MAC -> username -> AC
    """
    password = decrypt_password(
        ac.encrypted_password
    )
    api = connect(
        username=ac.username,
        password=password,
        host=ac.ip_address,
        port=8728,
    )

    sessions = list(
        api("/ppp/active/print")
    )

    # -------------------------------------------------
    # Learn active PPPoE clients
    # -------------------------------------------------

    for session in sessions:

        username = session.get("name")
        mac = normalize_mac(
            session.get("caller-id")
        )

        if not username or not mac:
            continue

        client, created = PPPoEClient.objects.get_or_create(
            mac_address=mac,
            defaults={
                "username": username,
                "ac": ac,
            }
        )

        if not created:

            changed = False

            if client.username != username:
                client.username = username
                changed = True

            if client.ac_id != ac.id:
                client.ac = ac
                changed = True

            if changed:
                client.save()

            else:
                client.save(
                    update_fields=["last_seen"]
                )

    return sessions