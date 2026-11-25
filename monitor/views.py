from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import JsonResponse, Http404
from monitor.models import AccessConcentrator
from monitor.websocket_utils import broadcast_pppoe_event
from django.utils import timezone
from django.conf import settings
import os
from .models import *
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from librouteros import connect
from monitor.crypto import decrypt_password
from monitor.models import AccessConcentrator
from librouteros.query import Key
from monitor.log_collector import IGNORED_USERS, IGNORED_MACS
from monitor.location_detection import get_location_summary
from collections import defaultdict

RAW_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "management",
    "raw_logs",
)

def client_traffic_history(request):
    username = request.GET.get("username")
    range_value = request.GET.get("range", "1h").lower()
    since_timestamp = request.GET.get("since")

    if not username:
        return JsonResponse({
            "found": False,
            "message": "Username is required.",
        })

    ranges = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "12h": timedelta(hours=12),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "15d": timedelta(days=15),
    }

    if range_value not in ranges:
        range_value = "1h"

    since = timezone.now() - ranges[range_value]

    if since_timestamp:
        try:
            since = max(
                since,
                timezone.datetime.fromisoformat(
                    since_timestamp.replace("Z", "+00:00")
                ),
            )
        except ValueError:
            pass

    history = (
        PPPoETrafficHistory.objects
        .filter(
            client__username=username,
            timestamp__gte=since,
        )
        .order_by("timestamp")
    )

    samples = [
        {
            "timestamp": row.timestamp.isoformat(),
            "rx": row.rx_bits_per_second,
            "tx": row.tx_bits_per_second,
        }
        for row in history
    ]

    return JsonResponse({
        "found": True,
        "username": username,
        "range": range_value,
        "samples": samples,
    })


def get_raw_log_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "management",
        "raw_logs",
    )

@login_required
def dashboard(request):
    query = request.GET.get("q", "").strip()
    acs = AccessConcentrator.objects.filter(enabled=True)
    ac_data = []
    total_active_users = 0

    for ac in acs:
        active_users = PPPoESession.objects.filter(ac=ac, active=True).count()
        total_active_users += active_users
        ac_data.append({
            "ac": ac,
            "active_users": active_users,
        })
    events = (PPPoEEvent.objects.select_related("ac").exclude(username__in=IGNORED_USERS).exclude(mac_address__in=IGNORED_MACS))

    if query:
        events = events.filter(Q(username__icontains=query) | Q(mac_address__icontains=query) | Q(ip_address__icontains=query))
    recent_events = events.order_by("-timestamp")[:50]

    context = {
        "ac_data": ac_data,
        "total_active_users": total_active_users,
        "recent_events": recent_events,
        "query": query,
    }

    return render(request, "monitor/dashboard.html", context)

