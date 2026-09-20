import re

def normalize_mac(mac):
    mac = mac.replace(":", "")
    mac = mac.replace(".", "")
    mac = mac.replace("-", "")
    mac = mac.replace(" ", "")

    mac = mac.lower()

    if not re.fullmatch(r"[0-9a-f]{12}", mac):
        raise ValueError(f"Invalid MAC address: {mac}")
    return mac

def format_vsol_mac(mac):
    mac = normalize_mac(mac)

    return (
        mac[0:4] + ":" +
        mac[4:8] + ":" +
        mac[8:12]
    )

def format_bdcom_mac(mac):
    mac = normalize_mac(mac)

    return (
        mac[0:4] + "." +
        mac[4:8] + "." +
        mac[8:12]
    )