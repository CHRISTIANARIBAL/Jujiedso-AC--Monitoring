from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_pppoe_event(event):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "pppoe_monitor",
        {
            "type": "pppoe_event",
            "message": event,
        },
    )

def broadcast_active_counts(counts):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "pppoe_monitor",
        {
            "type": "active_counts",
            "counts": counts,
        },
    )