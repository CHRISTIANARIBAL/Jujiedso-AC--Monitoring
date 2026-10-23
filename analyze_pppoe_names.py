
import re
from collections import defaultdict
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from monitor.models import PPPoEClient

usernames = (
    PPPoEClient.objects
    .values_list("username", flat=True)
    .distinct()
)

pattern = re.compile(r"^([a-zA-Z-]+)(\d{2})(.+)$")

groups = defaultdict(list)
unmatched = []

for raw_username in usernames.iterator():
    username = (raw_username or "").strip().lower()

    if not username:
        continue

    match = pattern.fullmatch(username)

    if match:
        location, nap, customer = match.groups()
        groups[location].append((username, nap))
    else:
        unmatched.append(username)

print("\n" + "=" * 60)
print("PROPOSED LOCATION PREFIXES")
print("=" * 60)
print("Candidate prefixes:", len(groups))

for location, records in sorted(
    groups.items(), key=lambda item: (-len(item[1]), item[0])
):
    naps = sorted({nap for _, nap in records})
    samples = ", ".join(username for username, _ in records[:3])

    print(f"\n{location}")
    print(f"  Accounts: {len(records)}")
    print(f"  NAP numbers: {', '.join(naps)}")
    print(f"  Samples: {samples}")

print("\n" + "=" * 60)
print("UNMATCHED USERNAMES:", len(unmatched))
print("=" * 60)

for username in unmatched[:30]:
    print(" ", username)

if len(unmatched) > 30:
    print(" ... and", len(unmatched) - 30, "more")
