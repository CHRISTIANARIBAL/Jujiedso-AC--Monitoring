import hashlib
import re
from datetime import timedelta, datetime
from django.utils import timezone
from monitor.websocket_utils import broadcast_pppoe_event
from monitor.models import PPPoESession, PPPoEEvent, PPPoEClient

IGNORED_USERS = {
    "Dave",
}
IGNORED_MACS = {
    "70:28:0A:68:DA:1A",
    "70:28:0A:68:DA:1B",
}
def normalize_mac(mac):
    if not mac:
        return None
    return mac.strip().upper()

def parse_log_timestamp(timestamp):
    if not timestamp:
        return timezone.now()
    if isinstance(timestamp, datetime):
        return timestamp
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return timezone.now()

def make_log_hash(ac, timestamp, topics, message):
    raw = (
        f"{ac.id}|"
        f"{timestamp}|"
        f"{topics}|"
        f"{message}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def build_active_lookup(active_users):
    lookup = {}
    for user in active_users:
        mac = normalize_mac(user.get("caller-id"))
        if not mac:
            continue
        lookup[mac] = {
            "username": user.get("name"),
            "ip_address": user.get("address"),
            "session_id": user.get("session-id"),
        }
    return lookup

def extract_mac(message):
    if not message:
        return None
    pattern = (
        r"\b"
        r"[0-9A-Fa-f]{2}"
        r"(?::[0-9A-Fa-f]{2}){5}"
        r"\b"
    )
    match = re.search(pattern, message)
    if not match:
        return None
    return normalize_mac(match.group(0))

def extract_username(message):
    if not message:
        return None
    match = re.search(r"<pppoe-(.+?)>:\s*(?:authenticated|connected|disconnected|terminating)", message, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    patterns = [
        r"user\s+(.+?)\s+authentication failed",
        r"user\s+(.+?)\s+logged in",
        r"user\s+(.+?)\s+logged out",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def get_event_type(topics, message):
    if not message:
        return PPPoEEvent.OTHER
    message_lower = message.lower()
    if "authentication failed" in message_lower:
        return PPPoEEvent.AUTH_FAILURE
    if re.search(r"<pppoe-.+?>:\s*authenticated", message, re.IGNORECASE):
        return PPPoEEvent.LOGIN
    if re.search(r"<pppoe-.+?>:\s*connected", message, re.IGNORECASE):
        return PPPoEEvent.CONNECTION
    if re.search(r"<pppoe-.+?>:\s*disconnected", message, re.IGNORECASE):
        return PPPoEEvent.LOGOUT
    if "logged out" in message_lower:
        return PPPoEEvent.LOGOUT
    if "logged in" in message_lower:
        return PPPoEEvent.LOGIN
    if "connection established" in message_lower:
        return PPPoEEvent.CONNECTION
    return PPPoEEvent.OTHER

def find_previous_session(ac, mac):
    if not mac:
        return None
    return (PPPoESession.objects.filter(ac=ac, mac_address__iexact=mac).order_by("-connected_at").first())

def find_client_by_mac(ac, mac):
    if not mac:
        return None
    return (PPPoEClient.objects.filter(ac=ac, mac_address__iexact=mac).order_by("-last_seen").first())

def broadcast_event(event):
    print("WS BROADCAST:", event.event_type, event.username, event.mac_address)
    broadcast_pppoe_event({
        "event": event.event_type,
        "username": event.username,
        "mac": event.mac_address,
        "ip": event.ip_address,
        "ac": event.ac.name if event.ac else None,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "message": event.raw_message,
    })
    print("WS BROADCAST SENT")
    
def process_logs(ac, logs, active_lookup):
    created_count = 0
    logs = sorted(logs, key=lambda log: parse_log_timestamp(log.get("time")))
    recent_logins = {}
    recent_logouts = {}

    for log in logs:
        topics = log.get("topics", "")
        message = log.get("message", "")
        timestamp = log.get("time")

        if "pppoe" not in topics.lower():
            continue
        if ("system" in topics.lower() and "account" in topics.lower()):
            continue

        log_hash = make_log_hash(ac, timestamp, topics, message)
        if PPPoEEvent.objects.filter(log_hash=log_hash).exists():
            continue

        mac = extract_mac(message)
        username = extract_username(message)
        if username in IGNORED_USERS:
            continue
        if mac in IGNORED_MACS:
            continue
        event_type = get_event_type(topics, message)
        if (event_type == PPPoEEvent.LOGIN and message.startswith("<pppoe-") and message.endswith(": authenticated")):
            continue
        if (event_type == PPPoEEvent.CONNECTION and message.startswith("<pppoe-") and message.endswith(": connected")):
            continue
        if (event_type == PPPoEEvent.LOGOUT and message.startswith("<pppoe-") and message.endswith(": disconnected")):
            continue
        event_timestamp = parse_log_timestamp(timestamp)
        ip_address = None
        if mac and mac in active_lookup:
            active_user = active_lookup[mac]
            username = active_user.get("username")
            ip_address = active_user.get("ip_address")

        if username and not mac:
            for lookup_mac, active_user in active_lookup.items():
                if (active_user.get("username") == username):
                    mac = lookup_mac
                    ip_address = active_user.get("ip_address")
                    break

        if username and not mac:
            previous_session = (PPPoESession.objects.filter( ac=ac,username=username).order_by("-connected_at").first())
            if previous_session:
                mac = previous_session.mac_address
                ip_address = (previous_session.ip_address)
        if username and not mac:
            client = (
                PPPoEClient.objects.filter(mac_address__iexact=mac).first() )
            if client:
                username = client.username
        if mac and not username:
            client = (PPPoEClient.objects.filter(ac=ac, mac_address__iexact=mac).order_by("-last_seen").first())
            if client:
                username = client.username
        if event_type == PPPoEEvent.AUTH_FAILURE:
            event = PPPoEEvent.objects.create(
                username=username,
                ac=ac,
                event_type=event_type,
                ip_address=ip_address,
                mac_address=mac,
                raw_message=message,
                timestamp=event_timestamp,
                log_hash=log_hash,
            )
            broadcast_event(event)
            created_count += 1
            print(
                f"EVENT: "
                f"{event_type} | "
                f"{username or 'UNKNOWN'} | "
                f"{mac or 'NO MAC'}"
            )
            continue

        if event_type in (
            PPPoEEvent.LOGIN,
            PPPoEEvent.CONNECTION,
        ):
            if not username:
                event = PPPoEEvent.objects.create(
                    username=None,
                    ac=ac,
                    event_type=event_type,
                    ip_address=ip_address,
                    mac_address=mac,
                    raw_message=message,
                    timestamp=event_timestamp,
                    log_hash=log_hash,
                )
                broadcast_event(event)
                created_count += 1
                print(
                    f"EVENT: "
                    f"{event_type} | "
                    f"UNKNOWN | "
                    f"{mac or 'NO MAC'}"
                )
                continue

            if event_type == PPPoEEvent.CONNECTION:
                previous_login = recent_logins.get(username)
                if previous_login:
                    difference = (event_timestamp - previous_login["timestamp"])
                    if (difference >= timedelta(seconds=0) and difference <= timedelta(seconds=2)):
                        continue

            if event_type == PPPoEEvent.LOGIN:
                recent_logins[username] = {
                    "timestamp": event_timestamp,
                    "mac": mac,
                }
                event = PPPoEEvent.objects.create(
                    username=username,
                    ac=ac,
                    event_type=PPPoEEvent.LOGIN,
                    ip_address=ip_address,
                    mac_address=mac,
                    raw_message=message,
                    timestamp=event_timestamp,
                    log_hash=log_hash,
                )
                broadcast_event(event)
                created_count += 1
                print(
                    f"EVENT: LOGIN | "
                    f"{username} | "
                    f"{mac or 'NO MAC'}"
                )
                continue
        # LOGOUT
        if event_type == PPPoEEvent.LOGOUT:
            if not username:
                event = PPPoEEvent.objects.create(
                    username=None,
                    ac=ac,
                    event_type=event_type,
                    ip_address=ip_address,
                    mac_address=mac,
                    raw_message=message,
                    timestamp=event_timestamp,
                    log_hash=log_hash,
                )
                broadcast_event(event)
                created_count += 1
                print(
                    f"EVENT: LOGOUT | "
                    f"UNKNOWN | "
                    f"{mac or 'NO MAC'}"
                )
                continue

            previous_logout = recent_logouts.get(username)
            if previous_logout:
                difference = (event_timestamp - previous_logout["timestamp"])
                if (difference >= timedelta(seconds=0) and difference <= timedelta(seconds=2)):
                    continue
            # Record logout
            recent_logouts[username] = {
                "timestamp": event_timestamp,
                "mac": mac,
            }
            event = PPPoEEvent.objects.create(
                username=username,
                ac=ac,
                event_type=PPPoEEvent.LOGOUT,
                ip_address=ip_address,
                mac_address=mac,
                raw_message=message,
                timestamp=event_timestamp,
                log_hash=log_hash,
            )
            broadcast_event(event)
            created_count += 1
            print(
                f"EVENT: LOGOUT | "
                f"{username} | "
                f"{mac or 'NO MAC'}"
            )
            continue

        if event_type == PPPoEEvent.OTHER:
            if (username and "terminating" in message.lower()):
                continue
            event = PPPoEEvent.objects.create(
                username=username,
                ac=ac,
                event_type=event_type,
                ip_address=ip_address,
                mac_address=mac,
                raw_message=message,
                timestamp=event_timestamp,
                log_hash=log_hash,
            )
            broadcast_event(event)
            created_count += 1
            print(
                f"EVENT: OTHER | "
                f"{username or 'UNKNOWN'} | "
                f"{mac or 'NO MAC'}"
            )
    return created_count