@login_required
def client_info(request):
    client_id = request.GET.get("id", "").strip()
    query = request.GET.get("q", "").strip()

    def build_connection_history(username, mac):
        if not mac:
            return []
        since = timezone.now() - timedelta(days=7)
        events = list(
            PPPoEEvent.objects.filter(
                mac_address=mac,
                event_type__in=[PPPoEEvent.LOGIN, PPPoEEvent.LOGOUT],
                timestamp__gte=since,
            )
            .select_related("ac")
            .order_by("timestamp")
        )
        history = []
        current_login = None

        for event in events:
            if event.event_type == PPPoEEvent.LOGIN:
                current_login = event
            elif event.event_type == PPPoEEvent.LOGOUT and current_login:
                duration_seconds = int(
                    (event.timestamp - current_login.timestamp).total_seconds()
                )
                if duration_seconds < 0:
                    duration_seconds = 0

                history.append({
                    "up_time": current_login.timestamp.isoformat(),
                    "down_time": event.timestamp.isoformat(),
                    "up_ac": current_login.ac.name if current_login.ac else None,
                    "down_ac": event.ac.name if event.ac else None,
                    "duration_seconds": duration_seconds,
                    "active": False,
                })
                current_login = None

        if current_login:
            duration_seconds = int(
                (timezone.now() - current_login.timestamp).total_seconds()
            )
            if duration_seconds < 0:
                duration_seconds = 0

            history.append({
                "up_time": current_login.timestamp.isoformat(),
                "down_time": None,
                "up_ac": current_login.ac.name if current_login.ac else None,
                "down_ac": None,
                "duration_seconds": duration_seconds,
                "active": True,
            })

        history.sort(key=lambda item: item["up_time"], reverse=True)
        return history

    if client_id:
        try:
            client = (
                PPPoEClient.objects
                .select_related("ac")
                .get(id=client_id)
            )
        except PPPoEClient.DoesNotExist:
            return JsonResponse({
                "found": False,
                "message": "Client not found."
            })

        username = client.username
        mac = client.mac_address

        session = (
            PPPoESession.objects
            .filter(
                username=username,
                mac_address=mac,
                ac=client.ac,
                active=True,
            )
            .select_related("ac")
            .order_by("-connected_at")
            .first()
        )

        # plan_data = get_client_plan(
        #     username,
        #     session.ac if session and session.active else client.ac,
        # )

        login_event = (
            PPPoEEvent.objects
            .filter(
                username=username,
                mac_address=mac,
                event_type=PPPoEEvent.LOGIN,
            )
            .order_by("-timestamp")
            .first()
        )

        logout_event = (
            PPPoEEvent.objects
            .filter(
                username=username,
                mac_address=mac,
                event_type=PPPoEEvent.LOGOUT,
            )
            .order_by("-timestamp")
            .first()
        )

        connected_at = None

        if session and session.connected_at:
            connected_at = session.connected_at
        elif login_event:
            connected_at = login_event.timestamp

        last_down_time = logout_event.timestamp if logout_event else None

        duration_seconds = None

        if connected_at:
            if session and session.active:
                end_time = timezone.now()
            elif logout_event:
                end_time = logout_event.timestamp
            else:
                end_time = timezone.now()

            duration_seconds = int(
                (end_time - connected_at).total_seconds()
            )

            if duration_seconds < 0:
                duration_seconds = 0

        connection_history = build_connection_history(username, mac)
        plan_data = get_client_plan_with_memory(
            username,
            session.ac if session and session.active else client.ac,
        )
        return JsonResponse({
            "found": True,
            "username": username or "UNKNOWN",
            "mac": mac or "No MAC",

            "plan": plan_data["plan"],
            "version": plan_data.get("version"),
            "max_limit": plan_data["max_limit"],
            "bandwidth_mbps": plan_data["bandwidth_mbps"],

            "version": plan_data.get("version"),
            "last_plan": plan_data.get("last_plan"),
            "last_plan_version": plan_data.get("last_plan_version"),
            "last_bandwidth_mbps": plan_data.get("last_bandwidth_mbps"),

            # New generic connection fields
            "connection_type": client.connection_type,
            "connection_name": client.connection_name,
            "connection_interface": client.connection_interface,

            # Keep old fields for compatibility
            "olt_name": client.olt_name,
            "olt_interface": client.olt_interface,

            "ip": session.ip_address if session else "No IP",
            "up_time": connected_at.isoformat() if connected_at else None,
            "last_down_time": last_down_time.isoformat() if last_down_time else None,
            "last_down_ac": (
                logout_event.ac.name
                if logout_event and logout_event.ac
                else client.ac.name if client.ac
                else None
            ),
            "duration_seconds": duration_seconds,
            "active_ac": (
                session.ac.name
                if session and session.active
                else None
            ),
            "connection_history": connection_history,
        })

    if not query:
        return JsonResponse({
            "found": False,
            "message": "Please enter a username, MAC address, or IP address."
        })

    session = (
        PPPoESession.objects
        .filter(
            Q(username__icontains=query) |
            Q(mac_address__icontains=query) |
            Q(ip_address__icontains=query)
        )
        .select_related("ac")
        .order_by("-connected_at")
        .first()
    )

    client = (
        PPPoEClient.objects
        .filter(
            Q(username__icontains=query) |
            Q(mac_address__icontains=query)
        )
        .select_related("ac")
        .order_by("-last_seen")
        .first()
    )

    if not session and not client:
        event = (
            PPPoEEvent.objects
            .filter(
                Q(username__icontains=query) |
                Q(mac_address__icontains=query) |
                Q(ip_address__icontains=query)
            )
            .select_related("ac")
            .order_by("-timestamp")
            .first()
        )

        if not event:
            return JsonResponse({
                "found": False,
                "message": "Client not found."
            })

        username = event.username
        mac = event.mac_address
        ip = event.ip_address
        active_ac = event.ac if event.event_type == PPPoEEvent.LOGIN else None

    else:
        if session:
            username = session.username
            mac = session.mac_address
            ip = session.ip_address
            active_ac = session.ac if session.active else None
        else:
            username = client.username
            mac = client.mac_address
            ip = None
            active_ac = None

    login_event = (
        PPPoEEvent.objects
        .filter(
            username=username,
            mac_address=mac,
            event_type=PPPoEEvent.LOGIN,
        )
        .order_by("-timestamp")
        .first()
    )

    logout_event = (
        PPPoEEvent.objects
        .filter(
            username=username,
            mac_address=mac,
            event_type=PPPoEEvent.LOGOUT,
        )
        .order_by("-timestamp")
        .first()
    )

    connected_at = None

    if session and session.active:
        connected_at = session.connected_at
    elif login_event:
        connected_at = login_event.timestamp

    last_down_time = logout_event.timestamp if logout_event else None

    duration_seconds = None

    if connected_at:
        if session and session.active:
            end_time = timezone.now()
        elif logout_event:
            end_time = logout_event.timestamp
        else:
            end_time = timezone.now()

        duration_seconds = int(
            (end_time - connected_at).total_seconds()
        )

        if duration_seconds < 0:
            duration_seconds = 0

    connection_history = build_connection_history(username, mac)

    plan_data = get_client_plan_with_memory(
        username,
        session.ac if session and session.active else (
            active_ac or (client.ac if client else None)
        ),
    )
    return JsonResponse({
        "found": True,
        "username": username or "UNKNOWN",
        "mac": mac or "No MAC",
        "ip": ip or "No IP",
        "up_time": connected_at.isoformat() if connected_at else None,
        "last_down_time": last_down_time.isoformat() if last_down_time else None,
        "last_down_ac": (
            logout_event.ac.name
            if logout_event and logout_event.ac
            else None
        ),
        "duration_seconds": duration_seconds,
        "active_ac": active_ac.name if active_ac else None,

        "plan": plan_data["plan"],
        "version": plan_data.get("version"),
        "max_limit": plan_data["max_limit"],
        "bandwidth_mbps": plan_data["bandwidth_mbps"],
        # Generic connection information
        "connection_type": client.connection_type if client else None,
        "connection_name": client.connection_name if client else None,
        "connection_interface": client.connection_interface if client else None,

        # Old fields retained
        "olt_name": client.olt_name if client else None,
        "olt_interface": client.olt_interface if client else None,

        "connection_history": connection_history,
    })

