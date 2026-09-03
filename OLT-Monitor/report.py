#report.py

import csv
from pathlib import Path

def generate_report(all_onus):
    # print("===================================")
    # print("           OLT HEALTH REPORT        ")
    # print("===================================")

    # print(f"Total ONUs : {len(all_onus)}")

    # print("\nCritical ONU")
    # print("-----------------------------------")

    critical_onus = []

    for onu in all_onus:
        if onu["rx_power"] <= -27:
            critical_onus.append(onu)

    #sort critical ONUs according to ther rx power
    critical_onus.sort(key=lambda onu: onu["rx_power"])

    # for onu in critical_onus:
    #     print(f"{onu['onu']:15} RX: {onu['rx_power']} dBm")

def save_csv(all_onus):
    report_folder = Path("reports")
    report_folder.mkdir(exist_ok=True)

    report_path = report_folder / "onu_report.csv"

    with report_path.open("w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "ONU",
            "Temperature",
            "Voltage",
            "TX Bias",
            "TX Power",
            "RX Power",
            "Status"
        ])

        for onu in all_onus:
            rx = onu["rx_power"]

            if rx <= -27:
                status = "Critical"

            elif rx <= -25:
                status = "Warning"

            else:
                status = "Healthy"

            writer.writerow([
                onu["onu"],
                onu["temperature"],
                onu["voltage"],
                onu["tx_bias"],
                onu["tx_power"],
                onu["rx_power"],
                status
            ])