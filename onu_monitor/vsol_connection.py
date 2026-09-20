import asyncio
import telnetlib3


class VSOLConnection:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.reader = None
        self.writer = None
    async def connect(self):
        self.reader, self.writer = await telnetlib3.open_connection(
            self.host,
            23
        )
        # Wait for login prompt
        await self.reader.readuntil(b"Login:")
        self.writer.write(self.username + "\r\n")
        # Wait for password prompt
        await self.reader.readuntil(b"Password:")
        self.writer.write(self.password + "\r\n")
        # Give the OLT a moment to finish login
        await asyncio.sleep(1)
        print("VSOL login successful.")

    async def close(self):

        if self.writer:

            print()
            print("==========================================")
            print("Closing VSOL Telnet connection...")

            self.writer.close()

            try:
                await self.writer.wait_closed()
            except Exception:
                pass

            self.writer = None
            self.reader = None

            print("VSOL Telnet connection closed successfully.")
            print("==========================================")
    async def enable(self, enable_password):
        self.writer.write("enable\r\n")
        output = ""
        while "Password:" not in output:
            data = await self.reader.read(1024)
            if not data:
                break
            output += data
        self.writer.write(enable_password + "\r\n")
        await asyncio.sleep(1)
        data = await self.reader.read(4096)
        output += data
        return output
    async def configure_terminal(self):
        self.writer.write("configure terminal\r\n")
        await asyncio.sleep(0.5)
        output = await self.reader.read(4096)
        return output
    async def send_command(self, command):
        self.writer.write(command + "\r\n")
        await asyncio.sleep(1)
        output = ""
        while True:
            data = await self.reader.read(1024)
            if not data:
                break
            output += data
            if "--More--" in output:
                self.writer.write(" ")
                output = output.replace("--More--", "")
                await asyncio.sleep(0.2)
                continue
            cleaned = output.rstrip()
            if cleaned.endswith("#") or cleaned.endswith(">"):
                break
        output = output.replace("\x08", "")
        output = output.replace("\r", "")

        lines = []

        for line in output.splitlines():

            stripped = line.lstrip()

            if stripped.lower().startswith(("gpon", "epon")):
                line = stripped

            lines.append(line)

        output = "\n".join(lines)

        return output