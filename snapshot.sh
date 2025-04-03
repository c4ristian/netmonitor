#!/bin/bash
# This script runs the snapshot utility in its conda environment.
conda run -n netmonitor python snapshot.py "$@"