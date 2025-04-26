#!/usr/bin/env python3
"""
This module runs the user interface for the netmonitor application.
"""

# Imports
import os
import gi
# pylint: disable=wrong-import-position
# this is needed to use Gtk3
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from netmonitor.ui import NetmonitorWindow


class App:
    """
    This class models the application and handles the splash screen
    and the main window.
    """
    def __init__(self):
        self.splash_window = None

    def show_splash_screen(self):
        """
        This method creates and displays the splash screen.
        """
        self.splash_window = Gtk.Window()
        self.splash_window.set_decorated(False)  # Remove window borders
        self.splash_window.set_position(Gtk.WindowPosition.CENTER)

        # Load the splash image from the data subfolder
        splash_path = os.path.join("data", "splash.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(splash_path)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.splash_window.add(image)

        self.splash_window.show_all()

        # Close splash screen after a while and show the main window
        GLib.timeout_add(2000, self.show_main_window)

    def show_main_window(self):
        """
        This method closes the splash screen and opens the main window.
        """
        self.splash_window.destroy()  # Close the splash screen
        win = NetmonitorWindow()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()

    def run(self):
        """
        This method runs the main loop of the application.
        """
        self.show_splash_screen()
        Gtk.main()


# Main block
if __name__ == "__main__":
    app = App()
    app.run()
