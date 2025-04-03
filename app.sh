#!/bin/bash
# This script runs the netmonitor application in its conda environment.
# Warnings are suppressed by redirecting stderr to /dev/null.
# To debug the application run app.py directly.
conda run --no-capture-output -n netmonitor python app.py 2>/dev/null