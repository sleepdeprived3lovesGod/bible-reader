#!/bin/bash

# Store the current directory
INSTALL_DIR=$(pwd)
echo "Installing in: $INSTALL_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determine the Python version
if command_exists python3.11; then
    PYTHON_EXEC="python3.11"
    PIP_EXEC="pip3.11"
    PYTHON_DEV_PACKAGE="python3.11-dev"
    echo "Using Python 3.11"
elif command_exists python3; then
    PYTHON_EXEC="python3"
    PIP_EXEC="pip3"
    PYTHON_VERSION=$($PYTHON_EXEC --version | cut -d ' ' -f 2 | cut -d '.' -f 1-2)
    PYTHON_DEV_PACKAGE="python${PYTHON_VERSION}-dev"
    echo "Using default Python 3 ($PYTHON_VERSION)"
else
    echo "ERROR: No Python installation found. Please install Python from https://www.python.org/"
    exit 1
fi

# Update package list and install Python and pip if not already installed
if [ "$PYTHON_EXEC" == "python3.11" ]; then
    echo "Updating package list and installing Python 3.11 and pip..."
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3-pip "$PYTHON_DEV_PACKAGE"
else
    echo "Updating package list and installing python3-venv and $PYTHON_DEV_PACKAGE..."
    sudo apt update
    sudo apt install -y python3-venv "$PYTHON_DEV_PACKAGE"
fi

# Install build tools, ALSA development libraries, ffmpeg, and gcc
echo "Installing build tools, ALSA development libraries, ffmpeg, and gcc..."
sudo apt install -y build-essential libasound2-dev ffmpeg

# Create virtual environment with the detected Python
echo "Creating virtual environment in: $INSTALL_DIR/venv"
"$PYTHON_EXEC" -m venv "$INSTALL_DIR/venv"
if [ ! -d "$INSTALL_DIR/venv/bin" ]; then
    echo "ERROR: Failed to create virtual environment."
    exit 1
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment..."
source "$INSTALL_DIR/venv/bin/activate"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    exit 1
fi

echo "Upgrading pip..."
"$PIP_EXEC" install --upgrade pip
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to upgrade pip."
    exit 1
fi

# Install build tools and dependencies
echo "Installing build tools and dependencies..."
"$PIP_EXEC" install wheel setuptools
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install build tools."
    exit 1
fi

# Install PortAudio
echo "Installing PortAudio..."
sudo apt install -y portaudio19-dev
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install PortAudio."
    exit 1
fi

# Install pyaudio using pip
echo "Installing pyaudio using pip..."
"$PIP_EXEC" install pyaudio
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install pyaudio."
    exit 1
fi

# Install other dependencies
echo "Installing other dependencies..."
"$PIP_EXEC" install pandas edge-tts pydub pyperclip
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

# Create start.sh with relative paths
echo "Creating start.sh..."
echo "#!/bin/bash" > "$INSTALL_DIR/start.sh"
echo "source \"venv/bin/activate\"" >> "$INSTALL_DIR/start.sh"
echo "\"$PYTHON_EXEC\" \"Bible.py\"" >> "$INSTALL_DIR/start.sh"
echo "read -p \"Press [Enter] key to continue...\"" >> "$INSTALL_DIR/start.sh"

# Make start.sh executable
chmod +x "$INSTALL_DIR/start.sh"

echo
echo "Installation Summary:"
echo "-------------------"
echo "Virtual Environment: $INSTALL_DIR/venv"
echo "Start Script: $INSTALL_DIR/start.sh"
echo
echo "Setup complete! You can now run the Bible Reader using the start.sh file."
echo
