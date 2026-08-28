from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WS: CONNECT START")

        await self.channel_layer.group_add("pppoe_monitor", self.channel_name)

        print("WS: GROUP ADDED")
        print("WS: CHANNEL:", self.channel_name)

        await self.accept()

        print("WS: ACCEPTED")

        await self.send(text_data=json.dumps({
            "type": "connection",
            "message": "PPPoE Monitor WebSocket connected",
            })
        )
        print("WS: MESSAGE SENT")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "pppoe_monitor",
            self.channel_name,
        )
        print("WS: DISCONNECT", close_code)

    async def pppoe_event(self, event):
        print("WS: BROADCAST RECEIVED")
        print("WS: EVENT:", event)
        await self.send(text_data=json.dumps(event["message"]))

    async def active_counts(self, event):
        print("WS: ACTIVE COUNTS RECEIVED")
        print(f"WS: COUNTS: {event['counts']}")

        await self.send(text_data=json.dumps({
            "type": "active_counts",
            "counts": event["counts"],
            })
        )