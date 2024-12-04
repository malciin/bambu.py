from argparse import Namespace
from dataclasses import dataclass

@dataclass
class BambuMqttCredentials:
    ip: str
    access_code: str
    serial_number: str

def parse(args: Namespace) -> BambuMqttCredentials:
    return BambuMqttCredentials(
        ip=args.bambu_ip,
        access_code=args.bambu_ac,
        serial_number=args.bambu_sn)
