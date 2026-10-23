import os
import time
import hashlib
import threading
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from librouteros import connect
from monitor.models import *
from monitor.session_sync import sync_ac_sessions
from monitor.log_collector import build_active_lookup, process_logs
from monitor.live_log_listener import start_listener_thread
from monitor.live_log_state import update_active_lookup
from monitor.websocket_utils import (broadcast_active_counts, broadcast_location_summary)
from monitor.location_detection import get_location_summary
from monitor.crypto import decrypt_password

logger = logging.getLogger(__name__)
RAW_LOG_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),"raw_logs",
)

def get_raw_log_directory(ac):
    ac_directory = os.path.join(RAW_LOG_DIR, ac.name)
    os.makedirs(ac_directory, exist_ok=True)
    return ac_directory

def get_daily_raw_log_file(ac):
    ac_directory = get_raw_log_directory(ac)
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(ac_directory, f"{today}.txt")

def format_raw_mikrotik_log(log):
    log_time = log.get("time", "")
    topics = log.get("topics", "")
    message = log.get("message", "")
    return (f"{log_time} | " f"{topics} | " f"{message}"
    ).strip()

def raw_log_hash(raw_line):
    return hashlib.sha256(
        raw_line.encode("utf-8", errors="ignore")
    ).hexdigest()

def read_last_raw_lines(file_path, max_lines=1000):
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, "rb") as file:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            if file_size == 0:
                return set()
            
            block_size = 8192
            blocks = []
            while file_size > 0 and len(b"".join(blocks).splitlines()) <= max_lines:
                read_size = min(block_size, file_size)
                file_size -= read_size
                file.seek(file_size)
                blocks.append(file.read(read_size))

                if file_size == 0:
                    break

            data = b"".join(reversed(blocks))
            lines = data.splitlines()
            lines = lines[-max_lines:]

            return {
                hashlib.sha256(line.decode("utf-8",errors="ignore").encode("utf-8")).hexdigest()
                for line in lines
            }
    except Exception:
        return set()

def save_new_raw_logs(ac, logs):
    file_path = get_daily_raw_log_file(ac)
    existing_hashes = read_last_raw_lines(file_path, max_lines=1000)
    new_lines = []
    for log in logs:
        raw_line = format_raw_mikrotik_log(log)
        if not raw_line:
            continue

        line_hash = raw_log_hash(raw_line)
        if line_hash in existing_hashes:
            continue

        new_lines.append(raw_line)
        existing_hashes.add(line_hash)
    if not new_lines:
        return 0

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as file:
        for line in new_lines:
            file.write(line + "\n")
    return len(new_lines)

RETENTION_DAYS = 7
TRAFFIC_RETENTION_DAYS = 15
CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60


