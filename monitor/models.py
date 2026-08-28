from django.db import models

class AccessConcentrator(models.Model):
    name = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255, null=True, blank=True)
    encrypted_password = models.TextField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PPPoESession(models.Model):
    username = models.CharField(max_length=100)
    ac = models.ForeignKey(AccessConcentrator, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=50, null=True, blank=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class PPPoEEvent(models.Model):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CONNECTION = "CONNECTED"
    AUTH_FAILURE = "AUTH_FAILURE"
    OTHER = "OTHER"

    EVENT_TYPES = [
        (LOGIN, "Login"),
        (LOGOUT, "Logout"),
        (CONNECTION, "Connection"),
        (AUTH_FAILURE, "Authentication Failure"),
        (OTHER, "Other"),
    ]
    username = models.CharField(max_length=100, null=True, blank=True)
    ac = models.ForeignKey(AccessConcentrator, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=50, null=True, blank=True)
    raw_message = models.TextField(null=True, blank=True)
    log_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return (
            f"{self.ac.name} - "
            f"{self.username or 'UNKNOWN'} - "
            f"{self.event_type}"
        )

class PPPoEClient(models.Model):
    username = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=50)
    ac = models.ForeignKey(AccessConcentrator, on_delete=models.CASCADE)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.mac_address}"

# class PPPoETrafficHistory(models.Model):
#     client = models.ForeignKey(
#         PPPoEClient,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="traffic_history",
#     )

#     ac = models.ForeignKey(
#         AccessConcentrator,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="pppoe_traffic_history",
#     )

#     interface_name = models.CharField(max_length=255)

#     timestamp = models.DateTimeField(auto_now_add=True)

#     # Traffic rate
#     tx_bits_per_second = models.BigIntegerField(default=0)
#     rx_bits_per_second = models.BigIntegerField(default=0)

#     # Packet rate
#     tx_packets_per_second = models.BigIntegerField(default=0)
#     rx_packets_per_second = models.BigIntegerField(default=0)

#     # FastPath traffic
#     fp_tx_bits_per_second = models.BigIntegerField(default=0)
#     fp_rx_bits_per_second = models.BigIntegerField(default=0)

#     fp_tx_packets_per_second = models.BigIntegerField(default=0)
#     fp_rx_packets_per_second = models.BigIntegerField(default=0)

#     # Drops
#     tx_drops_per_second = models.BigIntegerField(default=0)
#     rx_drops_per_second = models.BigIntegerField(default=0)
#     tx_queue_drops_per_second = models.BigIntegerField(default=0)

#     # Errors
#     tx_errors_per_second = models.BigIntegerField(default=0)
#     rx_errors_per_second = models.BigIntegerField(default=0)

#     class Meta:
#         ordering = ["timestamp"]

#     def __str__(self):
#         return f"{self.interface_name} - {self.timestamp}"