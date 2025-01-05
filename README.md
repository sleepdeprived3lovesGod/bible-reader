# Bible Reader

A Bible reader application with text-to-speech functionality and read verses tracking, designed to help you finally finish the Bible.

![Bible Reader GUI](https://i.imgur.com/vqhyUKy.png)

## Features
- **Text-to-Speech:** Read verses aloud with high-quality text-to-speech.
- **Verse Tracking:** Mark verses as read and keep track of your reading progress.
- **MP3 Creation:** Create MP3 files for selected verses to listen on your phone.
- **Chapter Notes:** Save and load notes for each chapter to enhance your study.
- **Customization:** Adjust text size and voice preferences.
- **Skip Read Verses:** Skip verses you've already read to focus on finishing the Bible.
- **Multiple Translations:** Choose from different free Bible translations (NET, KJV, WEB).

## Installation

### Prerequisites

1. **Python 3.11.9:**
   - Download the installer from [Python 3.11.9](https://www.python.org/downloads/release/python-3119/).
   - Run the installer and ensure to check the box that says "Add Python to PATH" before clicking "Install Now."

2. **ffmpeg 7.0.0.20240429:**
   - Download the installer from [ffmpeg 7.0.0.20240429](https://github.com/icedterminal/ffmpeg-installer/releases/tag/7.0.0.20240429).
   - Run the installer and follow the instructions.
   - **Add ffmpeg to PATH:**
     - Open the Start Menu and search for "Environment Variables."
     - Click on "Edit the system environment variables."
     - In the System Properties window, click on the "Environment Variables" button.
     - In the Environment Variables window, find the "Path" variable in the "System variables" section and click "Edit."
     - Click "New" and add the path to the `bin` directory of your ffmpeg installation (e.g., `C:\ffmpeg\bin`).
     - Click "OK" to close all windows.

3. **Git:**
   - Download and install Git from [Git for Windows](https://gitforwindows.org/).
   - Follow the installation instructions to ensure Git is added to your system's PATH.

### Steps

1. **Clone the Repository:**
   - Open a command prompt or terminal.
   - Navigate to the directory where you want to clone the repository.
   - Run the following command to clone the repository:
     ```sh
     git clone https://github.com/sleepdeprived3lovesGod/bible-reader.git
     ```

2. **Navigate to the Project Directory:**
   - Change into the project directory:
     ```sh
     cd bible-reader
     ```

3. **Run the Installer:**
   - Run the `windows_install.bat` file to set up the virtual environment and install dependencies:
     ```sh
     windows_install.bat
     ```
   - You might need to run it as Administrator to ensure all permissions are correctly set.

4. **Start the Application:**
   - Run the `start.bat` file to start the Bible Reader:
     ```sh
     start.bat
     ```

## Usage

- **Navigation:**
  - Use the dropdown menus to select the book, chapter, and verse you want to read.
  - Click the "Read" button to hear the verse read aloud.
  - Use the "Pause" button to pause the reading.
  - Click the "Next Unread" button to navigate to the next unread verse.

- **Customization:**
  - Adjust the text size using the "+" and "-" buttons.
  - Change the voice using the voice dropdown menu.
  - Skip read verses by checking the "Skip read verses" checkbox.

- **Notes:**
  - Write and save notes for each chapter using the notes section.
  - Copy notes to the clipboard using the "Copy Notes" button.

- **MP3 Creation:**
  - Click the "Create MP3" button to create an MP3 file for a selected range of verses.

- **Reset Options:**
  - Reset chapter history, notes, preferences, or all data using the reset buttons.

- **Translation Selection:**
  - Use the translation dropdown menu to switch between different Bible translations (NET, KJV, WEB).
  - Ensure you comply with the usage guidelines for each translation, especially the NET Bible text.

## Copyright

NET Scripture quoted by permission. Quotations designated (NET) are from the NET Bible® copyright ©1996, 2019 by Biblical Studies Press, L.L.C. https://netbible.com All rights reserved.
KJV The King James Version is public domain everywhere except the United Kingdom. If you are using this in the United Kingdom then please ensure that you have permission from the crown.
WEB The world English Bible is public domain.

## Troubleshooting

### Common Issues

- **Python Not Found:**
  - Ensure Python 3.11.9 is installed and added to your system's PATH.
  - Verify this by opening a command prompt and typing `python --version`. It should display the version number.

- **ffmpeg Not Found:**
  - Ensure ffmpeg 7.0.0.20240429 is installed and added to your system's PATH.
  - Verify this by opening a command prompt and typing `ffmpeg -version`. It should display the version number.

- **Module Not Found:**
  - Run the `windows_install.bat` file to install all dependencies.

- **Other Problems and Updating from Older Versions:**
  - Delete `config.ini` and let it create a new one.