@login_required
def test_broadcast(request):
    broadcast_pppoe_event({
        "type": "test",
        "event": "TEST",
        "username": "TestUser",
        "mac": "AA:BB:CC:DD:EE:FF",
    })

    return JsonResponse({
        "status": "broadcast sent"
    })

@login_required
def raw_logs(request):
    raw_log_dir = get_raw_log_directory()

    ac_logs = []
    acs = AccessConcentrator.objects.filter(enabled=True).order_by("id")

    for ac in acs:
        ac_directory = os.path.join(raw_log_dir, ac.name)

        files = []

        if os.path.isdir(ac_directory):
            for filename in os.listdir(ac_directory):
                if not filename.lower().endswith(".txt"):
                    continue

                file_path = os.path.join(ac_directory, filename)

                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = sum(1 for _ in f)
                    except OSError:
                        line_count = 0

                    files.append({
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "lines": line_count,
                    })

        files.sort(key=lambda x: x["name"], reverse=True)

        ac_logs.append({
            "ac": ac,
            "files": files,
        })

    return render(
        request,
        "monitor/raw_logs.html",
        {"ac_logs": ac_logs},
    )

@login_required
def raw_log_viewer(request, ac_name, filename):
    ac_directory = os.path.join(RAW_LOG_DIR, ac_name)
    file_path = os.path.join(ac_directory, filename)

    if not os.path.isfile(file_path):
        raise Http404("Log file not found.")
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            log_content = file.read()
    except Exception as e:
        raise Http404(f"Unable to read log file: {e}")
    return render(request, "monitor/raw_log_viewer.html",
        {
            "ac_name": ac_name,
            "filename": filename,
            "log_content": log_content,
        },
    )

