
import logging
import threading
import time

from django.db import close_old_connections

from librouteros import connect

from monitor.crypto import decrypt_password
from monitor.log_collector import process_logs
from monitor.live_log_state import get_active_lookup
from monitor.models import AccessConcentrator

logger = logging.getLogger(__name__)

RECONNECT_DELAY_SECONDS = 5


def listen_to_ac(ac_id, stop_event):
    """
    Listen for live RouterOS log updates on a dedicated API connection.
    Does not replace the regular session/traffic polling connection.
    """
    while not stop_event.is_set():
        api = None

        try:
            close_old_connections()

            ac = AccessConcentrator.objects.get(
                id=ac_id,
                enabled=True,
            )

            api = connect(
                host=ac.ip_address,
                username=ac.username,
                password=decrypt_password(ac.encrypted_password),
                port=8728,
                timeout=300,
            )

            logger.info("Live log listener connected: %s", ac.name)

            # Request a continuous stream of log changes.
                        
            # Capture existing log IDs before starting the live stream.
            # RouterOS may send these existing entries when /log/listen starts.
            existing_ids = {
                row.get(".id")
                for row in api("/log/print")
                if row.get(".id")
            }

            logger.info(
                "%s: captured %d existing log IDs before starting live listener",
                ac.name,
                len(existing_ids),
            )

            api.protocol.writeSentence("/log/listen")


            while not stop_event.is_set():

                reply, fields = api.readSentence()

                if reply == "!re":
                    # Ignore RouterOS removal notifications.
                    if fields.get(".dead"):
                        continue
                    log_id = fields.get(".id")

                    # Ignore entries that existed before the listener started.
                    if log_id and log_id in existing_ids:
                        continue

                    # Require an ID so historical records can be filtered safely.
                    if not log_id:
                        logger.warning(
                            "%s: ignoring live log record without an ID: %s",
                            ac.name,
                            fields,
                        )
                        continue

                    if not all(fields.get(key) for key in ("time", "topics", "message")):
                        continue

                    close_old_connections()
                    active_lookup = get_active_lookup(ac.id)
                    process_logs(ac, [fields], active_lookup)

                elif reply == "!trap":
                    logger.warning(
                        "%s: RouterOS listener trap: %s",
                        ac.name,
                        fields,
                    )

                elif reply == "!done":
                    logger.warning(
                        "%s: RouterOS listener ended.",
                        ac.name,
                    )
                    break


        except Exception:
            if not stop_event.is_set():
                logger.exception(
                    "Live log listener failed for AC ID %s",
                    ac_id,
                )

        finally:
            if api is not None:
                try:
                    api.close()
                except Exception:
                    pass

            close_old_connections()

        if not stop_event.is_set():
            stop_event.wait(RECONNECT_DELAY_SECONDS)


def start_listener_thread(ac_id, stop_event):
    thread = threading.Thread(
        target=listen_to_ac,
        args=(ac_id, stop_event),
        name=f"routeros-log-listener-{ac_id}",
        daemon=True,
    )
    thread.start()
    return thread
