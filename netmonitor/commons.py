"""
This module provides common functions related to network connections and traffic.
"""

# Imports
from datetime import datetime
import json
from netaddr import IPAddress
import pandas as pd
import psutil
import scapy.all as sc
import urllib3


# Columns for connection snapshot
_CONNECTION_COLUMNS = ["timestamp", "ip_address", "port", "ip_private", "pid", "status"]


def get_connection_snapshot():
    """
    This function returns a snapshot of this machine's network
    connections and the corresponding source processes.

    Internally the function psutil.net_connections is used. Its results are transformed
    into a pandas data frame. Connections with inactive source processes are filtered out.
    IP addresses are converted to ipv4 format.

    :return: The snapshot as pandas data frame.
    """
    # Get all network connections
    connections = psutil.net_connections(kind='all')

    # Create data frame
    if len(connections) > 0:
        con_frame = pd.DataFrame(connections)
    # If no connections are available, return empty data frame
    else:
        return pd.DataFrame(columns=_CONNECTION_COLUMNS)

    # Add timestamp
    con_frame["timestamp"] = datetime.now()

    # Remove empty addresses
    con_frame = con_frame.loc[con_frame["raddr"] != (), :]
    con_frame = con_frame.loc[con_frame["raddr"] != "", :]

    # Remove connections without pid
    con_frame = con_frame.loc[con_frame["pid"] > 0]
    con_frame["pid"] = con_frame["pid"].astype("int64")

    # Split addresses and ports
    con_frame['ip_address'], con_frame['port'] = zip(*con_frame["raddr"])

    # Transform addresses to ipv4
    con_frame["ip_address"] = con_frame["ip_address"].apply(to_ipv4)

    # Indicate whether ip is private
    private_ips = get_private_ips()
    con_frame["ip_private"] = con_frame["ip_address"].apply(
        is_private_ip, args=(private_ips,))

    # Reset index
    con_frame = con_frame.reset_index(drop=True)

    # Return only necessary cols
    return con_frame[_CONNECTION_COLUMNS]


def get_traffic_snapshot(pernic=True):
    """
    This function returns a snapshot of network traffic metrics of
    this machine.

    Internally the function psutil.net_io_counters is used. Its
    results are transformed into a pandas data frame.

    :param pernic: True if the metrics are to be returned per network interface,
    False if totals are to be returned.
    :return: The snapshot as a pandas data frame.
    """
    net_stats = psutil.net_io_counters(pernic=pernic, nowrap=True)

    interfaces = []
    packets_received = []
    packets_sent = []
    bytes_received = []
    bytes_sent = []

    # If statistics are total
    if not pernic:
        net_stats = {"all": net_stats}

    # Extract information
    for nic in net_stats:
        interfaces.append(nic)
        packets_received.append(net_stats[nic].packets_recv)
        packets_sent.append(net_stats[nic].packets_sent)
        bytes_received.append(net_stats[nic].bytes_recv)
        bytes_sent.append(net_stats[nic].bytes_sent)

    # Create data frame
    net_frame = pd.DataFrame({
        "timestamp": datetime.now(), "network_interface": interfaces,
        "packets_recv": packets_received, "packets_sent": packets_sent,
        "bytes_recv": bytes_received, "bytes_sent": bytes_sent
    })

    return net_frame


def get_process_name(pid: int):
    """
    This function returns the name of a specific process.

    :param pid: The process ID.
    :return: The name if available, otherwise None.
    """
    try:
        proc = psutil.Process(pid)
        return proc.name()
    except (ProcessLookupError, psutil.NoSuchProcess):
        return None


def is_private_ip(ip_address: str, private_ips=None):
    """
    This function returns true, if a specific IP address is private.

    :param ip_address: The IP address.
    :param private_ips: A list or set with private IP addresses. Default is None,
    in this case the function get_private_ips is called.
    :return: True if an address is private, False otherwise.
    """
    if private_ips is None:
        private_ips = get_private_ips()

    return any(l in ip_address for l in private_ips)


def get_private_ips():
    """
    This function returns the private IP addresses of this machine.

    :return: The private IP addresses as a set.
    """
    ips = set()

    # Try to get private ips from scapy
    for line in sc.read_routes():
        ips.add(line[4])

    # If scapy is not available, add some defaults
    if len(ips) == 0:
        ips.add("127.0.0.1")
        ips.add("10.0.0.0")
        ips.add("0.0.0.1")

    return ips


def get_ip_infos(ip_address: str, pool_manager: urllib3.PoolManager = None):
    """
    This function returns the organisation and the country of a specific
    IP address.

    :param ip_address: The IP address.
    :param pool_manager: The urllib3.PoolManager to use or None.
    :return: The organisation and country as tuple, if available. Otherwise a tuple with
    Nones is returned.
    """
    if pool_manager is None:
        pool_manager = urllib3.PoolManager()

    try:
        response = pool_manager.request("GET", f"https://ipinfo.io/{ip_address}/json")
        ip_infos = json.loads(response.data.decode('utf8'))
        return ip_infos["org"], ip_infos["country"]
    except KeyError:
        return None, None


def to_ipv4(ip_address: str):
    """
    This function transforms a certain IP address into the ipv4 format.

    :param ip_address: The IP address.
    :return: The ipv4 address.
    """
    addr = IPAddress(ip_address)
    return addr.ipv4().format()
