from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse, Http404
from monitor.models import AccessConcentrator
from monitor.websocket_utils import broadcast_pppoe_event
from django.utils import timezone
from django.conf import settings
import os
from .models import *


RAW_LOG_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "management",
    "raw_logs",
)

def get_raw_log_directory():
    return os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "management",
        "raw_logs",
    )

def dashboard(request):

    query = request.GET.get("q", "").strip()

    acs = AccessConcentrator.objects.filter(
        enabled=True
    )

    ac_data = []

    total_active_users = 0

    for ac in acs:

        active_users = PPPoESession.objects.filter(
            ac=ac,
            active=True
        ).count()

        total_active_users += active_users

        ac_data.append({
            "ac": ac,
            "active_users": active_users,
        })

    events = PPPoEEvent.objects.select_related("ac")

    if query:
        events = events.filter(
            Q(username__icontains=query) |
            Q(mac_address__icontains=query) |
            Q(ip_address__icontains=query)
        )

    recent_events = events.order_by("-timestamp")[:50]

    context = {
        "ac_data": ac_data,
        "total_active_users": total_active_users,
        "recent_events": recent_events,
        "query": query,
    }

    return render(
        request,
        "monitor/dashboard.html",
        context
    )

def client_info(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({
            "found": False,
            "message": "Please enter a username, MAC address, or IP address."
        })

    session = PPPoESession.objects.filter(
        Q(username__iexact=query) |
        Q(mac_address__iexact=query) |
        Q(ip_address__iexact=query)
    ).select_related("ac").order_by("-connected_at").first()

    client = PPPoEClient.objects.filter(
        Q(username__iexact=query) |
        Q(mac_address__iexact=query)
    ).select_related("ac").order_by("-last_seen").first()

    if not session and not client:
        event = PPPoEEvent.objects.filter(
            Q(username__iexact=query) |
            Q(mac_address__iexact=query) |
            Q(ip_address__iexact=query)
        ).select_related("ac").order_by("-timestamp").first()

        if not event:
            return JsonResponse({
                "found": False,
                "message": "Client not found."
            })

        username = event.username
        mac = event.mac_address
        ip = event.ip_address
        active_ac = event.ac
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
            active_ac = client.ac

    # ---------------------------------------------------------
    # LAST LOGIN
    # ---------------------------------------------------------

    login_event = PPPoEEvent.objects.filter(
        username=username,
        event_type=PPPoEEvent.LOGIN
    ).order_by("-timestamp").first()

    # ---------------------------------------------------------
    # LAST LOGOUT
    # ---------------------------------------------------------

    logout_event = PPPoEEvent.objects.filter(
        username=username,
        event_type=PPPoEEvent.LOGOUT
    ).order_by("-timestamp").first()

    # ---------------------------------------------------------
    # UP TIME
    # ---------------------------------------------------------

    connected_at = None

    if session and session.active:
        connected_at = session.connected_at
    elif login_event:
        connected_at = login_event.timestamp

    # ---------------------------------------------------------
    # LAST DOWN TIME
    # ---------------------------------------------------------

    last_down_time = logout_event.timestamp if logout_event else None

    # ---------------------------------------------------------
    # DURATION
    # ---------------------------------------------------------

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

    return JsonResponse({
        "found": True,
        "username": username or "UNKNOWN",
        "mac": mac or "No MAC",
        "ip": ip or "No IP",
        "up_time": connected_at.isoformat() if connected_at else None,
        "last_down_time": last_down_time.isoformat() if last_down_time else None,
        "last_down_ac": logout_event.ac.name if logout_event else None,
        "duration_seconds": duration_seconds,
        "active_ac": active_ac.name if active_ac else None,
    })

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

def raw_logs(request):

    raw_log_dir = get_raw_log_directory()

    print("RAW LOG DIRECTORY:", raw_log_dir)

    ac_logs = []

    acs = AccessConcentrator.objects.filter(
        enabled=True
    ).order_by("id")

    for ac in acs:

        ac_directory = os.path.join(
            raw_log_dir,
            ac.name,
        )

        print("CHECKING:", ac_directory)

        files = []

        if os.path.isdir(ac_directory):

            for filename in os.listdir(ac_directory):

                if not filename.lower().endswith(".txt"):
                    continue

                file_path = os.path.join(
                    ac_directory,
                    filename,
                )

                if os.path.isfile(file_path):

                    files.append({
                        "name": filename,
                        "size": os.path.getsize(file_path),
                    })

        files.sort(
            key=lambda x: x["name"],
            reverse=True,
        )

        ac_logs.append({
            "ac": ac,
            "files": files,
        })

    return render(
        request,
        "monitor/raw_logs.html",
        {
            "ac_logs": ac_logs,
        },
    )


def raw_log_viewer(request, ac_name, filename):

    ac_directory = os.path.join(
        RAW_LOG_DIR,
        ac_name,
    )

    file_path = os.path.join(
        ac_directory,
        filename,
    )

    print("RAW LOG VIEWER:")
    print("AC:", ac_name)
    print("FILE:", filename)
    print("PATH:", file_path)

    if not os.path.isfile(file_path):
        raise Http404("Log file not found.")

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="replace",
        ) as file:

            log_content = file.read()

    except Exception as e:
        raise Http404(f"Unable to read log file: {e}")

    return render(
        request,
        "monitor/raw_log_viewer.html",
        {
            "ac_name": ac_name,
            "filename": filename,
            "log_content": log_content,
        },
    )