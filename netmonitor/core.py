"""
This module provides core functions to monitor network connections.
"""

# Imports
import http.client
import json
import numpy as np
import pandas as pd
import psutil
import scapy.all as sc


# Column names for connection snapshot
CONNECTION_COLUMNS = [
    'date', 'pid', 'proc', 'status', 'lip', 'lport', 'rip', 'rport', 'rpriv']


def _extract_ip(address):
    """
    This function extracts the IP address from a named tuple with the
    format (ip, port).

    :param address: A tuple with the IP address.
    :return: The ip address or None if the tuple is not in the correct format.
    """
    result = None
    if address is not None and len(address) > 0:
        result = address[0]
    return result


def _extract_port(address):
    """
    This function extracts the port from a named tuple with the
    format (ip, port).

    :param address: A tuple with the port.
    :return: The port or -1 if the tuple is not in the correct format.
    """
    result = -1
    if address is not None and len(address) > 1:
        result = address[1]
    return result


def is_private_ip(ip_address: str, private_ips=None):
    """
    This function returns true, if a specific IP address is private.

    :param ip_address: The IP address.
    :param private_ips: A list or set with private IP addresses. Default is None,
    in this case the function get_private_ips is called.
    :return: True if an address is private, False otherwise.
    """
    result = False

    if ip_address is not None:
        if private_ips is None:
            private_ips = get_private_ips()

        result = any(l in ip_address for l in private_ips)
    return result


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

    # Convert ips to ipv6 format

    return ips


def get_connections():
    """
    This function returns a DataFrame with the current network connections.

    :return: A DataFrame with the current network connections.
    """
    # Get connections and convert to DataFrame
    raw_connections = psutil.net_connections()

    if raw_connections is not None and len(raw_connections) > 0:
        connections = pd.DataFrame(raw_connections)
    # If no connections are available, return an empty DataFrame
    else:
        return pd.DataFrame(columns=CONNECTION_COLUMNS)

    # Extract IPs and ports
    connections['lip'] = connections['laddr'].apply(_extract_ip)
    connections['lport'] = connections['laddr'].apply(_extract_port)
    connections['rip'] = connections['raddr'].apply(_extract_ip)
    connections['rport'] = connections['raddr'].apply(_extract_port)

    # Check if remote IP is private
    private_ips = get_private_ips()
    connections["rpriv"] = connections["rip"].apply(
        is_private_ip, args=(private_ips,))

    # Add current date and time
    connections['date'] = pd.Timestamp.now()

    # Use numpy to replace empty values with -1
    connections["pid"] = np.where(connections["pid"].isna(), -1, connections["pid"])
    connections["pid"] = connections["pid"].astype(int)

    # Get process names
    connections['proc'] = connections['pid'].apply(get_process_name)

    result_frame = connections[CONNECTION_COLUMNS]
    return result_frame


def get_process_name(pid: int):
    """
    This function returns the name of a specific process.

    :param pid: The process ID.
    :return: The name if available, otherwise None.
    """
    process_name = None

    if pid is not None and isinstance(pid, int) and pid > 0:
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
        except (ProcessLookupError, psutil.NoSuchProcess):
            pass

    return process_name


def get_ip_infos(ip_address: str):
    """
    This function returns the organisation and the country of a specific
    IP address.

    :param ip_address: The IP address.
    :return: The organisation and country as tuple, if available. Otherwise a tuple with
    Nones is returned.
    """
    result = None, None

    # Check if the IP address is valid
    if ip_address is None or len(ip_address) == 0:
        return result

    # Try to get infos
    conn = http.client.HTTPSConnection("ipinfo.io")
    try:
        conn.request("GET", f"/{ip_address}/json")
        response = conn.getresponse()
        if response.status == 200:
            ip_infos = json.loads(response.read().decode('utf8'))
            result = ip_infos.get("org"), ip_infos.get("country")
    finally:
        conn.close()
    return result
