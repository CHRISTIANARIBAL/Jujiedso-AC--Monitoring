import time

from django.core.management.base import BaseCommand
from librouteros import connect

from monitor.models import AccessConcentrator
from monitor.session_sync import sync_ac_sessions
from monitor.log_collector import build_active_lookup, process_logs
from monitor.websocket_utils import broadcast_active_counts

class Command(BaseCommand):
    help = "Monitor active PPPoE sessions and MikroTik logs"
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "PPPoE monitoring started..."
            )
        )
        while True:
            active_counts = {}
            acs = AccessConcentrator.objects.filter(
                enabled=True
            )
            for ac in acs:
                try:
                    self.stdout.write(
                        f"\nCollecting {ac.name}..."
                    )
                    # -------------------------------------------------
                    # ONE API CONNECTION
                    # -------------------------------------------------
                    api = connect(
                        username=ac.username,
                        password=ac.password,
                        host=ac.ip_address,
                        port=8728,
                    )
                    # -------------------------------------------------
                    # GET ACTIVE PPPoE USERS
                    # -------------------------------------------------
                    active_users = list(
                        api("/ppp/active/print")
                    )
                    # -------------------------------------------------
                    # SYNC CURRENT SESSIONS
                    # -------------------------------------------------
                    active_count = sync_ac_sessions(
                        ac,
                        mikrotik_sessions=active_users,
                    )
                    active_counts[ac.id] = active_count
                    # -------------------------------------------------
                    # BUILD MAC → USER LOOKUP
                    # -------------------------------------------------
                    active_lookup = build_active_lookup(
                        active_users
                    )
                    # -------------------------------------------------
                    # GET MIKROTIK LOGS
                    # -------------------------------------------------
                    logs = list(
                        api("/log/print")
                    )
                    # -------------------------------------------------
                    # PROCESS NEW PPPoE EVENTS
                    # -------------------------------------------------
                    new_events = process_logs(
                        ac,
                        logs,
                        active_lookup,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{ac.name}: "
                            f"{active_count} active users, "
                            f"{new_events} new events"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"{ac.name}: {e}"
                        )
                    )
            broadcast_active_counts(active_counts)
            self.stdout.write(
                "\nWaiting 30 seconds..."
            )
            time.sleep(30)