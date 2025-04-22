"""
This module contains test cases for the con module.
"""

# Imports
from multiprocessing import Process
import pandas as pd
import psutil
import pytest

from netmonitor import core


# pylint: disable=protected-access
# Access to protected members is okay for testing
def test_extract_ip():
    """
    This function tests the _extract_ip function.

    :return: None.
    """
    assert core._extract_ip(None) is None
    assert core._extract_ip(()) is None
    assert core._extract_ip((1,)) == 1
    assert core._extract_ip(('ff::1',)) == "ff::1"
    assert core._extract_ip(('192.11.80.1', 40)) == '192.11.80.1'


def test_extract_port():
    """
    This function tests the _extract_port function.

    :return: None.
    """
    assert core._extract_port(None) == -1
    assert core._extract_port(()) == -1
    assert core._extract_port(('ff::1',)) == -1
    assert core._extract_port((None,1)) == 1
    assert core._extract_port(('192.11.80.1', 40)) == 40
    assert core._extract_port(('192.11.80.1', 'ABC')) == 'ABC'


def test_is_private_ip():
    """
    Testcase for the function is_private_ip.

    :return: None.
    """
    private_ips = ["127.0.0.1", "192.168.8.100", "169.254.153.26"]
    assert core.is_private_ip("127.0.0.1", private_ips)
    assert core.is_private_ip("192.168.8.100", private_ips)
    assert core.is_private_ip("169.254.153.26", private_ips)
    assert core.is_private_ip("::ffff:169.254.153.26", private_ips)
    assert core.is_private_ip(list(core.get_private_ips())[0])

    assert not core.is_private_ip("169.254.153.01", private_ips)
    assert not core.is_private_ip("", private_ips)
    assert not core.is_private_ip(None, private_ips)


def test_get_private_ips():
    """
    Testcase for the function get_private_ips.

    :return: None.
    """
    ips = list(core.get_private_ips())
    assert ips is not None
    assert len(ips) > 0
    assert str(ips[0]).replace(".", "0").isdigit()


def test_get_connections():
    """
    Testcase for the function get_connections.

    :return: None.
    """
    # Get connections
    connections = core.get_connections()

    # Check data frame
    assert connections is not None
    assert isinstance(connections, pd.DataFrame)

    # Check columns
    assert len(connections.columns) == len(core.CONNECTION_COLUMNS)
    assert all(col in connections.columns for col in
               core.CONNECTION_COLUMNS)

    # Check specific columns
    if len(connections) > 0:
        # Check timestamps
        assert len(connections["date"].unique()) == 1

        # Check one connection
        status_list = [psutil.CONN_CLOSE, psutil.CONN_CLOSE_WAIT,
                       psutil.CONN_CLOSING, psutil.CONN_ESTABLISHED,
                       psutil.CONN_FIN_WAIT1, psutil.CONN_FIN_WAIT2,
                       psutil.CONN_LAST_ACK, psutil.CONN_LISTEN,
                       psutil.CONN_NONE, psutil.CONN_SYN_RECV,
                       psutil.CONN_SYN_SENT, psutil.CONN_TIME_WAIT]

        assert connections["pid"][0] >= -1
        assert connections["status"][0] in status_list
        assert connections["lport"][0] >= -1
        assert connections["rport"][0] >= -1
        assert connections["rpriv"][0] in (True, False)


def test_get_process_name():
    """
    Testcase for the function get_process_name.

    :return: None.
    """
    # Create a new process with name "test_process"
    process = Process()

    try:
        # Start the process
        process.start()
        pid = process.pid

        # Check if the pid is valid
        assert pid is not None
        assert isinstance(pid, int)
        assert pid > 0

        # Test function
        assert core.get_process_name(pid) is not None
        assert core.get_process_name(pid).startswith("py")
        assert core.get_process_name(-1) is None
        assert core.get_process_name(999999) is None
    finally:
        process.terminate()
        process.join()


def test_get_ip_infos():
    """
    Testcase for the function get_ip_infos.

    :return: None.
    """
    # Get IP infos for Google
    org, country = core.get_ip_infos("172.217.0.0")
    assert org.find("Google") > 0
    assert country == "US"

    org, country = core.get_ip_infos("2a00:1450:4013:c04::54")
    assert org.find("Google") > 0
    assert country == "NL"

    # Get IP infos for Microsoft
    org, country = core.get_ip_infos("20.54.232.160")
    assert org.find("Microsoft") > 0
    assert country == "NL"

    # Invalid addresses
    org, country = core.get_ip_infos("20.54.232.x")
    assert org is None
    assert country is None

    org, country = core.get_ip_infos("")
    assert org is None
    assert country is None


def test_match_ip_infos():
    """
    Testcase for the function match_ip_infos.

    :return: None.
    """
    # One correct result
    ip_addresses = pd.Series(["172.217.0.0"])
    ip_infos = core.match_ip_infos(ip_addresses)

    assert ip_infos is not None
    assert isinstance(ip_infos, pd.DataFrame)
    assert len(ip_infos) == 1
    assert len(ip_infos.columns) == 3
    assert all(col in ip_infos.columns for col in ["ip", "org", "country"])

    first_row = ip_infos.iloc[0]
    assert first_row["ip"] == "172.217.0.0"
    assert first_row["org"].find("Google") > 0
    assert first_row["country"] == "US"

    # Multiple correct results
    ip_addresses = pd.Series(["20.54.232.160", "2a00:1450:4013:c04::54", "1111"])
    ip_infos = core.match_ip_infos(ip_addresses)

    assert ip_infos is not None
    assert len(ip_infos) == 3

    first_row = ip_infos.iloc[0]
    assert first_row["ip"] == "20.54.232.160"
    assert first_row["org"].find("Microsoft") > 0
    assert first_row["country"] == "NL"

    second_row = ip_infos.iloc[1]
    assert second_row["ip"] == "2a00:1450:4013:c04::54"
    assert second_row["org"].find("Google") > 0
    assert second_row["country"] == "NL"

    third_row = ip_infos.iloc[2]
    assert third_row["ip"] == "1111"
    assert third_row["org"] is None
    assert third_row["country"] is None

    # Error cases
    with pytest.raises(AttributeError):
        core.match_ip_infos("172.11.80.1")

    with pytest.raises(AttributeError):
        core.match_ip_infos(None)
