#!/usr/bin/env python3
"""
This script prints a snapshot of the current connections of the system.

Examples
--------
# >>> python snapshot.py -h
# >>> python snapshot.py --private --empty_rip --csv
"""

# Imports
import argparse
from netmonitor import core


def _parse_cmd_args():
    """
    This function parses the command-line arguments of the program.

    :return: The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Print connection snapshot')

    parser.add_argument(
        '--private', help="include private remote IPs. Default is False",
        action=argparse.BooleanOptionalAction)


    parser.add_argument(
        '--empty_rip', help="include empty remote IPs. Default is False",
        action=argparse.BooleanOptionalAction)

    parser.add_argument(
        '--csv', help="print as CSV. Default is False",
        action=argparse.BooleanOptionalAction)

    args = parser.parse_args()
    return args


def _main():
    """
    This function executes the script.

    :return: None.
    """
    # Parse command-line arguments
    args = _parse_cmd_args()
    print_private = False
    print_empty_remote = False
    print_as_csv = False

    if args is not None:
        print_as_csv = args.csv
        print_private = args.private
        print_empty_remote = args.empty_rip

    # Get connections
    snapshot = core.get_connections()

    # Maybe filter out private connections
    if not print_private:
        # pylint: disable=C0121
        # is False does not work with pandas
        snapshot = snapshot[snapshot['rpriv'] == False]

    if not print_empty_remote:
        snapshot = snapshot[(snapshot['rip'] != '')]
        snapshot = snapshot[(snapshot['rip'].notna())]

    # Print snapshot
    if print_as_csv:
        print(snapshot.to_csv(index=False))
    else:
        print(snapshot.to_string(index=False))


# Main block
if __name__ == "__main__":
    _main()
