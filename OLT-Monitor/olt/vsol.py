from mac_utils import format_vsol_mac

class VSOL:
    def __init__(self, ip):
        self.ip = ip

    def connect(self):
        print(f"Connecting VSOL OLT: {self.ip}")

    def enable(self):
        print("Entering enable mode...")
        return "enable"

    def configure_terminal(self):
        print("Entering configuration mode...")
        return "configure terminal"

    def parse_mac_lookup(self, output):
        port = None
        onu_id = None

        for line in output.splitlines():
            line = line.strip()

            if line.startswith("Port"):
                port = line.split(":", 1)[1].strip()

            elif line.startswith("ONU ID"):
                onu_id = line.split(":", 1)[1].strip()

        if port is None or onu_id is None:
            return None

        return f"{port}:{onu_id}"

    def find_onu_by_mac(self, mac):
        vsol_mac = format_vsol_mac(mac)
        command = f"show mac address-table address {vsol_mac}"
        print(f"Executing: {command}")
        return None

    def get_opm(self, onu):
        command = "show onu opm-diag all"
        print(f"Executing: {command}")

        return None

    def parse_opm(self, output, target_onu):
        for line in output.splitlines():
            line = line.strip()

            if not line.startswith(target_onu):
                continue

            columns = line.split()

            if len(columns) != 6:
                continue

            return {
                "ONU": columns[0],
                "Temperature": float(columns[1]),
                "Voltage": float(columns[2]),
                "TX_Bias": float(columns[3]),
                "TX_Power": float(columns[4]),
                "RX_Power": float(columns[5]),
            }
        return None
    

    async def get_customer_info(self, connection, mac):

        # =========================
        # FORMAT MAC
        # =========================

        vsol_mac = format_vsol_mac(mac)

        print()
        print(f"Searching for MAC: {mac}")
        print(f"VSOL MAC format: {vsol_mac}")

        # =========================
        # MAC LOOKUP
        # =========================

        command = f"show mac address-table address {vsol_mac}"

        print()
        print(f"Executing: {command}")

        output = await connection.send_command(command)

        onu = self.parse_mac_lookup(output)

        if not onu:
            print()
            print("ONU not found.")
            return None

        print()
        print(f"ONU found: {onu}")

        # =========================
        # OPM
        # =========================

        print()
        print("Reading ONU optical information...")

        opm_output = await connection.send_command(
            "show onu opm-diag all"
        )

        result = self.parse_opm(
            opm_output,
            onu
        )

        if not result:
            print()
            print("OPM information not found.")
            return None

        return result