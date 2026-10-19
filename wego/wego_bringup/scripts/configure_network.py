#!/usr/bin/env python3
"""Add temporary sensor addresses without replacing addresses or default routes."""

import argparse
import ipaddress
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--go2-interface', default='enP8p1s0',
        help='Go2 Ethernet interface (default: %(default)s).')
    parser.add_argument(
        '--lidar-interface', default='enx00181af29c25',
        help='MID360 Ethernet interface (default: %(default)s).')
    parser.add_argument(
        '--interface',
        help='Use one shared interface for both devices; overrides both interface options.')
    parser.add_argument(
        '--go2-address', default='192.168.123.99/24',
        help='Jetson address on the Go2 subnet (default: %(default)s).')
    parser.add_argument(
        '--lidar-address', default='192.168.1.5/24',
        help='Jetson address on the MID360 subnet (default: %(default)s).')
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Run with sudo; only temporary IP aliases are added.')

    device_interfaces = (
        args.interface or args.go2_interface,
        args.interface or args.lidar_interface,
    )
    unique_interfaces = list(dict.fromkeys(device_interfaces))
    for interface in unique_interfaces:
        if not (Path('/sys/class/net') / interface).exists():
            parser.error(f'Network interface {interface!r} does not exist.')
    try:
        addresses = [ipaddress.IPv4Interface(address) for address in
                     (args.go2_address, args.lidar_address)]
    except ValueError as exc:
        parser.error(str(exc))

    existing = {}
    for interface in unique_interfaces:
        links = json.loads(subprocess.check_output(
            ['ip', '-j', 'addr', 'show', 'dev', interface], text=True))
        existing[interface] = {
            address['local'] for address in links[0]['addr_info']
            if address['family'] == 'inet'
        }
    for interface, address in zip(device_interfaces, addresses):
        if str(address.ip) not in existing[interface]:
            subprocess.run(['ip', 'address', 'add', str(address),
                            'dev', interface], check=True)
            existing[interface].add(str(address.ip))
            print(f'Added {address} to {interface}')
    print('Temporary recovery addresses are ready; NetworkManager profiles are unchanged.')
    for interface in unique_interfaces:
        subprocess.run(['ip', '-br', 'addr', 'show', 'dev', interface], check=True)


if __name__ == '__main__':
    main()