@login_required
def client_search(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({
            "found": False,
            "results": [],
            "message": "Please enter a search term."
        })

    clients = (
        PPPoEClient.objects
        .filter(
            Q(username__icontains=query) |
            Q(mac_address__icontains=query)
        )
        .select_related("ac")
        .order_by("-last_seen", "-id")
    )

    grouped_clients = {}

    for client in clients:
        key = (
            client.username.lower(),
            (client.mac_address or "").lower(),
        )

        if key not in grouped_clients:
            grouped_clients[key] = []

        grouped_clients[key].append(client)

    results = []

    for client_key, client_records in grouped_clients.items():
        username = client_records[0].username
        mac = client_records[0].mac_address

        active_session = (
            PPPoESession.objects
            .filter(
                username=username,
                mac_address=mac,
                active=True,
            )
            .select_related("ac")
            .order_by("-connected_at")
            .first()
        )

        if active_session:
            active = True
            ac = active_session.ac

            client = next(
                (
                    record
                    for record in client_records
                    if record.ac_id == active_session.ac_id
                ),
                client_records[0]
            )
        else:
            active = False
            client = client_records[0]
            ac = client.ac

        results.append({
            "id": client.id,
            "username": username,
            "mac": mac,
            "ac": ac.name if ac else None,

            # New generic connection information
            "connection_type": client.connection_type,
            "connection_name": client.connection_name,
            "connection_interface": client.connection_interface,

            # Keep old fields for compatibility
            "olt_name": client.olt_name,
            "olt_interface": client.olt_interface,

            "active": active,
        })

    results.sort(
        key=lambda x: (
            not x["active"],
            (x["username"] or "").lower()
        )
    )

    return JsonResponse({
        "found": bool(results),
        "results": results,
        "message": (
            "Clients found."
            if results
            else "Client not found."
        )
    })

@login_required
def client_traffic(request):
    username = request.GET.get("username", "").strip()

    if not username:
        return JsonResponse({
            "found": False,
            "message": "Username is required."
        })

    # Find the currently active PPPoE session
    session = (
        PPPoESession.objects
        .filter(
            username=username,
            active=True
        )
        .select_related("ac")
        .order_by("-connected_at")
        .first()
    )

    if not session:
        return JsonResponse({
            "found": False,
            "message": "Client is currently offline."
        })

    if not session.ac:
        return JsonResponse({
            "found": False,
            "message": "No Access Concentrator found."
        })

    ac = session.ac

    # MikroTik PPPoE dynamic interface name
    interface_name = f"<pppoe-{username}>"

    api = None

    try:
        password = decrypt_password(ac.encrypted_password)

        api = connect(
            username=ac.username,
            password=password,
            host=ac.ip_address,
            port=8728,
        )

        traffic = list(
            api(
                "/interface/monitor-traffic",
                **{
                    "interface": interface_name,
                    "once": "yes",
                }
            )
        )

        if not traffic:
            return JsonResponse({
                "found": False,
                "message": "No traffic data returned."
            })

        data = traffic[0]

        return JsonResponse({
            "found": True,
            "username": username,
            "interface": interface_name,
            "ac": ac.name,

            "rx_bits_per_second": data.get(
                "rx-bits-per-second", 0
            ),

            "tx_bits_per_second": data.get(
                "tx-bits-per-second", 0
            ),

            "rx_packets_per_second": data.get(
                "rx-packets-per-second", 0
            ),

            "tx_packets_per_second": data.get(
                "tx-packets-per-second", 0
            ),

            "rx_bits": data.get("rx-bits", 0),
            "tx_bits": data.get("tx-bits", 0),

        })

    except Exception as e:

        return JsonResponse({
            "found": False,
            "message": str(e)
        })

    finally:
        if api:
            try:
                api.close()
            except Exception:
                pass

def identify_v2_plan(max_limit, burst_threshold, burst_limit):
    """
    Identify verified V2 plans using actual MikroTik queue configurations.
    Returns None if the configuration does not match a verified V2 plan.
    """

    def normalize_rate(value):
        value = str(value or "").strip().lower().replace(" ", "")

        multiplier = 1

        if value.endswith("k"):
            multiplier = 1_000
            value = value[:-1]
        elif value.endswith("m"):
            multiplier = 1_000_000
            value = value[:-1]
        elif value.endswith("g"):
            multiplier = 1_000_000_000
            value = value[:-1]

        return int(round(float(value) * multiplier))

    def parse_symmetric_rate(value):
        parts = str(value or "").split("/")

        if len(parts) != 2:
            return None

        upload = normalize_rate(parts[0])
        download = normalize_rate(parts[1])

        if upload != download:
            return None

        return upload

    committed = parse_symmetric_rate(max_limit)
    threshold = parse_symmetric_rate(burst_threshold)
    burst = parse_symmetric_rate(burst_limit)

    if None in (committed, threshold, burst):
        return None

    v2_plans = {
        (10_240_000, 75_000_000, 97_280_000):
            {"plan": "Sparrow V2", "bandwidth_mbps": 10},

        (20_480_000, 95_000_000, 206_800_000):
            {"plan": "Falcon V2", "bandwidth_mbps": 20},

        (30_720_000, 230_000_000, 409_600_000):
            {"plan": "Hawk V2", "bandwidth_mbps": 30},

        (51_200_000, 280_000_000, 512_000_000):
            {"plan": "Phoenix V2", "bandwidth_mbps": 50},
        
        (61_440_000, 203_600_000, 317_200_000): {
            "plan": "Eagle", "bandwidth_mbps": 60},
    }

    return v2_plans.get((committed, threshold, burst))

def get_client_plan(username, ac):
    """
    Identify a PPPoE client's plan.

    Priority:
    1. Disconnected detection
    2. Verified V2 configurations
    3. Original V1 max-limit mapping
    4. Unknown plan
    """

    if not username or not ac:
        return {
            "plan": "Unknown plan",
            "max_limit": None,
            "bandwidth_mbps": None,
        }

    api = None

    def normalize_rate(value):
        """Convert RouterOS rate values to bits per second."""
        value = str(value).strip().lower().replace(" ", "")

        multiplier = 1

        if value.endswith("k"):
            multiplier = 1_000
            value = value[:-1]
        elif value.endswith("m"):
            multiplier = 1_000_000
            value = value[:-1]
        elif value.endswith("g"):
            multiplier = 1_000_000_000
            value = value[:-1]

        return int(round(float(value) * multiplier))


    def parse_rate_pair(value):
        parts = str(value or "").split("/")

        if len(parts) != 2:
            return None

        upload = normalize_rate(parts[0])
        download = normalize_rate(parts[1])

        return upload, download


    def discover_queue_configurations(ac):
        api = None
        discovered = defaultdict(list)

        try:
            password = decrypt_password(ac.encrypted_password)

            api = connect(
                username=ac.username,
                password=password,
                host=ac.ip_address,
                port=8728,
            )

            queues = list(
                api.path("/queue/simple").select(
                    Key("name"),
                    Key("max-limit"),
                    Key("burst-threshold"),
                    Key("burst-limit"),
                )
            )

            for queue in queues:
                name = queue.get("name", "")

                # Only inspect PPPoE client queues.
                if not name.startswith("<pppoe-"):
                    continue

                committed = parse_rate_pair(
                    queue.get("max-limit")
                )
                threshold = parse_rate_pair(
                    queue.get("burst-threshold")
                )
                burst = parse_rate_pair(
                    queue.get("burst-limit")
                )

                if not committed or not threshold or not burst:
                    continue

                # Keep asymmetric configurations visible too.
                config = (committed, threshold, burst)

                discovered[config].append(name)

            return discovered

        finally:
            if api is not None:
                try:
                    api.close()
                except Exception:
                    pass

    def parse_queue_rate(value):
        """Read a symmetric upload/download rate pair."""
        if not value:
            return None

        parts = str(value).strip().split("/")

        if len(parts) != 2:
            return None

        upload = normalize_rate(parts[0])
        download = normalize_rate(parts[1])

        if upload is None or download is None:
            return None

        if upload != download:
            return None

        return upload

    try:
        password = decrypt_password(ac.encrypted_password)

        api = connect(
            username=ac.username,
            password=password,
            host=ac.ip_address,
            port=8728,
        )

        queue_name = f"<pppoe-{username}>"

        queues = list(
            api.path("/queue/simple")
            .select(
                Key("name"),
                Key("max-limit"),
                Key("burst-threshold"),
                Key("burst-limit"),
            )
            .where(Key("name") == queue_name)
        )

        if not queues:
            # Check whether the PPPoE client is currently active.
            active_sessions = list(
                api.path("/ppp/active")
                .select(
                    Key("name"),
                )
                .where(Key("name") == username)
            )

            if not active_sessions:
                return {
                    "plan": "Disconnected",
                    "max_limit": None,
                    "bandwidth_mbps": None,
                }

            return {
                "plan": "Unknown plan",
                "max_limit": None,
                "bandwidth_mbps": None,
            }

        queue = queues[0]

        max_limit = queue.get("max-limit", "")
        burst_threshold = queue.get("burst-threshold", "")
        burst_limit = queue.get("burst-limit", "")

        normalized = str(max_limit).replace(" ", "").lower()

        # -------------------------------------------------
        # 1. ORIGINAL DISCONNECTED DETECTION - PRESERVED
        # -------------------------------------------------
        if normalized in ("1000/1000", "1k/1k"):
            return {
                "plan": "Disconnected",
                "max_limit": max_limit,
                "bandwidth_mbps": None,
            }

        # -------------------------------------------------
        # 2. VERIFIED V2 CONFIGURATIONS
        # Uses the separate V2 identification function.
        # -------------------------------------------------

        v2_info = identify_v2_plan(
            max_limit,
            burst_threshold,
            burst_limit,
        )

        if v2_info:
            return {
                "plan": v2_info["plan"],
                "max_limit": max_limit,
                "bandwidth_mbps": v2_info["bandwidth_mbps"],
                "version": "V2",
                "burst_threshold": burst_threshold,
                "burst_limit": burst_limit,
            }

        # -------------------------------------------------
        # 3. ORIGINAL V1 LOGIC - PRESERVED
        # Do not change these original mappings.
        # -------------------------------------------------

        plans = {
            "10240k/10240k": ("Sparrow", 10),
            "10240000/10240000": ("Sparrow", 10),

            "20480k/20480k": ("Falcon", 20),
            "20480000/20480000": ("Falcon", 20),

            "30720k/30720k": ("Hawk", 30),
            "30720000/30720000": ("Hawk", 30),

            "40960k/40960k": ("Phoenix", 40),
            "40960000/40960000": ("Phoenix", 40),
        }

        plan_info = plans.get(normalized)

        if not plan_info:
            return {
                "plan": "Unknown plan",
                "max_limit": max_limit or None,
                "bandwidth_mbps": None,
            }

        return {
            "plan": plan_info[0],
            "max_limit": max_limit,
            "bandwidth_mbps": plan_info[1],
            "version": "V1",
            "burst_threshold": burst_threshold,
            "burst_limit": burst_limit,
        }

    except Exception as exc:
        print(f"Plan lookup error for {username}: {exc}")

        return {
            "plan": "Unavailable",
            "max_limit": None,
            "bandwidth_mbps": None,
        }

    finally:
        if api is not None:
            try:
                api.close()
            except Exception:
                pass


def get_client_plan_with_memory(username, ac):
    """
    Detect the live plan and remember it.
    If disconnected, retrieve the last successfully detected plan.
    """

    plan_data = get_client_plan(username, ac)

    # Do not save disconnected, unknown, or unavailable results.
    if plan_data["plan"] not in (
        "Disconnected",
        "Unknown plan",
        "Unavailable",
    ):
        if username and ac:
            PPPoEClientPlanMemory.objects.update_or_create(
                username=username,
                ac=ac,
                defaults={
                    "plan_name": plan_data["plan"],
                    "plan_version": plan_data.get("version") or "",
                    "bandwidth_mbps": plan_data.get("bandwidth_mbps") or 0,
                },
            )

        plan_data["last_plan"] = None
        plan_data["last_plan_version"] = None
        plan_data["last_bandwidth_mbps"] = None
        return plan_data

    # Retrieve previously remembered plan for disconnected clients.
    if plan_data["plan"] in ("Disconnected", "Unknown plan") and username and ac:
        remembered = PPPoEClientPlanMemory.objects.filter(
            username=username,
            ac=ac,
        ).first()

        if remembered:
            plan_data["last_plan"] = remembered.plan_name
            plan_data["last_plan_version"] = remembered.plan_version
            plan_data["last_bandwidth_mbps"] = remembered.bandwidth_mbps
        else:
            plan_data["last_plan"] = None
            plan_data["last_plan_version"] = None
            plan_data["last_bandwidth_mbps"] = None

    return plan_data

@login_required
def location_summary_api(request):
    locations = get_location_summary()

    return JsonResponse({
        "locations": locations,
        "total_locations": len(locations),
        "total_clients": sum(item["total"] for item in locations),
        "total_online": sum(item["online"] for item in locations),
        "total_down": sum(item["down"] for item in locations),
    })


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        if "profile_picture" in request.FILES:
            profile.profile_picture = request.FILES["profile_picture"]
            profile.save(update_fields=["profile_picture"])

        return redirect("profile")

    return render(
        request,
        "monitor/profile.html",
        {"profile": profile},
    )

@login_required
def barangay_monitor(request):
    return render(
        request,
        "monitor/barangay_monitor.html"
    )