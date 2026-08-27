from django.shortcuts import render, get_object_or_404
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

RAW_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "management",
    "raw_logs",
)

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
    events = PPPoEEvent.objects.select_related("ac")

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
        since = timezone.now() - timedelta(hours=24)
        now = timezone.now()
        events = list( PPPoEEvent.objects.filter( mac_address=mac, event_type__in=[ PPPoEEvent.LOGIN, PPPoEEvent.LOGOUT, ], timestamp__gte=since, ) .select_related("ac") .order_by("timestamp") )
        history = []
        current_login = None

        for event in events:
            if event.event_type == PPPoEEvent.LOGIN:
                current_login = event
            elif event.event_type == PPPoEEvent.LOGOUT:
                if current_login:
                    duration_seconds = int((event.timestamp - current_login.timestamp).total_seconds())
                    if duration_seconds < 0:
                        duration_seconds = 0
                    history.append({
                        "up_time": current_login.timestamp.isoformat(),
                        "down_time": event.timestamp.isoformat(),
                        "up_ac": (current_login.ac.name
                            if current_login.ac
                            else None
                        ),
                        "down_ac": (current_login.ac.name
                            if current_login.ac
                            else None
                        ),
                        "duration_seconds": duration_seconds, "active": False,
                    })
                    current_login = None
        if current_login:
            duration_seconds = int((timezone.now() - current_login.timestamp).total_seconds())

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
        history.sort( key=lambda item: item["up_time"],  reverse=True)
        return history
    if client_id:
        try:
            client = PPPoEClient.objects.select_related("ac").get(id=client_id)
        except PPPoEClient.DoesNotExist:
            return JsonResponse({"found": False, "message": "Client not found."})

        username = client.username
        mac = client.mac_address
        session = PPPoESession.objects.filter(username=username, mac_address=mac, ac=client.ac, active=True).select_related("ac").order_by("-connected_at").first()
        login_event = PPPoEEvent.objects.filter(username=username, mac_address=mac, event_type=PPPoEEvent.LOGIN).order_by("-timestamp").first()
        logout_event = PPPoEEvent.objects.filter(username=username, mac_address=mac, event_type=PPPoEEvent.LOGOUT).order_by("-timestamp").first()
        connected_at = None

        if session and session.connected_at:
            connected_at = session.connected_at

        elif login_event:
            connected_at = login_event.timestamp

        last_down_time = (logout_event.timestamp
            if logout_event
            else None
        )

        duration_seconds = None
        if connected_at:
            if session and session.active:
                end_time = timezone.now()
            elif logout_event:
                end_time = logout_event.timestamp
            else:
                end_time = timezone.now()
            duration_seconds = int((end_time - connected_at).total_seconds())

            if duration_seconds < 0:
                duration_seconds = 0

        connection_history = build_connection_history(username, mac)

        return JsonResponse({
            "found": True,
            "username": username or "UNKNOWN",
            "mac": mac or "No MAC",
            "ip": (session.ip_address
                if session
                else "No IP"
            ),
            "up_time": (connected_at.isoformat()
                if connected_at
                else None
            ),
            "last_down_time": (last_down_time.isoformat()
                if last_down_time
                else None
            ),
            "last_down_ac": ( logout_event.ac.name
                if logout_event
                else client.ac.name
            ),
            "duration_seconds": duration_seconds,

            "active_ac": ( session.ac.name
                if session and session.active
                else None
            ),
            "connection_history": connection_history,
        })

    if not query:
        return JsonResponse({
            "found": False,
            "message": ("Please enter a username, MAC address, " "or IP address.")
        })

    session = PPPoESession.objects.filter(
        Q(username__icontains=query) |
        Q(mac_address__icontains=query) |
        Q(ip_address__icontains=query)
    ).select_related("ac").order_by("-connected_at").first()
    client = PPPoEClient.objects.filter(
        Q(username__icontains=query) |
        Q(mac_address__icontains=query)
    ).select_related("ac").order_by("-last_seen").first()
    if not session and not client:
        event = PPPoEEvent.objects.filter(
            Q(username__icontains=query) |
            Q(mac_address__icontains=query) |
            Q(ip_address__icontains=query)
        ).select_related("ac").order_by("-timestamp").first()
        if not event:
            return JsonResponse({
                "found": False,
                "message": "Client not found."
            })
        username = event.username
        mac = event.mac_address
        ip = event.ip_address
        active_ac = (event.ac
            if event.event_type == PPPoEEvent.LOGIN
            else None
        )
    else:
        if session:
            username = session.username
            mac = session.mac_address
            ip = session.ip_address
            active_ac = (session.ac
                if session.active
                else None
            )
        else:
            username = client.username
            mac = client.mac_address
            ip = None
            active_ac = None

    login_event = PPPoEEvent.objects.filter(username=username,  mac_address=mac, event_type=PPPoEEvent.LOGIN).order_by("-timestamp").first()
    logout_event = PPPoEEvent.objects.filter(username=username, mac_address=mac, event_type=PPPoEEvent.LOGOUT).order_by("-timestamp").first()
    connected_at = None

    if session and session.active:
        connected_at = session.connected_at
    elif login_event:
        connected_at = login_event.timestamp

    last_down_time = (logout_event.timestamp
        if logout_event
        else None
    )

    duration_seconds = None
    if connected_at:
        if session and session.active:
            end_time = timezone.now()
        elif logout_event:
            end_time = logout_event.timestamp
        else:
            end_time = timezone.now()
        duration_seconds = int((end_time - connected_at).total_seconds())
        if duration_seconds < 0:
            duration_seconds = 0
    connection_history = build_connection_history(username, mac)

    return JsonResponse({
        "found": True,
        "username": username or "UNKNOWN",
        "mac": mac or "No MAC",
        "ip": ip or "No IP",
        "up_time": (connected_at.isoformat()
            if connected_at
            else None
        ),

        "last_down_time": (last_down_time.isoformat()
            if last_down_time
            else None
        ),
        "last_down_ac": (logout_event.ac.name
            if logout_event
            else None
        ),
        "duration_seconds": duration_seconds,
        "active_ac": ( active_ac.name
            if active_ac
            else None
        ),
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
    print("RAW LOG DIRECTORY:", raw_log_dir)

    ac_logs = []
    acs = AccessConcentrator.objects.filter(enabled=True).order_by("id")

    for ac in acs:
        ac_directory = os.path.join(raw_log_dir, ac.name)
        print("CHECKING:", ac_directory)

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
    print("RAW LOG VIEWER:")
    print("AC:", ac_name)
    print("FILE:", filename)
    print("PATH:", file_path)

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

    clients = PPPoEClient.objects.filter(Q(username__icontains=query) | Q(mac_address__icontains=query)).select_related("ac")
    results = []
    seen_clients = set()

    for client in clients:
        active_session = PPPoESession.objects.filter(username=client.username, mac_address=client.mac_address, active=True).select_related("ac").order_by("-connected_at").first()
        if active_session:
            ac = active_session.ac
            active = True
        else:
            ac = client.ac
            active = False
        client_key = (client.username.lower(), (client.mac_address or "").lower())

        if client_key in seen_clients:
            continue
        seen_clients.add(client_key)

        results.append({
            "id": client.id,
            "username": client.username,
            "mac": client.mac_address,
            "ac": ac.name if ac else None,
            "active": active,
        })

    active_sessions = PPPoESession.objects.filter(
        Q(username__icontains=query) |
        Q(mac_address__icontains=query),
        active=True
    ).select_related("ac").order_by("-connected_at")

    for session in active_sessions:
        client_key = (session.username.lower(), (session.mac_address or "").lower())

        if client_key in seen_clients:
            continue

        seen_clients.add(client_key)

        results.append({
            "id": session.id,
            "username": session.username,
            "mac": session.mac_address,
            "ac": session.ac.name if session.ac else None,
            "active": True,
        })

    results.sort(key=lambda x: (not x["active"], (x["username"] or "").lower()))

    return JsonResponse({
        "found": bool(results),
        "results": results,
        "message": (
            "Clients found."
            if results
            else "Client not found."
        )
    })