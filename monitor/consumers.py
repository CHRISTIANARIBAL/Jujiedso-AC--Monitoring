from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("pppoe_monitor", self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection",
            "message": "PPPoE Monitor WebSocket connected",
            })
        )
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "pppoe_monitor",
            self.channel_name,
        )

    async def pppoe_event(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def active_counts(self, event):

        await self.send(text_data=json.dumps({
            "type": "active_counts",
            "counts": event["counts"],
            })
        )


    async def location_summary(self, event):
        await self.send(text_data=json.dumps({
            "type": "location_summary",
            "locations": event["locations"],
        }))
