"""
This module contains user interface elements for the netmonitor application.
"""

# Imports
import pandas as pd
from gi.repository import Gtk
from netmonitor import core


# Constants
_WINDOW_TITLE = "netmonitor"
_COLUMN_WIDTH = 100
_WINDOW_WIDTH = len(core.CONNECTION_COLUMNS * _COLUMN_WIDTH) * 1.2
_WINDOW_HEIGHT = 550
_REFRESH_TITLE = "Refresh"


class DataFrameTable(Gtk.TreeView):
    """
    This class represents a table view for displaying a DataFrame.
    """
    def __init__(self, data_frame):
        super().__init__()
        self.data_frame = data_frame
        self._init_component()

    def set_data_frame(self, data_frame):
        """
        Set the DataFrame to be displayed in the table.

        :param data_frame: The DataFrame to be displayed.
        """
        self.data_frame = data_frame
        self._update_component()

    def _update_component(self):
        """
        Update the component with the current DataFrame data.
        """
        # Clear the ListStore
        self.liststore.clear()

        # Append each row of the DataFrame to the ListStore
        for row in self.data_frame.itertuples(index=False):
            self.liststore.append(list(row))

    def _init_component(self):
        """
        Set up the user interface for the DataFrame table.
        """
        # Create a column for each DataFrame column
        for i, column_title in enumerate(self.data_frame.columns):
            # Create a ListStore with the same number of columns as the DataFrame
            self.liststore = Gtk.ListStore(*(str,) * len(self.data_frame.columns))
            self.set_model(self.liststore)

            renderer = Gtk.CellRendererText()
            renderer.set_property("xalign", 1.0)
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            column.set_min_width(_COLUMN_WIDTH)
            self.append_column(column)


class NetmonitorWindow(Gtk.Window):
    """
    This class represents the main window of the netmonitor application.
    """
    def __init__(self):
        super().__init__(title=_WINDOW_TITLE)
        self.set_default_size(_WINDOW_WIDTH, _WINDOW_HEIGHT)

        # Create an empty connections frame
        self.connections = pd.DataFrame(columns=core.CONNECTION_COLUMNS)
        self.filtered_connections = self.connections.copy()

        # Create a table to show the connections
        self.table = DataFrameTable(self.filtered_connections)

        # When a row is double-clicked open a dialog
        # showing connection details
        self.table.connect("row-activated", self._on_row_activated)

        # Add the TreeView to a ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.table)

        # Create a button to refresh the table
        refresh_button = Gtk.Button(label=_REFRESH_TITLE)
        refresh_button.connect("clicked", self._refresh_button_clicked)

        # Create a checkbox for non-remote connections
        self.non_remote_checkbox = Gtk.CheckButton(label="Non-remote")
        self.non_remote_checkbox.connect("toggled", self._non_remote_toggled)

        # Create a checkbox for private connections
        self.private_checkbox = Gtk.CheckButton(label="Private")
        self.private_checkbox.connect("toggled", self._private_toggled)

        # Create a button to export the current view to a CSV file
        export_button = Gtk.Button(label="Export CSV")
        export_button.connect("clicked", self._export_to_csv)

        # Create a horizontal box and add the button to it
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.pack_start(refresh_button, False, False, 0)
        hbox.pack_start(self.non_remote_checkbox, False, False, 0)
        hbox.pack_start(self.private_checkbox, False, False, 0)
        hbox.pack_end(export_button, False, False, 0)

        # Create a vertical box and add the horizontal box and scrolled window to it
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(hbox, False, False, 0)
        vbox.pack_start(scrolled_window, True, True, 0)

        # Add the vertical box to the main window
        self.add(vbox)

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
        # Get the selected row number and show dialog
        row_number = path.get_indices()[0]
        self._show_details_dialog(row_number)

    # pylint: disable=unused-argument
    # Argument is necessary for the function to work
    def _refresh_button_clicked(self, widget):
        """
        This function is called when the refresh button is clicked.

        :param widget: The widget that was clicked.
        :return: None.
        """
        # Get connections and update the component
        self._load_connections()
        self._update_component()

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
        if not self.non_remote_checkbox.get_active():
            self.filtered_connections = self.filtered_connections[
                self.filtered_connections['rip'].str.len() > 0]

        # private ips
        if not self.private_checkbox.get_active():
            self.filtered_connections = self.filtered_connections[
                self.filtered_connections['rpriv'] == 'False']

        # Update the table with the filtered DataFrame
        self.table.set_data_frame(self.filtered_connections)

        # Visualize that the column 'rip' is sorted
        self.table.get_column(self.filtered_connections.columns.get_loc(
            'rip')).set_sort_indicator(True)
        self.table.get_column(self.filtered_connections.columns.get_loc(
            'rip')).set_sort_order(Gtk.SortType.DESCENDING)
