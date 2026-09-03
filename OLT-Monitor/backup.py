# from pathlib import Path

# def read_olt_file(file_name):
#     file_path = Path("data") / file_name

#     with file_path.open("r") as file:
#         return file.readlines()

# lines = read_olt_file("onu.txt")
# all_onus = []
# healthy = 0
# warning = 0
# critical = 0

# for line in lines:
#     line = line.strip()

#     if not line:
#         continue

#     if line.startswith("ONU-ID") or line.startswith("calu"):
#         continue

#     if line.startswith("---"):
#         continue

#     columns = line.split()

#     onu = columns[0]
#     temperature = float(columns[1])
#     voltage = float(columns[2])
#     tx_bias = float(columns[3])
#     tx_power = float(columns[4])
#     rx_power = float(columns[5])

#     onu_data = {
#         "onu": onu,
#         "temperature": temperature,
#         "voltage": voltage,
#         "tx_bias": tx_bias,
#         "tx_power": tx_power,
#         "rx_power": rx_power,
#     }

#     all_onus.append(onu_data)

# # print("\nWeak RX Power (<= -27 dBm)")
# # print("-" * 49)

# total_onus = len(all_onus)
# for onu in all_onus:
#     rx = onu["rx_power"]

#     if rx > -25:
#         healthy += 1
#     elif rx > -27:
#         warning += 1
#     else:
#         critical += 1

# print("=" * 40)
# print("          OLT HEALTH REPORT")
# print("=" * 40)

# print(f"Total ONUs : {total_onus}")
# print(f"Healthy : {healthy}")
# print(f"Warning : {warning}")
# print(f"Critical : {critical}")


# print("\nCritical ONU")
# print("-" * 40)

# for onu in all_onus:
#     if onu["rx_power"] <= -27:
#         print(f"{onu['onu']:15} RX: {onu['rx_power']} dBm")