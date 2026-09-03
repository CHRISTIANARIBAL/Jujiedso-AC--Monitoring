import asyncio

from flask import Flask, jsonify, request, send_from_directory

from config import OLTS
from vsol_connection import VSOLConnection
from bdcom_connection import BDCOMConnection

from mac_utils import format_vsol_mac, format_bdcom_mac

from olt.vsol import VSOL
from olt.bdcom import BDCOM


app = Flask(__name__, static_folder="web")

def clean_terminal_output(output):
    return (
        output
        .replace("\x08", "")
        .replace("\r", "")
    )

@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/api/olts")
def get_olts():
    result = {}

    for name, olt in OLTS.items():
        result[name] = {
            "brand": olt["brand"],
            "ip": olt["ip"],
        }

    return jsonify(result)


@app.route("/api/lookup", methods=["POST"])
def lookup():
    data = request.get_json()

    olt_name = data.get("olt")
    username = data.get("username")
    password = data.get("password")
    mac = data.get("mac")

    if not olt_name:
        return jsonify({
            "success": False,
            "error": "OLT was not selected."
        }), 400

    if olt_name not in OLTS:
        return jsonify({
            "success": False,
            "error": "Invalid OLT."
        }), 400

    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Username and password are required."
        }), 400

    if not mac:
        return jsonify({
            "success": False,
            "error": "MAC address is required."
        }), 400

    olt = OLTS[olt_name]

    try:

        if olt["brand"] == "VSOL":

            result = asyncio.run(
                run_vsol(
                    olt_name,
                    olt,
                    username,
                    password,
                    mac
                )
            )

        elif olt["brand"] == "BDCOM":

            result = asyncio.run(
                run_bdcom(
                    olt_name,
                    olt,
                    username,
                    password,
                    mac
                )
            )

        else:

            return jsonify({
                "success": False,
                "error": "Unsupported OLT brand."
            }), 400

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


async def run_vsol(
    olt_name,
    olt,
    username,
    password,
    mac
):

    terminal = []

    terminal.append("==========================================")
    terminal.append(f"OLT SELECTED: {olt_name}")
    terminal.append("==========================================")

    terminal.append(f"Brand: {olt['brand']}")
    terminal.append(f"IP: {olt['ip']}")

    terminal.append("")
    terminal.append("Connecting to VSOL...")

    connection = VSOLConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:

        # =========================
        # CONNECT
        # =========================

        await connection.connect()

        terminal.append("")
        terminal.append("VSOL login successful.")

        # =========================
        # ENABLE
        # =========================

        terminal.append("")
        terminal.append("Entering enable mode...")

        await connection.enable(password)

        # =========================
        # CONFIGURATION MODE
        # =========================

        terminal.append("")
        terminal.append("Entering configuration mode...")

        await connection.configure_terminal()

        terminal.append("")
        terminal.append("OLT connection is ready.")

        # =========================
        # FORMAT MAC
        # =========================

        terminal.append("")
        terminal.append(f"Searching for MAC: {mac}")

        vsol_mac = format_vsol_mac(mac)

        terminal.append(
            f"VSOL MAC format: {vsol_mac}"
        )

        # =========================
        # MAC LOOKUP
        # =========================

        command = (
            f"show mac address-table address {vsol_mac}"
        )

        terminal.append("")
        terminal.append(
            f"Executing: {command}"
        )

        output = await connection.send_command(
            command
        )

        terminal.append("")
        terminal.append(
            "========== RAW VSOL OUTPUT =========="
        )

        terminal.append(
            output
        )

        terminal.append(
            "====================================="
        )

        # =========================
        # PARSE MAC
        # =========================

        onu = VSOL(
            olt["ip"]
        ).parse_mac_lookup(
            output
        )

        if not onu:

            terminal.append("")
            terminal.append(
                "ONU not found."
            )

            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "ONU not found."
            }

        terminal.append("")
        terminal.append(
            f"ONU found: {onu}"
        )

        # =========================
        # OPM
        # =========================

        terminal.append("")
        terminal.append(
            "Reading ONU optical information..."
        )

        opm_command = "show onu opm-diag all"

        terminal.append("")
        terminal.append(
            f"Executing: {opm_command}"
        )

        opm_output = await connection.send_command(
            opm_command
        )

        terminal.append("")
        terminal.append(
            "========== RAW OPTICAL OUTPUT =========="
        )

        terminal.append(
            opm_output
        )

        terminal.append(
            "========================================"
        )

        # =========================
        # PARSE OPM
        # =========================

        vsol = VSOL(
            olt["ip"]
        )

        optical = vsol.parse_opm(
            opm_output,
            onu
        )

        if not optical:

            terminal.append("")
            terminal.append(
                "OPM information not found."
            )

            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "OPM information not found."
            }

        terminal.append("")
        terminal.append(
            "OPM information retrieved successfully."
        )

        # =========================
        # RESULT
        # =========================

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

        terminal.append("")
        terminal.append(
            f"ERROR: {str(e)}"
        )

        return {
            "success": False,
            "terminal": "\n".join(terminal),
            "error": str(e)
        }

    finally:

        await connection.close()


