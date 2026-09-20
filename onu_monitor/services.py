import asyncio

from .vsol_connection import VSOLConnection
from .bdcom_connection import BDCOMConnection
from .mac_utils import format_vsol_mac, format_bdcom_mac
from .olt.vsol import VSOL
from .olt.bdcom import BDCOM


async def run_vsol(olt_name, olt, username, password, mac):
    terminal = []

    connection = VSOLConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:
        terminal.append(f"Connecting to {olt_name} ({olt['ip']})...")

        await connection.connect()
        terminal.append("Connected.")

        await connection.enable(password)
        terminal.append("Enable mode entered.")

        await connection.configure_terminal()
        terminal.append("Terminal configured.")

        vsol_mac = format_vsol_mac(mac)
        command = f"show mac address-table address {vsol_mac}"

        terminal.append(f"$ {command}")

        output = await connection.send_command(command)
        terminal.append(output)

        olt_parser = VSOL(olt["ip"])
        onu = olt_parser.parse_mac_lookup(output)

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

        optical = olt_parser.parse_opm(opm_output, onu)

        return {
            "success": True,
            "terminal": "\n".join(terminal),
            "onu": {
                "mac": mac,
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


async def run_bdcom(olt_name, olt, username, password, mac):
    terminal = []

    connection = BDCOMConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:
        terminal.append(f"Connecting to {olt_name} ({olt['ip']})...")

        success = await connection.connect()

        if not success:
            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "Authentication failed."
            }

        terminal.append("Connected.")

        bdcom = BDCOM(olt["ip"])

        bdcom_mac = format_bdcom_mac(mac)
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
            "onu": {
                "mac": mac,
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