import asyncio

from .vsol_connection import VSOLConnection
from .bdcom_connection import BDCOMConnection
from .mac_utils import format_vsol_mac, format_bdcom_mac
from .olt.vsol import VSOL
from .olt.bdcom import BDCOM
from monitor.models import PPPoEClient
import asyncio
from asgiref.sync import sync_to_async

@sync_to_async
def find_pppoe_clients(mac):
    clients = (
        PPPoEClient.objects
        .filter(mac_address__iexact=mac)
        .select_related("ac")
        .order_by("-last_seen", "-id")
    )

    return [
        {
            "username": client.username,
            "mac": client.mac_address,
            "ac": client.ac.name if client.ac else None,
            "olt_name": client.olt_name,
            "olt_interface": client.olt_interface,
            "connection_type": client.connection_type,
            "connection_name": client.connection_name,
            "connection_interface": client.connection_interface,
            "last_seen": client.last_seen.isoformat() if client.last_seen else None,
        }
        for client in clients
    ]

async def run_vsol(olt_name, olt, username, password, value, lookup_mode="mac"):
    terminal = []

    connection = VSOLConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:
        terminal.append("==========================================")
        terminal.append(f"OLT: {olt_name}")
        terminal.append(f"IP: {olt['ip']}")
        terminal.append(f"BRAND: {olt['brand']}")
        terminal.append("==========================================")
        terminal.append("")
        terminal.append("Connecting...")

        await connection.connect()

        terminal.append("Connected.")

        await connection.enable(password)
        terminal.append("Enable mode entered.")

        await connection.configure_terminal()
        terminal.append("Terminal configured.")

        vsol = VSOL(olt["ip"])

        if lookup_mode == "onu":
            onu = value.strip()

            commands = vsol.get_reverse_mac_command(onu)

            if not commands:
                return {
                    "success": False,
                    "terminal": "\n".join(terminal),
                    "error": "Invalid ONU format. Example: epon0/2:40"
                }

            terminal.append(f"$ {commands['interface']}")

            await connection.send_command(
                commands["interface"]
            )

            terminal.append(f"$ {commands['mac']}")

            output = await connection.send_command(
                commands["mac"]
            )

            terminal.append(output)

            mac = vsol.parse_reverse_mac(output)
            if not mac:
                return {"success": False, "terminal": "\n".join(terminal), "error": "MAC address not found for this ONU."}

            print("DEBUG 1: MAC FOUND:", mac, flush=True)

            interface = onu.split(":")[0]

            print("DEBUG 2: BEFORE PPPoE LOOKUP", flush=True)

            pppoe_clients = await find_pppoe_clients(mac)

            print("DEBUG 3: AFTER PPPoE LOOKUP:", pppoe_clients, flush=True)

            return {
                "success": True,
                "terminal": "\n".join(terminal),
                "lookup_mode": "onu",
                "onu": {
                    "mac": mac,
                    "interface": interface,
                    "onu": onu
                },
                "pppoe_clients": pppoe_clients
            }

        vsol_mac = format_vsol_mac(value)

        command = f"show mac address-table address {vsol_mac}"

        terminal.append(f"$ {command}")

        output = await connection.send_command(command)

        terminal.append(output)

        onu = vsol.parse_mac_lookup(output)

        if not onu:
            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "ONU not found."
            }

        opm_command = "show onu opm-diag all"

        terminal.append(f"$ {opm_command}")

        opm_output = await connection.send_command(opm_command)

        terminal.append(opm_output)

        optical = vsol.parse_opm(opm_output, onu)

        return {
            "success": True,
            "terminal": "\n".join(terminal),
            "lookup_mode": "mac",
            "onu": {
                "mac": value,
                "interface": onu.split(":")[0],
                "onu": onu
            },
            "optical": optical
        }

    except Exception as e:
        return {
            "success": False,
            "terminal": "\n".join(terminal),
            "error": str(e)
        }

    finally:
        await connection.close()

async def run_bdcom(olt_name, olt, username, password, value, lookup_mode="mac"):
    terminal = []

    connection = BDCOMConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:
        terminal.append("==========================================")
        terminal.append(f"OLT: {olt_name}")
        terminal.append(f"IP: {olt['ip']}")
        terminal.append(f"BRAND: {olt['brand']}")
        terminal.append("==========================================")
        terminal.append("")
        terminal.append("Connecting...")

        success = await connection.connect()

        if not success:
            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "Authentication failed."
            }

        terminal.append("Connected.")

        bdcom = BDCOM(olt["ip"])

        # ==========================================
        # REVERSE LOOKUP
        # ONU -> MAC
        # ==========================================

        if lookup_mode == "onu":
            onu = value.strip()

            command = bdcom.get_reverse_mac_command(onu)

            if not command:
                return {
                    "success": False,
                    "terminal": "\n".join(terminal),
                    "error": "Invalid ONU format. Example: gpon0/2:27"
                }

            terminal.append(f"$ {command}")

            output = await connection.send_command(command)
            terminal.append(output)

            mac = bdcom.parse_reverse_mac(output)
            if not mac:
                return {"success": False, "terminal": "\n".join(terminal), "error": "MAC address not found for this ONU."}

            print("DEBUG 1: MAC FOUND:", mac, flush=True)

            interface = onu.split(":")[0]

            print("DEBUG 2: BEFORE PPPoE LOOKUP", flush=True)

            pppoe_clients = await find_pppoe_clients(mac)

            print("DEBUG 3: AFTER PPPoE LOOKUP:", pppoe_clients, flush=True)

            return {
                "success": True,
                "terminal": "\n".join(terminal),
                "lookup_mode": "onu",
                "onu": {
                    "mac": mac,
                    "interface": interface,
                    "onu": onu
                },
                "pppoe_clients": pppoe_clients
            }

        # ==========================================
        # NORMAL MAC LOOKUP
        # MAC -> ONU -> OPM
        # ==========================================

        bdcom_mac = format_bdcom_mac(value)
        command = f"show mac address-table {bdcom_mac}"

        terminal.append(f"$ {command}")

        output = await connection.send_command(command)
        terminal.append(output)

        result = bdcom.parse_mac_lookup(output)

        if not result:
            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "ONU not found."
            }

        interface = result["interface"]
        onu_id = result["onu_id"]
        onu = result["onu"]

        opm_command = bdcom.get_opm_command(interface)

        terminal.append(f"$ {opm_command}")

        opm_output = await connection.send_command(opm_command)
        terminal.append(opm_output)

        optical = bdcom.parse_opm(opm_output, onu)

        return {
            "success": True,
            "terminal": "\n".join(terminal),
            "lookup_mode": "mac",
            "onu": {
                "mac": value,
                "interface": interface,
                "onu": onu
            },
            "optical": optical
        }

    except Exception as e:
        return {
            "success": False,
            "terminal": "\n".join(terminal),
            "error": str(e)
        }

    finally:
        await connection.close()