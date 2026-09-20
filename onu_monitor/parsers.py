from pathlib import Path

def read_olt_file(file_name):
    file_path = Path("data") / file_name

    with file_path.open("r") as file:
        return file.readlines()

def parse_onus(lines):
    all_onus = []
    for line in lines:
        line = line.strip()

        if not line:
            continue
        if not line.startswith("EPON"):
            continue

        columns = line.split()

        if len(columns) != 6:
            continue

        onu_data = {
            "onu": columns[0],
            "temperature": float(columns[1]),
            "voltage": float(columns[2]),
            "tx_bias": float(columns[3]),
            "tx_power": float(columns[4]),
            "rx_power": float(columns[5]),
        }

        all_onus.append(onu_data)

    return all_onus