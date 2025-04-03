#!/bin/bash
# This script runs the netmonitor application in its conda environment.

# Initialize environment variables
export PATH="$HOME/miniconda3/bin:$PATH"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
export DISPLAY=$DISPLAY

# Set working directory
cd "$(dirname "$0")" || exit 1

# Activate the conda environment and run the application
conda run --no-capture-output -n netmonitor python app.py