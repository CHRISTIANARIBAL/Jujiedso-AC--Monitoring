# from django.core.management.base import BaseCommand

# from monitor.realtime import broadcast_pppoe_event


# class Command(BaseCommand):

#     help = "Test PPPoE WebSocket broadcast"

#     def handle(self, *args, **options):

#         broadcast_pppoe_event(
#             {
#                 "ac": "AC1",
#                 "username": "testuser",
#                 "event_type": "LOGIN",
#                 "ip_address": "10.0.0.100",
#                 "mac_address": "AA:BB:CC:DD:EE:FF",
#                 "timestamp": "2026-08-14 14:00:00",
#             }
#         )

#         self.stdout.write(
#             self.style.SUCCESS(
#                 "Test WebSocket event sent."
#             )
#         )