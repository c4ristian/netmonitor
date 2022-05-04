"""
This script captures snapshots of this machine's network connections and exports
them to a csv file. The snapshots are captured every 'e' seconds over a period
of 'o' minutes. If the 'o' option is not specified or refers to a value less than
or equal to zero, the programme runs indefinitely.

The option 'l' specifies whether local IPs shall be included. The parameter 'p'
defines if process names shall be looked up. The option 'i' specifices whether
infos on the ip-addresses are looked up.

Examples
--------
>>> python capture_connections.py --p --i --e 30
>>> python capture_connections.py --e 5 --o 1 --f "data/connections.csv"
"""

# Imports
import argparse
import logging
import time
from datetime import datetime, timedelta
import pyfiglet
import schedule
import urllib3
import netmonitor.commons as com

# Global variables
DEFAULT_EVERY_SECONDS = 30
DEFAULT_OVER_MINUTES = -1
DATA_PATH = "data/"
DEFAULT_FILE_PATH = DATA_PATH + "connections.csv"


def _parse_cmd_args():
    """
    This function parses the command-line arguments of the program.

    :return: The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Capture connections')

    parser.add_argument(
        "--e", help=("every e seconds. Default is " + str(DEFAULT_EVERY_SECONDS)),
        default=DEFAULT_EVERY_SECONDS
    )

    parser.add_argument(
        "--o", help=("over o minutes. Default is " + str(DEFAULT_OVER_MINUTES)),
        default=DEFAULT_OVER_MINUTES
    )

    parser.add_argument(
        "--f", help=("path of destination file. Default is '"
                     + str(DEFAULT_FILE_PATH) + "'"),
        default=DEFAULT_FILE_PATH
    )

    parser.add_argument(
        '--l', help="include local/private connections. Default is False",
        action=argparse.BooleanOptionalAction)

    parser.add_argument(
        '--p', help="look up process names. Default is False",
        action=argparse.BooleanOptionalAction)

    parser.add_argument(
        '--i', help="look IP infos. Default is False",
        action=argparse.BooleanOptionalAction)

    args = parser.parse_args()
    return args


def _capture_connections(file_name: str, include_privates=False,
                         look_up_processes=False, look_up_ips=False,
                         write_mode=False):
    """
    This function captures connection snapshots and stores them in a csv file.

    :param file_name: The name of the csv file.
    :param include_privates: True if private IPs shall be included.
    :param look_up_processes: True if process names shall be looked up.
    :param look_up_ips: True if IP infos shall be looked up.
    :param write_mode: True if the file is to be created,
    False if the data is to be appended.
    :return: None.
    """
    logging.info("Connections captured at %s", str(datetime.now()))

    # Get snapshot
    con_frame = com.get_connection_snapshot()

    # Remove local/private addresses
    if not include_privates:
        # pylint: disable=C0121
        # This comparison is ok for pandas
        con_frame = con_frame[con_frame["ip_private"] == False].copy()

    # Look up process names
    if look_up_processes:
        con_frame["process"] = con_frame["pid"].apply(com.get_process_name)

    # Look up IPs
    if look_up_ips and len(con_frame) > 0:
        pool_manager = urllib3.PoolManager()
        con_frame["ip_infos"] = con_frame["ip_address"].apply(
            com.get_ip_infos, args=(pool_manager,))

        con_frame["ip_org"], con_frame["ip_country"] = zip(*con_frame["ip_infos"])
        con_frame = con_frame.drop(["ip_infos"], axis=1)

    # Write results
    mode_flag = "w" if write_mode else "a"

    con_frame.to_csv(
        file_name, mode=mode_flag, index=False, header=write_mode)


def _main():
    """
    This function executes the program.

    :return: None.
    """
    # Configuration
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Parsing command line args
    args = _parse_cmd_args()
    logging.debug("Command line args: %s", args)

    every_seconds = int(args.e)
    over_minutes = int(args.o)
    export_file = args.f
    include_privates = args.l
    look_up_processes = args.p
    look_up_ips = args.i

    # Print figlet
    banner = pyfiglet.figlet_format("CAPCON")
    print(banner)

    # Capture stats initially
    _capture_connections(export_file, include_privates=include_privates,
                         look_up_processes=look_up_processes,
                         look_up_ips=look_up_ips,
                         write_mode=True)

    # Set up scheduler
    capture = schedule.every(every_seconds).seconds.do(
        _capture_connections, export_file, include_privates, look_up_processes, look_up_ips)

    if over_minutes > 0:
        capture.until(timedelta(minutes=over_minutes))

    # Run scheduler
    while 1:
        idle_secs = schedule.idle_seconds()
        if idle_secs is None:
            # no more jobs
            break
        if idle_secs > 0:
            # sleep the right amount of time
            time.sleep(idle_secs)

        schedule.run_pending()


# Main block to run the script
if __name__ == "__main__":
    _main()
