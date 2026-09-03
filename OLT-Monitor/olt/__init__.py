from .vsol import VSOL
from .bdcom import BDCOM

def get_olt(olt_name, config):
    olt = config[olt_name]

    if olt["brand"].upper() == "VISOL":
        return VSOL(olt["ip"])

    if olt["brand"].upper() == "BDCOM":
        return BDCOM(olt["ip"])

    raise ValueError(f"Unsupported OLT brand: {olt['brand']}")