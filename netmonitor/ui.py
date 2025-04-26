"""
This module contains user interface elements for the netmonitor application.
"""

# Imports
import pandas as pd
from gi.repository import Gtk, GLib
from netmonitor import core


# Constants
_WINDOW_TITLE = "netmonitor"
_COLUMN_WIDTH = 100
_CONNECTION_COLUMNS = core.CONNECTION_COLUMNS + ['country', 'org']
_WINDOW_WIDTH = 1100
_WINDOW_HEIGHT = 550
_IP_CACHE_FILE = "data/ip_info_cache.json"


class DataFrameTable(Gtk.TreeView):
    """
    This class represents a table view for displaying a DataFrame.
    """
    def __init__(self, data_frame):
        super().__init__()
        self.data_frame = data_frame
        self._init_component()
        self._update_component()

    def set_data_frame(self, data_frame):
        """
        This method sets the DataFrame to be displayed in the table.

        :param data_frame: The DataFrame to be displayed.
        :return: None.
        """
        self.data_frame = data_frame
        self._update_component()

    def set_column_visibility(self, column_titles, visible):
        """
        This method sets the visibility of specific table columns.

        :param column_titles: A list of column titles to show or hide.
        :param visible: A boolean indicating whether to show (True) or hide (False) the columns.
        :return: None.
        """
        for column in self.get_columns():
            if column.get_title() in column_titles:
                column.set_visible(visible)

    def _update_component(self):
        """
        This method updates the component with the currently set DataFrame.

        :return: None.
        """
        # Clear the ListStore
        self.liststore.clear()

        # Append each row of the DataFrame to the ListStore
        for row in self.data_frame.itertuples(index=False):
            self.liststore.append(list(row))

    def _init_component(self):
        """
        This method initializes the component by creating a ListStore
        and setting up the columns.
        """
        # Create a ListStore with the same number of columns as the DataFrame
        self.liststore = Gtk.ListStore(*(str,) * len(self.data_frame.columns))

        # Wrap the ListStore in a TreeModelSort
        sorted_model = Gtk.TreeModelSort(model=self.liststore)
        self.set_model(sorted_model)

        # Create a column for each DataFrame column
        for i, column_title in enumerate(self.data_frame.columns):
            renderer = Gtk.CellRendererText()
            renderer.set_property("xalign", 1.0)
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            column.set_min_width(_COLUMN_WIDTH)
            self.append_column(column)