async def run_bdcom(
    olt_name,
    olt,
    username,
    password,
    mac
):

    terminal = []

    terminal.append(
        f"Selected OLT: {olt_name}"
    )

    terminal.append(
        f"Brand: {olt['brand']}"
    )

    terminal.append(
        f"IP: {olt['ip']}"
    )

    terminal.append("")
    terminal.append("Connecting to BDCOM...")

    connection = BDCOMConnection(
        host=olt["ip"],
        username=username,
        password=password
    )

    try:

        success = await connection.connect()

        if not success:

            terminal.append("")
            terminal.append(
                "BDCOM authentication failed."
            )

            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "Authentication failed."
            }

        terminal.append("")
        terminal.append(
            "BDCOM login successful."
        )

        bdcom = BDCOM(olt["ip"])

        terminal.append("")
        terminal.append(
            f"MAC address: {mac}"
        )

        bdcom_mac = format_bdcom_mac(mac)

        terminal.append(
            f"BDCOM MAC format: {bdcom_mac}"
        )

        command = (
            f"show mac address-table {bdcom_mac}"
        )

        terminal.append("")
        terminal.append(
            f"Executing: {command}"
        )

        output = await connection.send_command(
            command
        )

        terminal.append("")
        terminal.append(
            "========== RAW BDCOM OUTPUT =========="
        )

        terminal.append(output)

        terminal.append(
            "======================================"
        )

        result = bdcom.parse_mac_lookup(output)

        if not result:

            terminal.append("")
            terminal.append("ONU not found.")

            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "ONU not found."
            }

        # ---------------------------------
        # PARSER RESULT
        # ---------------------------------

        interface = result["interface"]
        onu_id = result["onu_id"]
        onu = result["onu"]

        terminal.append("")
        terminal.append(
            f"ONU found: {onu}"
        )

        terminal.append(
            f"Interface: {interface}"
        )

        terminal.append(
            f"ONU ID: {onu_id}"
        )

        # ---------------------------------
        # GET OPM COMMAND
        # ---------------------------------

        opm_command = bdcom.get_opm_command(
            interface
        )

        terminal.append("")
        terminal.append(
            f"Executing: {opm_command}"
        )

        opm_output = await connection.send_command(
            opm_command
        )

        terminal.append("")
        terminal.append(
            "========== RAW OPTICAL OUTPUT =========="
        )

        terminal.append(opm_output)

        terminal.append(
            "========================================="
        )

        # ---------------------------------
        # PARSE OPTICAL INFORMATION
        # ---------------------------------

        optical = bdcom.parse_opm(
            opm_output,
            onu
        )

        if not optical:

            terminal.append("")
            terminal.append(
                "Optical information not found."
            )

            return {
                "success": False,
                "terminal": "\n".join(terminal),
                "error": "Optical information not found."
            }

        terminal.append("")
        terminal.append(
            "Optical information retrieved."
        )

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

        terminal.append("")
        terminal.append(
            f"ERROR: {str(e)}"
        )

        return {
            "success": False,
            "terminal": "\n".join(terminal),
            "error": str(e)
        }

    finally:

        await connection.close()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )