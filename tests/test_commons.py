"""
This module contains test cases for the module netmonitor.commons.
"""


# Imports
import time
from multiprocessing import Process
import psutil
import netmonitor.commons as com


def test_connection_snapshot():
    """
    Testcase for the function get_connection_snapshot.

    :return: None.
    """
    con_frame1 = com.get_connection_snapshot()
    assert con_frame1 is not None

    # Check column names
    assert "timestamp" in con_frame1.columns
    assert "raddr" in con_frame1.columns
    assert "raddr_port" in con_frame1.columns
    assert "pid" in con_frame1.columns
    assert "status" in con_frame1.columns

    if len(con_frame1) > 0:
        # Check timestamps
        assert len(con_frame1["timestamp"].unique()) == 1

        # Check one connection
        status_list = [psutil.CONN_CLOSE, psutil.CONN_CLOSE_WAIT,
                       psutil.CONN_CLOSING, psutil.CONN_ESTABLISHED,
                       psutil.CONN_FIN_WAIT1, psutil.CONN_FIN_WAIT2,
                       psutil.CONN_LAST_ACK, psutil.CONN_LISTEN,
                       psutil.CONN_NONE, psutil.CONN_SYN_RECV,
                       psutil.CONN_SYN_SENT, psutil.CONN_TIME_WAIT]

        assert con_frame1["raddr"][0] is not None
        assert con_frame1["raddr_port"][0] > 0
        assert con_frame1["pid"][0] > 0
        assert con_frame1["status"][0] in status_list


def test_get_traffic_snapshot():
    """
    Testcase for the function get_traffic_snapshot.

    :return: None.
    """
    # Get first stats frame
    stats_frame1 = com.get_traffic_snapshot()

    # Check that frame is not empty
    assert stats_frame1 is not None
    assert len(stats_frame1) > 0

    # Check column names
    assert "timestamp" in stats_frame1.columns
    assert "network_interface" in stats_frame1.columns
    assert "packets_recv" in stats_frame1.columns
    assert "packets_sent" in stats_frame1.columns
    assert "bytes_recv" in stats_frame1.columns
    assert "bytes_sent" in stats_frame1.columns

    # Check timestamps
    assert len(stats_frame1["timestamp"].unique()) == 1

    # Check one network
    assert stats_frame1["network_interface"][0] is not None
    assert stats_frame1["packets_recv"][0] >= 0
    assert stats_frame1["packets_sent"][0] >= 0
    assert stats_frame1["bytes_recv"][0] >= 0
    assert stats_frame1["bytes_sent"][0] >= 0

    # Compare to second stats frame
    time.sleep(0.01)
    stats_frame2 = com.get_traffic_snapshot()

    assert stats_frame1["timestamp"][0] < stats_frame2["timestamp"][0]
    assert stats_frame1["packets_recv"][0] <= stats_frame2["packets_recv"][0]
    assert stats_frame1["packets_sent"][0] <= stats_frame2["packets_sent"][0]
    assert stats_frame1["bytes_recv"][0] <= stats_frame2["bytes_recv"][0]
    assert stats_frame1["bytes_sent"][0] <= stats_frame2["bytes_sent"][0]

    # Check total statistics
    stats_frame3 = com.get_traffic_snapshot(pernic=False)
    assert(len(stats_frame3)) == 1
    assert stats_frame3["network_interface"][0] == "all"


def test_get_process_name():
    """
    Testcase for the function get_process_name.

    :return: None.
    """
    proc = Process()
    assert com.get_process_name(proc.pid).startswith("py")
    assert com.get_process_name(9999999) is None


def test_get_local_ips():
    """
    Testcase for the function get_local_ips.

    :return: None.
    """
    ips = com.get_local_ips()
    assert ips is not None
    assert len(ips) > 0
    assert str(ips[0]).replace(".", "0").isdigit()


def test_get_ip_infos():
    """
    Testcase for the function get_ip_infos.

    :return: None.
    """
    # Get IP infos for Google
    org, country = com.get_ip_infos("172.217.0.0")
    assert org.find("Google") > 0
    assert country == "US"

    # Get IP infos for Microsoft
    org, country = com.get_ip_infos("20.54.232.160")
    assert org.find("Microsoft") > 0
    assert country == "NL"

    # Illegal IP address
    org, country = com.get_ip_infos("20.54.232.x")
    assert org is None
    assert country is None
