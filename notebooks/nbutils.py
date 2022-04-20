"""
This module provides utility functions for the notebooks of
this library
"""

# Imports
import sys
import pandas as pd

# Fix possible import problems
sys.path.append("..")


def set_default_pd_options():
    """
    This functions sets default options for pandas.

    :return: None.
    """
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('display.max_rows', 10000)
