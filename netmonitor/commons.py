"""
This module provides common functions related to network connections and traffic.
"""

# Imports
from datetime import datetime
import json
import pandas as pd
import psutil
import scapy.all as sc
import urllib3


def get_connection_snapshot():
    """
    This function returns a snapshot of this machine's remote network
    connections and the corresponding processes.

    Local IP addresses are filtered out. The same is true for connections
    with inactive source processes. Internally the function psutil.net_connections
    is used. Its results are transformed into a pandas data frame.

    :return: The snapshot as pandas data frame.
    """
    # Get all network connections
    connections = psutil.net_connections(kind='all')
    con_frame = pd.DataFrame(connections)

    # Add timestamp
    con_frame["timestamp"] = datetime.now()

    # Remove empty addresses
    con_frame = con_frame.loc[con_frame["raddr"] != (), :]

    # Remove connections without pid
    con_frame = con_frame.loc[con_frame["pid"] > 0]

    # Split addresses and ports
    con_frame['laddr'], con_frame['laddr_port'] = zip(*con_frame["laddr"])
    con_frame['raddr'], con_frame['raddr_port'] = zip(*con_frame["raddr"])

    # Remove local ip addresses
    local_ips = get_local_ips()
    con_frame = con_frame.loc[~con_frame["raddr"].isin(local_ips)]

    # Reset index
    con_frame = con_frame.reset_index(drop=True)

    # Return only necessary cols
    cols = ["timestamp", "raddr", "raddr_port", "pid", "status"]
    return con_frame[cols]


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
    :return: The name if available otherwise None.
    """
    try:
        proc = psutil.Process(pid)
        return proc.name()
    except (ProcessLookupError, psutil.NoSuchProcess):
        return None


def get_local_ips():
    """
    This function returns the local IP addresses of this machine.

    :return: The local IP addresses as a list.
    """
    ips = set()

    for line in sc.read_routes():
        ips.add(line[4])

    return list(ips)


def get_ip_infos(ip_address: str, pool_manager: urllib3.PoolManager = None):
    """
    This function returns the organisation and the country of a specific
    IP address.

    :param ip_address: The IP address.
    :param pool_manager: The urllib3.PoolManager to use or None.
    :return: The organisation and country as tuple, if known. Otherwise a tuple with
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
