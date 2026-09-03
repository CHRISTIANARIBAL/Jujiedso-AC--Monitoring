import asyncio
import telnetlib3

async def main():
    reader, writer = await telnetlib3.open_connection(
        "10.99.2.11",
        23
    )

    print("Connected!")

    async def recieve():
        while True:
            data = await reader.read(4096)

            if not data:
                break

            print(data, end="", flush=True)

    async def send():
        while True:
            command = await asyncio.to_thread(input)
            writer.write(command + "\r\n")

    await asyncio.gather(
        recieve(),
        send()
    )

asyncio.run(main())