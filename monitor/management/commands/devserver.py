import os
import sys
import subprocess

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start Django development server and PPPoE monitor"

    def handle(self, *args, **options):
        monitor_process = None

        try:
            self.stdout.write(
                self.style.SUCCESS(
                    "Starting PPPoE monitor..."
                )
            )

            monitor_process = subprocess.Popen(
                [
                    sys.executable,
                    "manage.py",
                    "monitor_pppoe",
                ]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "PPPoE monitor started."
                )
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Starting Django server..."
                )
            )

            os.system(
                f'"{sys.executable}" manage.py runserver 0.0.0.0:8000'
            )

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING(
                    "\nStopping..."
                )
            )

        finally:
            if monitor_process:
                self.stdout.write(
                    self.style.WARNING(
                        "Stopping PPPoE monitor..."
                    )
                )

                monitor_process.terminate()

                try:
                    monitor_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    monitor_process.kill()