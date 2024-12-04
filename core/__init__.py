import argparse

def add_core_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('-ip', '--bambu-ip', required=True, help="IP of your bambu printer. Eg. 192.168.1.100")
    parser.add_argument('-sn', '--bambu-sn', required=True, help="SN of your bambu printer. Required to subscribe to MQTT channel.")
    parser.add_argument('-ac', '--bambu-ac', required=True, help="Access code of your bambu printer")
