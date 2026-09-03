
import asyncio

from config import OLTS
from mac_utils import format_vsol_mac, format_bdcom_mac

from vsol_connection import VSOLConnection
from bdcom_connection import BDCOMConnection

from olt.vsol import VSOL
from olt.bdcom import BDCOM


async def run_vsol(olt_name, olt, username, password):
    connection = VSOLConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:
        print()
        print(f"Selected OLT : {olt_name}")
        print(f"Brand        : {olt['brand']}")
        print(f"IP Address   : {olt['ip']}")

        await connection.connect()
        await connection.enable(password)
        await connection.configure_terminal()

        print()
        print("VSOL login successful.")
        print("OLT connection is ready.")
        print()

        vsol = VSOL(olt["ip"])

        # =========================================================
        # ONE MAC LOOKUP ONLY
        # =========================================================

        mac = input("Enter MAC address: ").strip()

        if not mac:
            print()
            print("No MAC address entered.")
            return

        print()
        print(f"Searching for MAC: {mac}")

        try:
            vsol_mac = format_vsol_mac(mac)
        except ValueError as e:
            print()
            print(e)
            print()
            return

        print(f"VSOL MAC format: {vsol_mac}")

        command = f"show mac address-table address {vsol_mac}"

        print()
        print(f"Executing: {command}")

        try:
            output = await connection.send_command(command)

            print()
            print("========== RAW VSOL OUTPUT ==========")
            print(repr(output))
            print("=====================================")

        except (
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            BrokenPipeError,
            EOFError
        ) as e:

            print()
            print("===================================")
            print("       OLT CONNECTION LOST")
            print("===================================")
            print(f"Reason: {e}")
            print("===================================")

            return

        onu = vsol.parse_mac_lookup(output)

        if not onu:
            print()
            print("ONU not found.")
            print()
            return

        # =========================================================
        # ONU FOUND
        # =========================================================

        print()
        print(f"ONU found: {onu}")

        print()
        print("Reading ONU optical information...")

        try:
            opm_output = await connection.send_command(
                "show onu opm-diag all"
            )

        except (
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            BrokenPipeError,
            EOFError
        ) as e:

            print()
            print("===================================")
            print("       OLT CONNECTION LOST")
            print("===================================")
            print(f"Reason: {e}")
            print("===================================")

            return

        result = vsol.parse_opm(opm_output, onu)

        if not result:
            print()
            print("OPM information not found.")
            print()
            return

        # =========================================================
        # DISPLAY CUSTOMER INFORMATION
        # =========================================================

        print()
        print("===================================")
        print("       CUSTOMER ONU INFORMATION")
        print("===================================")

        print(f"MAC         : {mac}")
        print(f"ONU         : {result['ONU']}")
        print(f"Temperature : {result['Temperature']} °C")
        print(f"Voltage     : {result['Voltage']} V")
        print(f"TX Bias     : {result['TX_Bias']} mA")
        print(f"TX Power    : {result['TX_Power']} dBm")
        print(f"RX Power    : {result['RX_Power']} dBm")

        print("===================================")
        print()

    except KeyboardInterrupt:
        print()
        print()
        print("Stopping OLT session...")

    finally:
        print()
        print("Closing VSOL connection...")

        try:
            await connection.close()
        except Exception:
            pass

        print("VSOL connection closed.")


async def run_bdcom(olt_name, olt, username, password):
    connection = BDCOMConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:
        print()
        print(f"Selected OLT : {olt_name}")
        print(f"Brand        : {olt['brand']}")
        print(f"IP Address   : {olt['ip']}")

        success = await connection.connect()

        if not success:
            print()
            print("Could not authenticate to BDCOM.")
            return

        print()
        print("BDCOM login successful.")
        print("OLT connection is ready.")
        print()

        bdcom = BDCOM(olt["ip"])

        # =========================================================
        # ONE MAC LOOKUP ONLY
        # =========================================================

        mac = input("Enter MAC address: ").strip()

        if not mac:
            print()
            print("No MAC address entered.")
            return

        print()
        print(f"Searching for MAC: {mac}")

        try:
            bdcom_mac = format_bdcom_mac(mac)

        except ValueError as e:
            print()
            print(e)
            print()
            return

        print(f"BDCOM MAC format: {bdcom_mac}")

        command = f"show mac address-table {bdcom_mac}"

        print()
        print(f"Executing: {command}")

        try:
            output = await connection.send_command(command)

        except (
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            BrokenPipeError,
            EOFError
        ) as e:

            print()
            print("===================================")
            print("       OLT CONNECTION LOST")
            print("===================================")
            print(f"Reason: {e}")
            print("===================================")

            return

        result = bdcom.parse_mac_lookup(output)

        if not result:
            print()
            print("ONU not found.")
            print()
            return

        # =========================================================
        # ONU FOUND
        # =========================================================

        print()
        print("ONU FOUND")
        print("-----------------------------")
        print(f"Interface : {result['interface']}")
        print(f"ONU ID    : {result['onu_id']}")
        print(f"ONU       : {result['onu']}")
        print("-----------------------------")

        interface = result["interface"]

        print()
        print(f"Reading optical information from {interface}...")

        gpon_interface = interface.split(":")[0]
        slot_port = gpon_interface.replace("gpon", "")

        slot, port = slot_port.split("/")

        command = (
            f"show gpon onu-optical-transceiver-diagnosis "
            f"interface gpon {slot}/{port}"
        )

        print()
        print(f"Executing: {command}")

        try:
            opm_output = await connection.send_command(command)

        except (
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            BrokenPipeError,
            EOFError
        ) as e:

            print()
            print("===================================")
            print("       OLT CONNECTION LOST")
            print("===================================")
            print(f"Reason: {e}")
            print("===================================")

            return

        opm = bdcom.parse_opm(
            opm_output,
            result["onu"]
        )

        if not opm:
            print()
            print("Optical information not found.")
            print()
            return

        # =========================================================
        # DISPLAY CUSTOMER INFORMATION
        # =========================================================

        print()
        print("===================================")
        print("       CUSTOMER ONU INFORMATION")
        print("===================================")

        print(f"MAC         : {mac}")
        print(f"ONU         : {opm['ONU']}")
        print(f"Temperature : {opm['Temperature']} °C")
        print(f"Voltage     : {opm['Voltage']} V")
        print(f"TX Bias     : {opm['TX_Bias']} mA")
        print(f"TX Power    : {opm['TX_Power']} dBm")
        print(f"RX Power    : {opm['RX_Power']} dBm")

        print("===================================")
        print()

    except KeyboardInterrupt:
        print()
        print()
        print("Stopping OLT session...")

    finally:
        print()
        print("Closing BDCOM connection...")

        try:
            await connection.close()
        except Exception:
            pass

        print("BDCOM connection closed.")


async def main():

    olt_name = input(
        "Select: CALU-OLT1 to CALU-OLT4 or COMM-OLT1): "
    ).strip().upper()

    if olt_name not in OLTS:
        print()
        print("Invalid OLT.")
        return

    olt = OLTS[olt_name]

    print()
    username = input("Username: ").strip()

    import getpass
    password = getpass.getpass("Password: ")

    if olt["brand"] == "VSOL":
        await run_vsol(olt_name, olt, username, password)

    elif olt["brand"] == "BDCOM":
        await run_bdcom(olt_name, olt, username, password)

    else:
        print()
        print(f"Unsupported OLT brand: {olt['brand']}")


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print()
        print()
        print("Program stopped.")