class WaitDialog(Gtk.Dialog):
    """
    This dialog shows a wait message while a process is running.
    """
    def __init__(self, parent):
        super().__init__(title="Processing", parent=parent, flags=Gtk.DialogFlags.MODAL)
        self.set_default_size(300, 100)

        # Add a label with the message
        label = Gtk.Label(label="Please wait...")
        self.get_content_area().add(label)
        self.show_all()

    def __enter__(self):
        """
        Enter the context manager and show the dialog.
        """
        self.show()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager and destroy the dialog.
        """
        self.destroy()

    def run_with_task(self, task, *args, **kwargs):
        """
        Run a task while showing the dialog.

        :param task: The function to execute.
        :param args: Positional arguments for the task.
        :param kwargs: Keyword arguments for the task.
        """
        def wrapped_task():
            try:
                task(*args, **kwargs)
            finally:
                self.destroy()
            return False  # Stop the idle loop

        GLib.timeout_add(50, wrapped_task)
        self.run()


class IpInfoCacheDialog(Gtk.Dialog):
    """
    This class represents a dialog for managing an IpInfoCache.
    """
    def __init__(self, ip_cache: core.IpInfoCache, parent=None):
        super().__init__(title="IP cache", parent=parent, flags=Gtk.DialogFlags.MODAL)
        self.set_default_size(750, 300)
        self.ip_cache = ip_cache
        self.cache_frame = self.ip_cache.to_data_frame()

        # Create a DataFrameTable to display the cache entries
        self.table = DataFrameTable(self.cache_frame)

        # Add a ScrolledWindow for the table
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.table)

        # Create a toolbar with the "Clear Cache" button
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        clear_button = Gtk.Button(label="Clear Cache")
        clear_button.connect("clicked", self._clear_cache)
        toolbar.pack_start(clear_button, False, False, 0)

        # Create a status bar with a centered label
        self.entries_label = Gtk.Label(label=f"Records: {len(self.cache_frame)}")
        file_label = Gtk.Label(label=f"File: {_IP_CACHE_FILE}")

        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_bar.pack_start(self.entries_label, True, True, 10)
        status_bar.pack_start(file_label, True, True, 10)

        # Add OK and Cancel buttons
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        # Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(toolbar, False, False, 0)  # Add toolbar at the top
        vbox.pack_start(scrolled_window, True, True, 0)
        vbox.pack_start(status_bar, False, False, 7)  # Add status bar at the bottom
        self.get_content_area().add(vbox)

        self.show_all()

    # pylint: disable=unused-argument
    # Argument is necessary for the function to work
    def _clear_cache(self, widget):
        """
        This function is called when the "Clear Cache" button is clicked.

        :param widget: The widget that was clicked.
        :return: None.
        """
        # Create a confirmation dialog
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            message_format="Are you sure you want to clear the cache?"
        )
        response = dialog.run()
        dialog.destroy()

        # If the user confirms, clear the cache
        if response == Gtk.ResponseType.YES:
            self.ip_cache.clear()
            self.cache_frame = self.ip_cache.to_data_frame()
            self.table.set_data_frame(self.cache_frame)
            self.entries_label.set_text(f"Records: {len(self.cache_frame)}")


class NetmonitorToolbar(Gtk.Box):
    """
    This class represents a toolbar with buttons and checkboxes for controlling
    the NetMonitorWindow.
    """
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Create a refresh button
        self.refresh_button = Gtk.Button(label="Refresh")

        # Create a checkbox for non-remote connections
        self.non_remote_checkbox = Gtk.CheckButton(label="Non-remote")

        # Create a checkbox for private connections
        self.private_checkbox = Gtk.CheckButton(label="Private")

        # Create a checkbox for local ips
        self.local_checkbox = Gtk.CheckButton(label="Local")

        # Create a checkbox for ip infos
        self.ip_infos_checkbox = Gtk.CheckButton(label="Remote Infos")

        # Create a button to manage the ip info cache
        self.cache_button = Gtk.Button(label="Cache...")

        # Create a button to export the current view to a CSV file
        self.export_button = Gtk.Button(label="Export...")

        # Add the buttons and checkboxes to the toolbar
        self.pack_start(self.refresh_button, False, False, 0)
        self.pack_start(self.non_remote_checkbox, False, False, 0)
        self.pack_start(self.private_checkbox, False, False, 0)
        self.pack_start(self.local_checkbox, False, False, 0)
        self.pack_start(self.ip_infos_checkbox, False, False, 0)
        self.pack_end(self.export_button, False, False, 0)
        self.pack_end(self.cache_button, False, False, 0)


class NetmonitorWindow(Gtk.Window):
    """
    This class represents the main window of the netmonitor application.
    """
    def __init__(self):
        super().__init__(title=_WINDOW_TITLE)
        self.set_default_size(_WINDOW_WIDTH, _WINDOW_HEIGHT)

        # Create an empty connections frame
        self.connections = pd.DataFrame(columns=_CONNECTION_COLUMNS)
        self.filtered_connections = self.connections.copy()
        self.ip_cache = core.IpInfoCache()

        # Create a table to show the connections
        self.table = DataFrameTable(self.filtered_connections)

        # When a row is double-clicked open a dialog
        # showing connection details
        self.table.connect("row-activated", self._on_row_activated)

        # Add the TreeView to a ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.table)

        # Create the control panel and register events
        self.toolbar = NetmonitorToolbar()

        self.toolbar.refresh_button.connect(
            "clicked", self._refresh_button_clicked)

        self.toolbar.non_remote_checkbox.connect(
            "toggled", self._non_remote_toggled)

        self.toolbar.private_checkbox.connect(
            "toggled", self._private_toggled)

        self.toolbar.local_checkbox.connect(
            "toggled", self._local_toggled)

        self.toolbar.ip_infos_checkbox.connect(
            "toggled", self._ip_infos_toggled)

        self.toolbar.cache_button.connect(
            "clicked", self._show_cache_dialog)

        self.toolbar.export_button.connect(
            "clicked", self._export_to_csv)

        # Create a vertical box and add the horizontal box and scrolled window to it
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(scrolled_window, True, True, 0)

        # Add the vertical box to the main window
        self.add(vbox)

        # Try to load the ip infos cache
        try:
            self.ip_cache.load_from_json(_IP_CACHE_FILE)
        except FileExistsError:
            # Write a warning message
            print("Could not load the ip infos cache. Creating a new one.")

        # Get connections and update the component
        self._load_connections()
        self._update_component()

    # pylint: disable=unused-argument
    # Arguments are necessary for the function to work
    def _on_row_activated(self, widget, path, column):
        """
        This function is called when a row is double-clicked.

        :param widget: The widget that was double-clicked.
        :param path: The path of the row that was double-clicked.
        :param column: The column that was double-clicked.
        :return: None.
        """
        # Convert the sorted path to the original path
        model = self.table.get_model()
        original_path = model.convert_path_to_child_path(path)

        # Retrieve the original index from the original path
        original_index = original_path.get_indices()[0]

        # Show the details dialog for the correct row
        self._show_details_dialog(original_index)

    # pylint: disable=unused-argument
    # Argument is necessary for the function to work
    def _refresh_button_clicked(self, widget):
        """
        This function is called when the refresh button is clicked.

        :param widget: The widget that was clicked.
        :return: None.
        """
        # Get connections and update the component
        with WaitDialog(parent=self) as dialog:
            self._load_connections()
            dialog.run_with_task(self._update_component)

    def _non_remote_toggled(self, widget):
        """
        This function is called when the non-remote checkbox is toggled.

        :param widget: The widget that was toggled.
        :return: None.
        """
        # Update the component
        self._update_component()

    def _private_toggled(self, widget):
        """
        This function is called when the private checkbox is toggled.

        :param widget: The widget that was toggled.
        :return: None.
        """
        # Update the component
        self._update_component()

    def _local_toggled(self, widget):
        """
        This function is called when the local IPs checkbox is toggled.

        :param widget: The widget that was toggled.
        :return: None.
        """
        # Update the component
        self._update_component()

    def _ip_infos_toggled(self, widget):
        """
        This function is called when the IP infos checkbox is toggled.

        :param widget: The widget that was toggled.
        :return: None.
        """
        # Update the component
        with WaitDialog(parent=self) as dialog:
            dialog.run_with_task(self._update_component)

    def _show_cache_dialog(self, widget):
        """
        This function is called when the cache button is clicked.

        :param widget: The widget that was clicked.
        :return: None.
        """
        cache_copy = self.ip_cache.copy()
        dialog = IpInfoCacheDialog(cache_copy, self)
        response = dialog.run()
        dialog.destroy()

        # If the user clicked OK, update the main cache
        if response == Gtk.ResponseType.OK:
            # Update the main cache with the modified copy
            self.ip_cache = cache_copy
            self.ip_cache.save_to_json(_IP_CACHE_FILE)

    def _export_to_csv(self, widget):
        """
        This function exports the current view to a CSV file.

        :param widget: The widget that was clicked.
        :return: None.
        """
        dialog = Gtk.FileChooserDialog(
            title="Save CSV", parent=self, action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT)

        filter_csv = Gtk.FileFilter()
        filter_csv.set_name("CSV files")
        filter_csv.add_pattern("*.csv")
        dialog.add_filter(filter_csv)
        dialog.set_do_overwrite_confirmation(True)

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            self.filtered_connections.to_csv(filename, index=False)

        dialog.destroy()

    def _show_details_dialog(self, row_number):
        """
        This function shows a dialog with connection details.

        :param row_number: The row number of the connection.
        :return: None.
        """
        # Get the selected row
        row = self.filtered_connections.iloc[row_number]

        # Get connection details
        org, country = core.get_ip_infos(row['rip'])
        org = org if org else ""
        country = country if country else ""

        # Create the details dialog and show it
        dialog = self._create_details_dialog(row, org, country)
        dialog.run()
        dialog.destroy()

    def _create_details_dialog(self, row, org, country):
        """
        This function creates a dialog with connection details for a
        selected row.

        :param row: The selected row.
        :param org: The organization name.
        :param country: The country name.
        :return: The created dialog.
        """
        dialog = Gtk.Dialog(title="Connection Details", parent=self, flags=0)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)

        labels = [
            Gtk.Label(label=f"PID: {row['pid']}", selectable=True),
            Gtk.Label(label=f"Process: {row['proc']}", selectable=True),
            Gtk.Label(label=f"Status: {row['status']}", selectable=True),
            Gtk.Label(label=f"Local IP: {row['lip']}", selectable=True),
            Gtk.Label(label=f"Local Port: {row['lport']}", selectable=True),
            Gtk.Label(label=f"Remote IP: {row['rip']}", selectable=True),
            Gtk.Label(label=f"Remote Port: {row['rport']}", selectable=True),
            Gtk.Label(label=f"Organization: {org}", selectable=True),
            Gtk.Label(label=f"Country: {country}", selectable=True)
        ]

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        for i, label in enumerate(labels):
            vbox.pack_start(label, False, False, 0)
            # Check by index whether to add a separator
            if i in (2, 4):
                separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                vbox.pack_start(separator, False, False, 0)

        dialog.get_content_area().add(vbox)
        dialog.set_default_size(350, 300)
        dialog.show_all()

        return dialog

    def _load_connections(self):
        """
        This function loads the connections DataFrame from the core module.

        The connections are sorted by the 'rip' column in descending order.

        :return: None.
        """
        # Get connections and update the component
        self.connections = core.get_connections()

        # Format date column so that we can see day and time until seconds
        self.connections['date'] = self.connections['date'].dt.strftime('%H:%M:%S')

        # Convert all DataFrame values to strings
        self.connections = self.connections.astype(str)

        # Replace None and nan values with empty strings
        self.connections = self.connections.replace('None', '')
        self.connections = self.connections.replace('-1', '')

        # Sort by rip column in descending order
        self.connections = self.connections.sort_values(by='rip', ascending=False)

    def _update_component(self):
        """
        This function updates the component on basis of the connections DataFrame.

        :return: None.
        """
        # Filter the connections based on the checkboxes state
        self.filtered_connections = self.connections.copy()

       # non-remote ips
        if not self.toolbar.non_remote_checkbox.get_active():
            self.filtered_connections = self.filtered_connections[
                self.filtered_connections['rip'].str.len() > 0]

        # private ips
        if not self.toolbar.private_checkbox.get_active():
            self.filtered_connections = self.filtered_connections[
                self.filtered_connections['rpriv'] == 'False']

        self.table.set_column_visibility(
            ["rpriv"], self.toolbar.private_checkbox.get_active())

        # local ips
        self.table.set_column_visibility(
            ["lip", "lport"], self.toolbar.local_checkbox.get_active())

        # Rest indexes
        self.filtered_connections.reset_index(drop=True, inplace=True)

        # ip infos
        if self.toolbar.ip_infos_checkbox.get_active():
            ip_infos = self.ip_cache.match_ip_infos(self.filtered_connections["rip"])
            ip_infos = ip_infos.astype(str)
            ip_infos = ip_infos.replace('None', '')
            self.filtered_connections["country"] = ip_infos["country"]
            self.filtered_connections["org"] = ip_infos["org"]
            self.ip_cache.save_to_json(_IP_CACHE_FILE)
        else:
            self.filtered_connections["country"] = ''
            self.filtered_connections["org"] = ''

        self.table.set_column_visibility(
            ["country", "org"], self.toolbar.ip_infos_checkbox.get_active())

        # Update the table with the filtered DataFrame
        self.table.set_data_frame(self.filtered_connections)

        # Visualize that the column 'rip' is sorted
        self.table.get_column(self.filtered_connections.columns.get_loc(
            'rip')).set_sort_indicator(True)
        self.table.get_column(self.filtered_connections.columns.get_loc(
            'rip')).set_sort_order(Gtk.SortType.DESCENDING)
