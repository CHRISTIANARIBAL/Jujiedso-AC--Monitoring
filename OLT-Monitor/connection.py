import asyncio
import telnetlib3

class TelnetConnection:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await telnetlib3.open_connection(
            self.host,
            self.port
        )

        print(f"Connected to {self.host}")

    async def send_command(self, command):
        self.writer.write(command + "\r\n")
        output = await self.reader.read(4096)

        return output

    async def close(self):
        if self.writer:
            self.writer.close()

            try:
                await self.writer.wait_closed()
            except Exception:
                pass

            self.writer = None
            self.reader = None