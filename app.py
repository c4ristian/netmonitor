#!/usr/bin/env python3
"""
This module runs the user interface for the netmonitor application.
"""

# Imports
import gi
# pylint: disable=wrong-import-position
# this is needed to use Gtk3
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from netmonitor.ui import NetmonitorWindow


def _main():
    """
    This function runs the application.

    :return: None.
    """
    # Create the main window
    win = NetmonitorWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    _main()