def cleanup_old_raw_logs(retention_days=RETENTION_DAYS):
    """Delete dated raw log files outside the current seven-calendar-day window."""
    if not os.path.isdir(RAW_LOG_DIR):
        return 0

    # Keep today and the previous six calendar dates (seven dates total).
    cutoff_date = timezone.localdate() - timedelta(days=retention_days - 1)
    deleted_count = 0

    for ac_name in os.listdir(RAW_LOG_DIR):
        ac_directory = os.path.join(RAW_LOG_DIR, ac_name)
        if not os.path.isdir(ac_directory):
            continue

        for filename in os.listdir(ac_directory):
            if not filename.lower().endswith(".txt"):
                continue

            # Only delete files matching the collector's YYYY-MM-DD.txt format.
            try:
                log_date = datetime.strptime(filename, "%Y-%m-%d.txt").date()
            except ValueError:
                continue

            if log_date < cutoff_date:
                file_path = os.path.join(ac_directory, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except FileNotFoundError:
                    # Another process may have removed the file already.
                    continue

    return deleted_count


def cleanup_old_history(
    retention_days=RETENTION_DAYS,
    traffic_retention_days=TRAFFIC_RETENTION_DAYS,
):
    """Keep raw logs/events for 7 days and traffic history for 15 days."""
    deleted_raw_files = cleanup_old_raw_logs(retention_days)
    event_cutoff = timezone.now() - timedelta(days=retention_days)
    traffic_cutoff = timezone.now() - timedelta(days=traffic_retention_days)

    deleted_events, _ = PPPoEEvent.objects.filter(
        timestamp__lt=event_cutoff
    ).delete()
    deleted_traffic, _ = PPPoETrafficHistory.objects.filter(
        timestamp__lt=traffic_cutoff
    ).delete()

    return deleted_events, deleted_traffic, deleted_raw_files


class Command(BaseCommand):
    help = "Monitor active PPPoE sessions and MikroTik logs"
    def handle(self, *args, **options):
        print(
            "MONITOR PID:", os.getpid(),
            "PARENT:", os.getppid(),
            "DJANGO_AUTORELOAD_ENV:",
            os.environ.get("DJANGO_AUTORELOAD_ENV"),
        )
        # self.stdout.write(self.style.SUCCESS("PPPoE monitoring started..."))
        connections = {}
        last_cleanup = None
        listener_stop_event = threading.Event()
        listener_threads = {}

        while True:
            # Run immediately at startup, then approximately once every 24 hours.
            now_monotonic = time.monotonic()
            if (
                last_cleanup is None
                or now_monotonic - last_cleanup >= CLEANUP_INTERVAL_SECONDS
            ):
                try:
                    deleted_events, deleted_traffic, deleted_raw_files = cleanup_old_history()
                    # self.stdout.write(self.style.SUCCESS(
                    #     "Retention cleanup completed: "
                    #     f"{deleted_events} old events, "
                    #     f"{deleted_traffic} old traffic samples, "
                    #     f"{deleted_raw_files} old raw log files deleted."
                    # ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Retention cleanup failed: {e}"
                    ))
                finally:
                    last_cleanup = time.monotonic()

            active_counts = {}
            acs = AccessConcentrator.objects.filter(enabled=True)


            for ac in acs:
                try:
                    # Start one live log listener for each enabled AC.
                    listener_thread = listener_threads.get(ac.id)

                    if listener_thread is None or not listener_thread.is_alive():
                        listener_threads[ac.id] = start_listener_thread(
                            ac.id,
                            listener_stop_event,
                        )
                        # self.stdout.write(
                        #     self.style.SUCCESS(
                        #         f"{ac.name}: live log listener started"
                        #     )
                        # )

                    api = connections.get(ac.id)

                    if api is None:
                        # self.stdout.write(f"\nConnecting to {ac.name}...")
                        password = decrypt_password(ac.encrypted_password)
                        api = connect(username=ac.username, password=password, host=ac.ip_address, port=8728)
                        connections[ac.id] = api

                        # self.stdout.write(self.style.SUCCESS(f"{ac.name}: connected"))
                    else:
                        self.stdout.write(f"\nCollecting {ac.name}...")

                    active_users = list(api("/ppp/active/print"))
                    active_count = sync_ac_sessions(ac, mikrotik_sessions=active_users, api=api,)
                    active_counts[str(ac.id)] = active_count

                    active_lookup = build_active_lookup(active_users)
                    update_active_lookup(ac.id, active_lookup)
                    logs = list(api("/log/print"))
                    saved_count = save_new_raw_logs(ac, logs)

                    traffic_saved = collect_pppoe_traffic(api, ac, active_users,)
                    # self.stdout.write(self.style.SUCCESS(f"{ac.name}: "f"{traffic_saved} traffic samples saved"))

                    if saved_count > 0:
                        self.stdout.write(self.style.SUCCESS(
                            f"{ac.name}: "
                            f"saving {saved_count} "
                            f"new raw data..."
                            )
                        )

                    new_events = process_logs(ac, logs, active_lookup)
                    self.stdout.write(self.style.SUCCESS(
                            f"{ac.name}: "
                            f"{active_count} active users, "
                            f"{new_events} new events"
                            )
                        )

                except Exception as e:

                    self.stdout.write(self.style.ERROR(
                        f"{ac.name}: {e}"
                        )
                    )

                    if ac.id in connections:
                        try:
                            connections[ac.id].close()
                        except Exception:
                            pass

                        del connections[ac.id]
                        self.stdout.write(self.style.WARNING(
                                f"{ac.name}: connection lost, "
                                f"will reconnect..."
                                )
                            )

            broadcast_active_counts(active_counts)
            try:
                locations = get_location_summary()

                # Convert the summary to JSON-safe primitive values.
                broadcast_location_summary(locations)

                # self.stdout.write(self.style.SUCCESS(
                #     f"Broadcast location summary: {len(locations)} locations"
                # ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Location summary broadcast failed: {e}"
                ))

            self.stdout.write("\nWaiting 30 seconds...")
            time.sleep(30)

def collect_pppoe_traffic(api, ac, active_users):
    saved_count = 0

    for session in active_users:
        username = session.get("name")

        if not username:
            continue

        interface_name = f"<pppoe-{username}>"

        try:
            traffic = list(
                api(
                    "/interface/monitor-traffic",
                    **{
                        "interface": interface_name,
                        "once": "yes",
                    },
                )
            )

            if not traffic:
                continue

            data = traffic[0]

            client = PPPoEClient.objects.filter(
                username=username,
                ac=ac,
            ).first()

            if not client:
                continue

            PPPoETrafficHistory.objects.create(
                client=client,
                ac=ac,
                interface_name=interface_name,
                tx_bits_per_second=data.get(
                    "tx-bits-per-second", 0
                ),
                rx_bits_per_second=data.get(
                    "rx-bits-per-second", 0
                ),
                tx_packets_per_second=data.get(
                    "tx-packets-per-second", 0
                ),
                rx_packets_per_second=data.get(
                    "rx-packets-per-second", 0
                ),
                fp_tx_bits_per_second=data.get(
                    "fp-tx-bits-per-second", 0
                ),
                fp_rx_bits_per_second=data.get(
                    "fp-rx-bits-per-second", 0
                ),
                fp_tx_packets_per_second=data.get(
                    "fp-tx-packets-per-second", 0
                ),
                fp_rx_packets_per_second=data.get(
                    "fp-rx-packets-per-second", 0
                ),
                tx_drops_per_second=data.get(
                    "tx-drops-per-second", 0
                ),
                rx_drops_per_second=data.get(
                    "rx-drops-per-second", 0
                ),
                tx_queue_drops_per_second=data.get(
                    "tx-queue-drops-per-second", 0
                ),
                tx_errors_per_second=data.get(
                    "tx-errors-per-second", 0
                ),
                rx_errors_per_second=data.get(
                    "rx-errors-per-second", 0
                ),
            )

            saved_count += 1

        except Exception:
            logger.exception(
                "%s: traffic collection failed for %s",
                ac.name,
                username,
            )

    return saved_count