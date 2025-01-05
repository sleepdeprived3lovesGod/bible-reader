#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Activate virtual environment
source "venv/bin/activate"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    exit 1
fi

# Determine the Python version to use
if command_exists python3.11; then
    PYTHON_EXEC="python3.11"
else
    PYTHON_EXEC="python3"
fi

# Check if tkinter is installed
if ! "$PYTHON_EXEC" -c "import tkinter" &> /dev/null; then
    echo "tkinter is not installed. Installing tkinter..."
    sudo apt update
    sudo apt install -y python3-tk
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install tkinter."
        exit 1
    fi
fi

# Run the Bible Reader application
"$PYTHON_EXEC" "Bible.py"

# Wait for user input before closing
read -p "Press [Enter] key to continue..."
