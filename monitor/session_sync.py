from django.utils import timezone

from .models import *
from .mikrotik_collector import get_active_sessions


def sync_ac_sessions(ac, mikrotik_sessions=None):

    # --------------------------------------------------
    # Get current sessions from MikroTik
    # --------------------------------------------------

    if mikrotik_sessions is None:
        mikrotik_sessions = get_active_sessions(ac)

    # --------------------------------------------------
    # Build current users dictionary
    # --------------------------------------------------

    current_users = {}

    for session in mikrotik_sessions:

        username = session.get("name")

        if not username:
            continue

        current_users[username] = {
            "ip_address": session.get("address"),
            "mac_address": session.get("caller-id"),
        }

    # --------------------------------------------------
    # Get sessions currently stored in database
    # --------------------------------------------------

    database_sessions = {
        session.username: session
        for session in PPPoESession.objects.filter(
            ac=ac,
            active=True,
        )
    }

    # --------------------------------------------------
    # NEW / EXISTING USERS
    # --------------------------------------------------

    for username, data in current_users.items():
        if data["mac_address"]:

            PPPoEClient.objects.update_or_create(
                username=username,
                mac_address=data["mac_address"],
                ac=ac,
            )
        if username not in database_sessions:

            # New active session
            PPPoESession.objects.create(
                username=username,
                ac=ac,
                ip_address=data["ip_address"],
                mac_address=data["mac_address"],
                connected_at=timezone.now(),
                active=True,
            )

        else:

            # Existing active session
            session = database_sessions[username]

            session.ip_address = data["ip_address"]
            session.mac_address = data["mac_address"]

            session.save(
                update_fields=[
                    "ip_address",
                    "mac_address",
                ]
            )

    # --------------------------------------------------
    # DISCONNECTED USERS
    # --------------------------------------------------

    for username, session in database_sessions.items():

        if username not in current_users:

            session.active = False
            session.disconnected_at = timezone.now()

            session.save(
                update_fields=[
                    "active",
                    "disconnected_at",
                ]
            )

    return len(current_users)