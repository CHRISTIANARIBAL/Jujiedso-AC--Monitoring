import os
import time
import hashlib
from datetime import datetime
from django.core.management.base import BaseCommand
from librouteros import connect
from monitor.models import AccessConcentrator
from monitor.session_sync import sync_ac_sessions
from monitor.log_collector import build_active_lookup, process_logs
from monitor.websocket_utils import broadcast_active_counts
from monitor.crypto import decrypt_password
# ============================================================
# RAW LOG SETTINGS
# ============================================================

RAW_LOG_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    "raw_logs",
)

# ============================================================
# RAW LOG HELPERS
# ============================================================

def get_raw_log_directory(ac):
    ac_directory = os.path.join(
        RAW_LOG_DIR,
        ac.name,
    )

    os.makedirs(
        ac_directory,
        exist_ok=True,
    )

    return ac_directory


def get_daily_raw_log_file(ac):
    """
    Return today's raw log file.

    Example:

        raw_logs/
            calu-ac1 new/
                2026-08-18.txt
    """

    ac_directory = get_raw_log_directory(ac)

    today = datetime.now().strftime("%Y-%m-%d")

    return os.path.join(
        ac_directory,
        f"{today}.txt",
    )


def format_raw_mikrotik_log(log):
    """
    Convert the MikroTik /log/print API result
    into a readable raw-log line.

    Example:

        2026-08-17 14:11:35 | memory | pppoe, info | PPPoE connection established from 70:28:0A:68:DA:1B
    """

    log_time = log.get("time", "")
    topics = log.get("topics", "")
    message = log.get("message", "")

    return (
        f"{log_time} | "
        f"{topics} | "
        f"{message}"
    ).strip()


def raw_log_hash(raw_line):
    """
    Generate a unique hash for a raw log line.

    This is used only for detecting duplicates
    between polling cycles.
    """

    return hashlib.sha256(
        raw_line.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()


def read_last_raw_lines(file_path, max_lines=1000):
    """
    Read only the last N lines of the local raw log file.

    We don't need to read the entire file.

    This is important because the file can eventually
    contain hundreds of thousands of lines.
    """

    if not os.path.exists(file_path):
        return set()

    try:

        with open(
            file_path,
            "rb",
        ) as file:

            file.seek(
                0,
                os.SEEK_END,
            )

            file_size = file.tell()

            if file_size == 0:
                return set()

            block_size = 8192

            blocks = []

            while file_size > 0 and len(
                b"".join(blocks).splitlines()
            ) <= max_lines:

                read_size = min(
                    block_size,
                    file_size,
                )

                file_size -= read_size

                file.seek(
                    file_size,
                )

                blocks.append(
                    file.read(read_size)
                )

                if file_size == 0:
                    break

            data = b"".join(
                reversed(blocks)
            )

            lines = data.splitlines()

            lines = lines[-max_lines:]

            return {
                hashlib.sha256(
                    line.decode(
                        "utf-8",
                        errors="ignore",
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()
                for line in lines
            }

    except Exception:
        return set()

def save_new_raw_logs(ac, logs):
    file_path = get_daily_raw_log_file(ac)

    existing_hashes = read_last_raw_lines(
        file_path,
        max_lines=1000,
    )

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

    os.makedirs(
        os.path.dirname(file_path),
        exist_ok=True,
    )

    with open(
        file_path,
        "a",
        encoding="utf-8",
    ) as file:
        for line in new_lines:
            file.write(line + "\n")

    return len(new_lines)


class Command(BaseCommand):
    help = "Monitor active PPPoE sessions and MikroTik logs"

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.SUCCESS(
                "PPPoE monitoring started..."
            )
        )

        # ========================================================
        # KEEP MIKROTIK CONNECTIONS ALIVE
        # ========================================================

        connections = {}

        while True:

            active_counts = {}

            acs = AccessConcentrator.objects.filter(
                enabled=True
            )

            for ac in acs:

                try:

                    # ====================================================
                    # CONNECT ONLY IF WE DON'T ALREADY HAVE A CONNECTION
                    # ====================================================

                    api = connections.get(ac.id)

                    if api is None:

                        self.stdout.write(
                            f"\nConnecting to {ac.name}..."
                        )

                        password = decrypt_password(ac.encrypted_password)

                        api = connect(
                            username=ac.username,
                            password=password,
                            host=ac.ip_address,
                            port=8728,
                        )

                        connections[ac.id] = api

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"{ac.name}: connected"
                            )
                        )

                    else:

                        self.stdout.write(
                            f"\nCollecting {ac.name}..."
                        )

                    # ====================================================
                    # PPPoE ACTIVE USERS
                    # ====================================================

                    active_users = list(
                        api("/ppp/active/print")
                    )

                    active_count = sync_ac_sessions(
                        ac,
                        mikrotik_sessions=active_users,
                    )

                    active_counts[str(ac.id)] = active_count

                    # ====================================================
                    # BUILD ACTIVE USER LOOKUP
                    # ====================================================

                    active_lookup = build_active_lookup(
                        active_users
                    )

                    # ====================================================
                    # MIKROTIK RAW LOGS
                    # ====================================================

                    logs = list(
                        api("/log/print")
                    )

                    # ====================================================
                    # SAVE NEW RAW LOGS
                    # ====================================================

                    saved_count = save_new_raw_logs(
                        ac,
                        logs,
                    )

                    if saved_count > 0:

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"{ac.name}: "
                                f"saving {saved_count} "
                                f"new raw data..."
                            )
                        )

                    # ====================================================
                    # PROCESS PPPoE EVENTS
                    # ====================================================

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

                    # ====================================================
                    # CONNECTION FAILED
                    #
                    # Remove the old connection so that on the NEXT
                    # polling cycle we automatically reconnect.
                    # ====================================================

                    if ac.id in connections:

                        try:
                            connections[ac.id].close()
                        except Exception:
                            pass

                        del connections[ac.id]

                        self.stdout.write(
                            self.style.WARNING(
                                f"{ac.name}: connection lost, "
                                f"will reconnect..."
                            )
                        )

            # ========================================================
            # BROADCAST ACTIVE COUNTS TO WEBSOCKET
            # ========================================================

            broadcast_active_counts(
                active_counts
            )

            # ========================================================
            # WAIT 30 SECONDS
            # ========================================================

            self.stdout.write(
                "\nWaiting 30 seconds..."
            )

            time.sleep(30)