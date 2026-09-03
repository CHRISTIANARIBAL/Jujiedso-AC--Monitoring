class Customer:
    def __init__(self, username, mac, ip_address, olt_name, nas_port):
        self.username = username
        self.mac = mac
        self.ip_address = ip_address
        self.olt_name = olt_name
        self.nas_port = nas_port