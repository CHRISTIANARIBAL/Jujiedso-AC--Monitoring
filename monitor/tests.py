from librouteros import connect
import time

api = connect(
    username="christian",
    password="chr1st14n",
    host="43.228.106.2",
    port=8728,
)

print("API LOGIN OK")
print("Connection is being kept alive.")
print("Press CTRL+C to disconnect.")

try:
    while True:
        list(api("/system/resource/print"))
        print("API connection still alive...")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nStopped by user.")