

class BDCOM:

    def __init__(self, ip):
        self.ip = ip

    def parse_mac_lookup(self, output):
        
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            columns = line.split()

            if len(columns) < 4:
                continue
            if columns[2].upper() != "DYNAMIC":
                continue
            port = columns[3]
            
            
            if not port.lower().startswith("gpon"):
                continue
            interface_part, onu_part = port.split(":")
            onu_id = onu_part.split("-")[0]
            interface = interface_part
            return {
                "interface": interface,
                "onu_id": onu_id,
                "onu": f"{interface}:{onu_id}"
            }
        return None

    def get_opm_command(self, interface):
        interface_number = interface.replace("gpon", "")

        return (
            "show gpon onu-optical-transceiver-diagnosis "
            f"interface gpon {interface_number}"
        )

    def parse_opm(self, output, target_onu):

        output = output.replace("\r", "")
        output = output.replace("\x08", "")

        lines = output.splitlines()

        for i, line in enumerate(lines):

            line = line.strip()

            if not line:
                continue

            columns = line.split()

            # ==========================================
            # NORMAL FORMAT
            # ==========================================

            if len(columns) == 6 and columns[0] == target_onu:

                try:

                    return {
                        "ONU": columns[0],
                        "Temperature": float(columns[1]),
                        "Voltage": float(columns[2]),
                        "TX_Bias": float(columns[3]),
                        "RX_Power": float(columns[4]),
                        "TX_Power": float(columns[5]),
                    }

                except ValueError:
                    continue


            # ==========================================
            # WRAPPED FORMAT
            # ==========================================

            if len(columns) == 5 and columns[0] == target_onu:

                if i + 1 >= len(lines):
                    continue

                next_line = lines[i + 1].strip()
                next_columns = next_line.split()

                if len(next_columns) < 2:
                    continue

                # Example:
                #
                # columns:
                # ['gpon0/6:17', '56.0', '3.3', '18.0', '-2']
                #
                # next_columns:
                # ['0.4', '2.2']
                #
                # RX Power = -2 + 0.4 = -20.4

                rx_power = columns[4] + next_columns[0]
                tx_power = next_columns[1]

                try:

                    return {
                        "ONU": columns[0],
                        "Temperature": float(columns[1]),
                        "Voltage": float(columns[2]),
                        "TX_Bias": float(columns[3]),
                        "RX_Power": float(rx_power),
                        "TX_Power": float(tx_power),
                    }

                except ValueError:
                    continue

        return None