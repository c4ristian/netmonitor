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


class IpInfoCache:
    """
    This class is used to cache IP address information.

    The cache is a dictionary with the IP address as key and the
    organisation and country as value. The cache is saved to a
    JSON file on disk.
    """
    def __init__(self):
        self._cache_dict = {}

    def load_from_json(self, cache_file: str):
        """
        This function loads the cache from the JSON file.
        """
        try:
            # Open with encoding UTF-8
            with open(cache_file, 'r', encoding='utf-8') as f:
                self._cache_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._cache_dict = {}

    def save_to_json(self, cache_file: str):
        """
        This function saves the cache to the JSON file.
        """
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self._cache_dict, f)

    def get_ip_infos(self, ip_address: str):
        """
        This function returns the organisation and country of a specific
        IP address. If the IP address is not in the cache, it is added. The
        information is retrieved from the get_ip_infos function.

        :param ip_address: The IP address.
        :return: The organisation and country as tuple, if available. Otherwise, a tuple with
        Nones is returned.
        """
        if ip_address in self._cache_dict:
            return self._cache_dict[ip_address]

        org, country = get_ip_infos(ip_address)
        self._cache_dict[ip_address] = (org, country)
        return org, country

    def match_ip_infos(self, ip_addresses: pd.Series):
        """
        This function takes a pandas Series with IP addresses and returns a
        DataFrame with the organisation and country of each IP address.

        The function uses the get_ip_infos function to retrieve the information.

        :param ip_addresses: A pandas Series with IP addresses.
        :return: A DataFrame with the organisation and country of each IP address.
        """
        if not isinstance(ip_addresses, pd.Series):
            raise AttributeError("ip_addresses must be a pandas Series")

        if ip_addresses is None or len(ip_addresses) == 0:
            return pd.DataFrame(columns=["org", "country"])

        original_frame = ip_addresses.to_frame(name="ip")

        # Get unique IP addresses
        unique_addresses = list(ip_addresses.unique())
        countries = []
        orgs = []

        for ip in unique_addresses:
            org, country = self.get_ip_infos(ip)
            orgs.append(org)
            countries.append(country)

        unique_frame = pd.DataFrame({"ip": unique_addresses, "org": orgs, "country": countries})

        # Merge the unique frame with the original frame so that
        # the original order is preserved
        merged_frame = pd.merge(original_frame, unique_frame, on="ip", how="left")
        return merged_frame

    def to_data_frame(self):
        """
        This function returns the cache as a DataFrame.
        """
        if len(self._cache_dict) == 0:
            return pd.DataFrame(columns=["ip", "org", "country"])

        # Convert the cache to a DataFrame
        cache_frame = pd.DataFrame.from_dict(
            self._cache_dict, orient='index', columns=["org", "country"])
        cache_frame.index.name = "ip"
        cache_frame.reset_index(inplace=True)
        return cache_frame

    def clear(self):
        """
        This function clears the cache.
        """
        self._cache_dict = {}
