import asyncio
import telnetlib3

class BDCOMConnection:

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.reader = None
        self.writer = None

    async def connect(self):

        print(f"Connecting to BDCOM: {self.host}")

        self.reader, self.writer = await telnetlib3.open_connection(
            self.host,
            23,
            cols=200,
            rows=50
        )

        print("TCP/Telnet connection established.")

        await asyncio.sleep(1)
        data = await self.reader.read(4096)

        print()
        print("==========================================")
        print("Sending username...")

        self.writer.write(self.username + "\r\n")
        await asyncio.sleep(0.5)
        data = await self.reader.read(4096)

        print()
        print("Sending password...")

        self.writer.write(self.password + "\r\n")

        data = ""
        while True:
            chunk = await self.reader.read(1024)
            if not chunk:
                break
            data += chunk
            if "#" in data or ">" in data or "Authentication failed" in data:
                break

        print()
        print("====================================")

        if "Authentication failed" in data:
            print()
            print("BDCOM authentication failed.")
            return False

        if ">" in data:
            print()
            print("BDCOM logged in user mode.")
            print()
            print("Entering enable mode...")

            self.writer.write("enable\r\n")
            await asyncio.sleep(0.5)
            enable_output = await self.reader.read(4096)
            print()
            print("==================================")

            if "Password:" in enable_output:
                print()
                print("Sending enable password...")
                self.writer.write(self.password + "\r\n")
                await asyncio.sleep(0.5)
                enable_output = await self.reader.read(4096)
                print()
                print("===========================================")

            if "#" in enable_output:
                print()
                print("BDCOM login successful.")

                print("Setting terminal width to 256...")

                self.writer.write("terminal width 256\r\n")
                await asyncio.sleep(0.5)
                await self.reader.read(4096)

                print("Terminal width set to 256.")

                return True
            
            print()
            print("Could not enter BDCOM enable mode.")
            return False

        if "#" in data:
            print()
            print("BDCOM login successful.")
            return True

        print()
        print("BDCOM login status could not be determined.")
        return False

    async def send_command(self, command):
        print()
        print(f"Executing: {command}")

        self.writer.write(command + "\r\n")

        output = ""

        while True:

            data = await self.reader.read(1024)

            if not data:
                break

            output += data

            if "--More--" in output:
                print()
                self.writer.write(" ")
                output = output.replace("--More--", "")
                continue

            cleaned = output.rstrip()

            if cleaned.endswith(">") or cleaned.endswith("#"):
                print()
                break

        return output.replace("\x08", "").replace("\r", "")

    async def close(self):

        if self.writer:

            print()
            print("==========================================")
            print("Closing BDCOM Telnet connection...")

            self.writer.close()

            try:
                await self.writer.wait_closed()
            except Exception:
                pass

            self.writer = None
            self.reader = None

            print("BDCOM Telnet connection closed successfully.")
            print("==========================================")