
import os
import sys
import subprocess

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start Django server and PPPoE monitor"

    def handle(self, *args, **options):
        print("DEVSERVER PID:", os.getpid())
        print("PARENT PID:", os.getppid())
        print(
            "DJANGO_AUTORELOAD_ENV:",
            os.environ.get("DJANGO_AUTORELOAD_ENV"),
        )
        print("RUN_MAIN:", os.environ.get("RUN_MAIN"))
        monitor_process = None

        try:
            monitor_process = subprocess.Popen([
                sys.executable,
                "manage.py",
                "monitor_pppoe",
            ])

            subprocess.run([
                sys.executable,
                "manage.py",
                "runserver",
                "0.0.0.0:8000",
                "--noreload",
            ], check=False)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\nStopping...")
            )

        finally:
            if monitor_process and monitor_process.poll() is None:
                self.stdout.write(
                    self.style.WARNING("Stopping PPPoE monitor...")
                )
                monitor_process.terminate()

                try:
                    monitor_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    monitor_process.kill()
                    monitor_process.wait()
