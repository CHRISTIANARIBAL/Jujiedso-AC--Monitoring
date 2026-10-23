
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from librouteros import connect
from monitor.models import AccessConcentrator
from monitor.crypto import decrypt_password


AC_NAME = "calu-ac1 new"
TEST_MESSAGE = "LIVE_LISTENER_TEST"


def main():
    ac = AccessConcentrator.objects.filter(
        enabled=True,
        name=AC_NAME,
    ).first()

    if not ac:
        raise SystemExit(
            f"Enabled AC '{AC_NAME}' was not found."
        )

    api = None

    try:
        api = connect(
            host=ac.ip_address,
            username=ac.username,
            password=decrypt_password(ac.encrypted_password),
            port=8728,
            timeout=300,
        )

        print(f"\nConnected to {ac.name}.")

        # Inspect the current log table.
        print("\nReading current RouterOS log IDs...")

        current_logs = list(api("/log/print"))

        print(f"Current log entries returned: {len(current_logs)}")

        for row in current_logs[:10]:
            print(
                f"ID={row.get('.id')} | "
                f"Time={row.get('time')} | "
                f"Message={row.get('message')}"
            )

        # Look for the harmless test message in the retrieved logs.
        matches = [
            row for row in current_logs
            if row.get("message") == TEST_MESSAGE
        ]

        print(f"\n{TEST_MESSAGE} matches: {len(matches)}")

        for row in matches:
            print(
                f"Test entry ID: {row.get('.id')}\n"
                f"Time: {row.get('time')}\n"
                f"Topics: {row.get('topics')}\n"
                f"Message: {row.get('message')}"
            )

        # Start the live listener.
        print("\nStarting RouterOS /log/listen...")
        print("Incoming records will be displayed below.")
        print("Press Ctrl+C to stop.\n")

        api.protocol.writeSentence("/log/listen")

        while True:
            reply, fields = api.readSentence()

            if reply == "!re":
                if fields.get(".dead"):
                    print(
                        f"REMOVED ID={fields.get('.id')}",
                        flush=True,
                    )
                    continue

                print(
                    f"LIVE ID={fields.get('.id')} | "
                    f"Time={fields.get('time')} | "
                    f"Topics={fields.get('topics')} | "
                    f"Message={fields.get('message')}",
                    flush=True,
                )

            elif reply == "!trap":
                print(
                    f"RouterOS API error: {fields}",
                    flush=True,
                )

            elif reply == "!done":
                print("Listener ended.", flush=True)
                break

            else:
                print(
                    f"API response {reply}: {fields}",
                    flush=True,
                )

    except KeyboardInterrupt:
        print("\nListener test stopped.")

    except Exception as exc:
        print(
            f"Listener test failed: "
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        if api is not None:
            try:
                api.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
