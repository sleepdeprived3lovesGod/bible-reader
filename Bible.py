# This script is a Bible reader application that reads the Bible to the user and keeps track of which parts have already been read.
# It uses a graphical user interface (GUI) built with Tkinter, and it leverages the edge_tts library for text-to-speech functionality.
# The application allows users to navigate through the Bible, read verses, mark sections as completed, and save notes for each chapter.
# It also provides options to create MP3 files of selected verses and reset reading history and notes.

import tkinter as tk
from tkinter import ttk
import pandas as pd
import edge_tts
import os
import csv
import asyncio
import pyaudio
import wave
import threading
from pydub import AudioSegment
import configparser
from tkinter import messagebox
import pyperclip
from tkinter import filedialog
from datetime import datetime
from tkinter import Toplevel, Label, Button, StringVar, IntVar
from tkinter.ttk import Progressbar
import time

class BibleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bible Reader")
        self.geometry("1000x700")

        # Constants
        self.default_voice = "en-US-SteffanNeural"
        self.default_skip_read_verses = False
        self.default_text_size = 12
        self.default_translation = "net.csv"

        # Initialize settings
        self.config_file = "config.ini"
        self.load_settings()

        # Initialize storage files
        self.read_verses_file = "read_verses.csv"
        self.notes_file = "notes.csv"
        self.load_storage_files()

        # Initialize the current translation
        self.current_translation = "net.csv"
        self.load_bible_data()

        # Create a list of full book names for the dropdown
        self.full_book_names = self.books_data["Full Book Name"].tolist()

        # === Navigation Controls ===
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=0, column=0, columnspan=3, pady=10)

        # Create MP3 Button moved to the left of the Mark Section Completed button
        self.create_mp3_button = ttk.Button(nav_frame, text="Create MP3", command=self.create_mp3)
        self.create_mp3_button.grid(row=0, column=0, padx=5)

        # Mark Section Completed Button
        self.mark_section_button = ttk.Button(nav_frame, text="Mark Section Completed",
                                            command=self.create_mark_section_dialog)
        self.mark_section_button.grid(row=0, column=1, padx=5)

        # Book selection
        self.book_label = ttk.Label(nav_frame, text="Book:")
        self.book_label.grid(row=0, column=2, padx=5)

        self.book_var = tk.StringVar()
        self.book_dropdown = ttk.Combobox(nav_frame, textvariable=self.book_var, state="readonly", width=20, height=15)
        self.book_dropdown['values'] = self.full_book_names
        self.book_dropdown.grid(row=0, column=3, padx=5)
        self.book_dropdown.bind('<<ComboboxSelected>>', lambda e: self.update_chapters())
        self.book_dropdown.bind('<FocusIn>', lambda e: self.save_notes())  # Save notes when dropdown gains focus

        # Chapter selection
        self.chapter_label = ttk.Label(nav_frame, text="Chapter:")
        self.chapter_label.grid(row=0, column=4, padx=5)

        self.chapter_var = tk.StringVar()
        self.chapter_dropdown = ttk.Combobox(nav_frame, textvariable=self.chapter_var, state="readonly", width=5, height=15)
        self.chapter_dropdown.grid(row=0, column=5, padx=5)
        self.chapter_dropdown.bind('<<ComboboxSelected>>', lambda e: self.update_verses())
        self.chapter_dropdown.bind('<FocusIn>', lambda e: self.save_notes())  # Save notes when dropdown gains focus

        # Verse selection
        self.verse_label = ttk.Label(nav_frame, text="Verse:")
        self.verse_label.grid(row=0, column=6, padx=5)

        self.verse_var = tk.StringVar()
        self.verse_dropdown = ttk.Combobox(nav_frame, textvariable=self.verse_var, state="readonly", width=5, height=15)
        self.verse_dropdown.grid(row=0, column=7, padx=5)
        self.verse_dropdown.bind('<<ComboboxSelected>>', self.on_verse_change)
        self.verse_dropdown.bind('<FocusIn>', lambda e: self.save_notes())  # Save notes when dropdown gains focus

        # Read and Pause buttons moved to the right of the Verse combo box
        self.read_button = ttk.Button(nav_frame, text="Read", command=self.read)
        self.read_button.grid(row=0, column=8, padx=5)

        self.pause_button = ttk.Button(nav_frame, text="Pause", command=self.pause)  # Added Pause button
        self.pause_button.grid(row=0, column=9, padx=5)

        # Add Next Unread Button
        self.next_unread_button = ttk.Button(nav_frame, text="Next Unread", command=self.next_unread)
        self.next_unread_button.grid(row=0, column=10, padx=5)

        # === Control Panel ===
        control_frame = tk.Frame(self)
        control_frame.grid(row=1, column=0, columnspan=3, pady=5)

        # Voice selection
        self.voice_var = tk.StringVar(value=self.voice)
        self.voice_dropdown = ttk.Combobox(control_frame, textvariable=self.voice_var, state="readonly", width=20, height=15)
        self.voice_dropdown['values'] = self.voice_options
        self.voice_dropdown.grid(row=0, column=0, padx=5)
        self.voice_dropdown.bind('<<ComboboxSelected>>', self.update_voice)
        self.voice_dropdown.bind('<FocusIn>', lambda e: self.save_notes())

        # Translation selection
        self.translation_var = tk.StringVar(value=self.current_translation.split('.')[0].upper())
        self.translation_dropdown = ttk.Combobox(control_frame, textvariable=self.translation_var, 
                                            state="readonly", width=5, height=15)
        self.translation_dropdown['values'] = ['NET', 'KJV', 'WEB']
        self.translation_dropdown.grid(row=0, column=1, padx=5)
        self.translation_dropdown.bind('<<ComboboxSelected>>', self.update_translation)
        self.translation_dropdown.bind('<FocusIn>', lambda e: self.save_notes())

        # Text size controls
        size_frame = tk.Frame(control_frame)
        size_frame.grid(row=0, column=2, padx=10)

        self.text_size = tk.IntVar(value=self.text_size)
        ttk.Label(size_frame, text="Text Size:").grid(row=0, column=0, padx=2)

        # Create a style for the buttons
        style = ttk.Style()
        style.configure('Square.TButton', padding=(5, 5))

        ttk.Button(size_frame, text="-", command=lambda: self.change_text_size(-1), style='Square.TButton', width=2).grid(row=0, column=1, padx=2)
        ttk.Button(size_frame, text="+", command=lambda: self.change_text_size(1), style='Square.TButton', width=2).grid(row=0, column=2, padx=2)

        # Skip read verses checkbox
        self.skip_read_verses = tk.BooleanVar(value=self.skip_read_verses)
        self.skip_checkbox = ttk.Checkbutton(control_frame, text="Skip read verses",
                                        variable=self.skip_read_verses)
        self.skip_checkbox.grid(row=0, column=3, padx=10)  # Changed from column=2 to column=3

        # Reset buttons
        reset_frame = tk.Frame(control_frame)
        reset_frame.grid(row=0, column=4, padx=10)  # Changed from column=3 to column=4

        ttk.Button(reset_frame, text="Reset Chapter History",
                 command=self.reset_chapter_history).grid(row=0, column=0, padx=5)
        ttk.Button(reset_frame, text="Reset Chapter Notes",
                 command=self.reset_chapter_notes).grid(row=0, column=1, padx=5)
        ttk.Button(reset_frame, text="Reset Preferences",
                 command=self.reset_preferences).grid(row=0, column=2, padx=5)
        ttk.Button(reset_frame, text="Reset All",
                 command=self.reset_all).grid(row=0, column=3, padx=5)

        # === Verse Display ===
        self.verse_display = tk.Text(self, height=20, wrap=tk.WORD)
        self.verse_display.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.verse_display.configure(font=("TkDefaultFont", self.text_size.get()))

        # Add scrollbar to verse display
        verse_scroll = ttk.Scrollbar(self, command=self.verse_display.yview)
        verse_scroll.grid(row=2, column=2, sticky="ns")  # Configure the text widget to use the scrollbar
        self.verse_display.configure(yscrollcommand=verse_scroll.set)

        # Configure highlighting for read verses
        self.verse_display.tag_configure("read", background="light gray")
        self.verse_display.tag_configure("current", background="yellow")
        self.verse_display.tag_raise("current", "read")

        # === Notes Section ===
        notes_frame = tk.Frame(self)
        notes_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")

        # Configure grid weights for better resizing
        notes_frame.grid_columnconfigure(0, weight=1)  # Notes label
        notes_frame.grid_columnconfigure(1, weight=3)  # Notes text
        notes_frame.grid_columnconfigure(2, weight=1)  # Copy Notes Button

        self.notes_label = ttk.Label(notes_frame, text="Chapter\nNotes:")
        self.notes_label.grid(row=0, column=0, padx=5, sticky="e")

        self.notes_text = tk.Text(notes_frame, width=80, height=4)  # Increased height to 4
        self.notes_text.grid(row=0, column=1, padx=5, sticky="ew")

        # Add scrollbar to notes text
        notes_scroll = ttk.Scrollbar(notes_frame, command=self.notes_text.yview)  # Add scrollbar to notes text
        notes_scroll.grid(row=0, column=2, sticky="ns")
        self.notes_text.configure(yscrollcommand=notes_scroll.set)  # Configure the text widget to use the scrollbar

        # Copy Notes Button
        self.copy_notes_button = ttk.Button(notes_frame, text="Copy Notes", command=self.copy_notes)
        self.copy_notes_button.grid(row=0, column=3, padx=5, sticky="e")  # Justify right

        # Configure grid weights for better resizing
        self.grid_rowconfigure(2, weight=1)  # Verse Display
        self.grid_columnconfigure(1, weight=1)  # Center column

        # Initialize reading state variables
        self.reading = False
        self.current_verse = None
        self.audio_stream = None
        self.audio_wave = None
        self.audio_paused = False
        self.audio_data = None
        self.audio_index = 0

        # Load last read verse or default to Genesis 1:1
        self.load_last_read_verse()

        # Bind the window close event to save notes
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        """Load or create the config file."""
        self.config = configparser.ConfigParser()
        self.voice_options = asyncio.run(self.get_voice_options())

        if not os.path.exists(self.config_file):
            self.config['Settings'] = {
                'Voice': self.default_voice,
                'SkipReadVerses': str(self.default_skip_read_verses),
                'TextSize': str(self.default_text_size),
                'Translation': self.default_translation,
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(self.config_file)

        self.voice = self.config['Settings']['Voice']
        self.skip_read_verses = self.config['Settings'].getboolean('SkipReadVerses')
        self.text_size = self.config['Settings'].getint('TextSize')
        self.current_translation = self.config['Settings']['Translation']

    async def get_voice_options(self):
        """Get available voices."""
        voices = await edge_tts.list_voices()
        return [v["ShortName"] for v in voices]

    def load_storage_files(self):
        """Initialize storage files if they don't exist."""
        # Update read_verses_file path based on current translation
        self.read_verses_file = f"read_verses_{self.current_translation.split('.')[0]}.csv"

        if not os.path.exists(self.read_verses_file):
            with open(self.read_verses_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Verse ID"])

        # Clean up and convert the verses file if needed
        try:
            # First, migrate any data from old read_verses.csv if it exists
            old_verses_file = "read_verses.csv"
            if os.path.exists(old_verses_file):
                try:
                    old_df = pd.read_csv(old_verses_file)
                    # Migrate data to new translation-specific file
                    if not old_df.empty:
                        old_df.to_csv(self.read_verses_file, index=False)
                    # Delete the old file after migration
                    os.remove(old_verses_file)
                    print(f"Migrated data from {old_verses_file} to {self.read_verses_file}")
                except Exception as e:
                    print(f"Error migrating old verses file: {e}")

            df = pd.read_csv(self.read_verses_file)
            cleaned_verses = []

            for verse_id in df["Verse ID"]:
                try:
                    # If it's already a number, add it directly
                    if isinstance(verse_id, (int, float)):
                        cleaned_verses.append(int(verse_id))
                    else:
                        # If it's in the format "book:chapter:verse", convert it
                        parts = str(verse_id).split(":")
                        if len(parts) == 3:
                            book_num, chapter, verse = map(int, parts)
                            # Find the corresponding Verse ID in bible_data
                            verse_data = self.bible_data[
                                (self.bible_data["Book Number"] == book_num) &
                                (self.bible_data["Chapter"] == chapter) &
                                (self.bible_data["Verse"] == verse)
                            ]
                            if not verse_data.empty:
                                cleaned_verses.append(int(verse_data["Verse ID"].values[0]))
                except:
                    continue  # Skip any problematic entries

            # Remove duplicates and sort
            cleaned_verses = sorted(list(set(cleaned_verses)))

            # Save the cleaned version back to the file
            with open(self.read_verses_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Verse ID"])
                for verse_id in cleaned_verses:
                    writer.writerow([verse_id])

            self.read_verses = cleaned_verses
            print(f"Loaded {len(self.read_verses)} read verses")

        except Exception as e:
            print(f"Error loading read verses: {e}")
            self.read_verses = []

        # Ensure notes.csv exists
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Book Number", "Chapter", "Notes"])

        # Load notes
        try:
            self.notes = pd.read_csv(self.notes_file)
        except Exception as e:
            print(f"Error loading notes: {e}")
            self.notes = pd.DataFrame(columns=["Book Number", "Chapter", "Notes"])

    def on_closing(self):
        """Save notes and close the window."""
        self.save_notes()
        self.destroy()

    def update_voice(self, event):
        """Update the selected voice and save to config."""
        self.voice = self.voice_var.get()
        self.config['Settings']['Voice'] = self.voice
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def update_translation(self, event):
        """Update the selected translation and reload Bible data."""
        new_translation = f"{self.translation_var.get().lower()}.csv"
        if new_translation != self.current_translation:
            self.save_notes()  # Save current notes
            self.current_translation = new_translation
            
            # Update config
            self.config['Settings']['Translation'] = self.current_translation
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            
            # Update read verses file path
            old_verses_file = self.read_verses_file
            self.read_verses_file = f"read_verses_{self.current_translation.split('.')[0]}.csv"
            
            # Load new translation data
            self.load_bible_data()
            self.load_storage_files()
            
            # Reset to Genesis 1:1
            self.book_var.set("Genesis")
            self.update_chapters()
            self.chapter_var.set("1")
            self.update_verses()
            self.verse_var.set("1")
            self.navigate()

    def on_book_change(self, event):
        """Handle book selection changes."""
        try:
            print("Book change detected")
            self.save_notes()  # Save notes for the current chapter first
            print("Notes saved for the current chapter")
            self.stop()  # Stop any current playback
            time.sleep(0.1)  # Brief pause to ensure cleanup is complete
            self.update_chapters()  # This will also trigger update_verses
            print("Chapters updated")
            self.navigate()
            print("Navigated to the new chapter")
        except Exception as e:
            print(f"Error during book change: {e}")

    def on_chapter_change(self, event):
        """Handle chapter selection changes."""
        try:
            print("Chapter change detected")
            self.save_notes()  # Save notes for the current chapter first
            print("Notes saved for the current chapter")
            self.stop()  # Stop any current playback
            time.sleep(0.1)  # Brief pause to ensure cleanup is complete
            self.update_verses()
            print("Verses updated")
            self.navigate()
            print("Navigated to the new verse")
        except Exception as e:
            print(f"Error during chapter change: {e}")

    def on_verse_change(self, event):
        """Handle verse selection changes."""
        try:
            self.stop()  # Stop any current playback
            time.sleep(0.1)  # Brief pause to ensure cleanup is complete
            self.save_notes()
            self.navigate()
        except Exception as e:
            print(f"Error during verse change: {e}")

    def load_bible_data(self):
        """Load the Bible data from the selected CSV file."""
        try:
            self.bible_data = pd.read_csv(self.current_translation)
            self.books_data = self.bible_data[["Book Abbreviation", "Full Book Name", "Book Number"]].drop_duplicates()
            self.books_data = self.books_data.sort_values("Book Number")
            self.book_to_number = dict(zip(self.books_data["Book Abbreviation"], self.books_data["Book Number"]))
            self.number_to_book = dict(zip(self.books_data["Book Number"], self.books_data["Book Abbreviation"]))
            self.book_abbrev_to_full = dict(zip(self.books_data["Book Abbreviation"], self.books_data["Full Book Name"]))
            self.book_full_to_abbrev = dict(zip(self.books_data["Full Book Name"], self.books_data["Book Abbreviation"]))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {self.current_translation}: {e}")
            self.current_translation = "net.csv"
            self.load_bible_data()

    def update_books(self):
        """Update the book dropdown with the full book names from the selected translation."""
        self.full_book_names = self.books_data["Full Book Name"].tolist()
        self.book_dropdown['values'] = self.full_book_names
        if self.full_book_names:  # Set the first book as default
            self.book_dropdown.set(self.full_book_names[0])
            self.update_chapters()

    def load_last_read_verse(self):
        """Navigate to the last read verse or default to Genesis 1:1."""
        if self.read_verses:
            last_verse_id = self.read_verses[-1]
            print(f"Last verse ID: {last_verse_id}")  # Debugging statement

            # Filter the bible_data DataFrame to find the verse
            verse_data = self.bible_data[
                self.bible_data["Verse ID"] == last_verse_id
            ]

            if not verse_data.empty:
                verse_data = verse_data.iloc[0]
                book_abbrev = self.number_to_book[verse_data["Book Number"]]
                book_name = self.book_abbrev_to_full[book_abbrev]
                self.book_var.set(book_name)
                self.update_chapters()

                self.chapter_var.set(str(verse_data["Chapter"]))
                self.update_verses()

                self.verse_var.set(str(verse_data["Verse"]))
                self.navigate()
            else:
                print(f"Verse ID {last_verse_id} not found in bible_data.")  # Debugging statement
                # Default to Genesis 1:1
                self.book_var.set("Genesis")
                self.update_chapters()
                self.chapter_var.set("1")
                self.update_verses()
                self.verse_var.set("1")
                self.navigate()
        else:
            # Default to Genesis 1:1
            self.book_var.set("Genesis")
            self.update_chapters()
            self.chapter_var.set("1")
            self.update_verses()
            self.verse_var.set("1")
            self.navigate()

    def update_chapters(self):
        """Update available chapters when a book is selected."""
        try:
            selected_book = self.book_var.get()
            if not selected_book:
                return

            book_abbrev = self.book_full_to_abbrev[selected_book]
            book_number = self.book_to_number[book_abbrev]

            # Get all chapters for the selected book
            chapters = sorted(self.bible_data[self.bible_data["Book Number"] == book_number]["Chapter"].unique())
            
            # Update chapter dropdown
            self.chapter_dropdown['values'] = chapters
            if chapters:
                self.chapter_var.set(str(chapters[0]))  # Set to first chapter
                self.update_verses()  # Update verses for the selected chapter
            
            self.navigate()
        except Exception as e:
            print(f"Error updating chapters: {e}")

    def update_verses(self):
        """Update available verses when a chapter is selected."""
        try:
            selected_book = self.book_var.get()
            selected_chapter = self.chapter_var.get()

            if not (selected_book and selected_chapter):
                return

            book_abbrev = self.book_full_to_abbrev[selected_book]
            book_number = self.book_to_number[book_abbrev]
            chapter = int(selected_chapter)

            # Get all verses for the selected book and chapter
            verses = sorted(self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter)
            ]["Verse"].unique())

            # Update verse dropdown
            self.verse_dropdown['values'] = verses
            if verses:
                self.verse_var.set(str(verses[0]))  # Set to first verse
            
            self.navigate()
        except Exception as e:
            print(f"Error updating verses: {e}")

    def navigate(self, event=None):
        """Display all verses in the chapter with the selected verse highlighted."""
        # Get current selections
        book = self.book_var.get()
        chapter = self.chapter_var.get()
        verse = self.verse_var.get()

        # Validate selections
        if not all([book, chapter, verse]):
            return

        # Convert to proper types
        book_abbrev = self.book_full_to_abbrev[book]
        book_number = self.book_to_number[book_abbrev]
        chapter = int(chapter)
        verse = int(verse)

        # Get chapter verses
        chapter_verses = self.bible_data[(
            self.bible_data["Book Number"] == book_number) &
            (self.bible_data["Chapter"] == chapter)
        ]

        if chapter_verses.empty:
            return

        # Clear display and remove any existing tags
        self.verse_display.delete("1.0", tk.END)  # Clear the verse display
        self.verse_display.tag_remove("current", "1.0", "end")  # Remove current tag
        self.verse_display.tag_remove("read", "1.0", "end")  # Remove read tag

        # Display verses
        line_number = 1
        target_line = None

        for _, row in chapter_verses.iterrows():  # Iterate over each verse in the chapter
            # Add verse text with abbreviated book name
            verse_text = f"{book_abbrev} {row['Chapter']}:{row['Verse']} {row['Text']}\n\n"
            self.verse_display.insert("end", verse_text)

            # Track current verse position
            if row['Verse'] == verse:
                target_line = line_number
                if self.reading and self.current_verse == verse:
                    self.verse_display.tag_add("current", f"{line_number}.0", f"{line_number + 1}.0")

            # Apply read tag
            if row['Verse ID'] in self.read_verses:
                self.verse_display.tag_add("read", f"{line_number}.0", f"{line_number + 1}.0")

            line_number += 2

        # Apply current tag after read tag to ensure it takes precedence
        if target_line:
            self.verse_display.tag_add("current", f"{target_line}.0", f"{target_line + 1}.0")

        # Center the target verse
        if target_line:
            self.center_verse(target_line)

        # Load chapter notes
        self.load_notes()

    def center_verse(self, line_number):
        """Center the specified line in the verse display."""
        try:
            # Get the number of visible lines
            visible_lines = self.verse_display.winfo_height() / int(self.text_size.get())

            # Calculate the line to center on
            # Position the target verse a few lines down from the top
            center_line = max(1, line_number - 4)  # Adjust this value to change the position

            # Use see() to make the line visible
            self.verse_display.see(f"{center_line}.0")

            # After a brief delay, adjust the view to position the verse a few lines down from the top
            self.after(50, lambda: self.verse_display.yview_moveto(
                (center_line - 1) / float(self.verse_display.count("1.0", "end", "lines")[0])
            ))
        except Exception as e:  # Handle any exceptions that may occur
            print(f"Error centering verse: {e}")

    def change_text_size(self, delta):
        """Change the font size of the verse display and save to config."""
        new_size = self.text_size.get() + delta
        if 8 <= new_size <= 24:  # Limit size range
            self.text_size.set(new_size)
            self.verse_display.configure(font=("TkDefaultFont", new_size))  # Update the font size
            self.config['Settings']['TextSize'] = str(new_size)
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

    def reset_chapter_history(self):
        """Reset the read history for the current chapter with confirmation."""
        confirmation = messagebox.askyesno(
            "Reset Chapter History",
            "Are you sure you want to reset the read history for this chapter?"
        )
        if confirmation:
            book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
            book_number = self.book_to_number[book_abbrev]
            chapter = int(self.chapter_var.get())

            # Get verse IDs for current chapter
            chapter_verses = self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter)
            ]["Verse ID"].tolist()

            # Remove these verses from read_verses
            self.read_verses = [v for v in self.read_verses if v not in chapter_verses]

            # Update read_verses file
            pd.DataFrame({"Verse ID": self.read_verses}).to_csv(self.read_verses_file, index=False)

            # Refresh display
            self.navigate()

    def reset_chapter_notes(self):
        """Delete all notes for the current chapter with confirmation."""
        confirmation = messagebox.askyesno(
            "Reset Chapter Notes",
            "Are you sure you want to delete all notes for this chapter?"
        )  # Ask for confirmation
        if confirmation:
            book_abbrev = self.book_full_to_abbrev[self.book_var.get()]  # Get the book abbreviation
            book_number = self.book_to_number[book_abbrev]  # Get the book number
            chapter = int(self.chapter_var.get())  # Get the chapter number

            # Remove notes for this chapter
            self.notes = self.notes[
                ~((self.notes["Book Number"] == book_number) & (self.notes["Chapter"] == chapter))]  # Filter out notes for the chapter

            # Update notes file
            self.notes.to_csv(self.notes_file, index=False)

            # Clear notes display
            self.notes_text.delete("1.0", tk.END)

    def reset_preferences(self):
        """Reset settings to their defaults with confirmation."""
        confirmation = messagebox.askyesno(
            "Reset Preferences",
            "Are you sure you want to reset all settings to their defaults?"
        )
        if confirmation:
            # Reset settings to defaults
            self.config['Settings'] = {
                'Voice': self.default_voice,
                'SkipReadVerses': str(self.default_skip_read_verses),
                'TextSize': str(self.default_text_size),
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

            # Update GUI elements
            self.voice_var.set(self.default_voice)
            self.skip_read_verses.set(self.default_skip_read_verses)
            self.text_size.set(self.default_text_size)  # Update the font size
            self.verse_display.configure(font=("TkDefaultFont", self.default_text_size))

    def reset_all(self):
        """Reset all history, notes, and settings to their defaults with confirmation."""
        confirmation = messagebox.askyesno(
            "Reset All",
            "THIS IRREVERSIBLE ACTION WILL RESET ALL HISTORY, NOTES AND SETTINGS TO THEIR DEFAULTS.\n\nYOU CANNOT GET YOUR NOTES BACK."
        )  # Ask for confirmation
        if confirmation:
            # Reset read verses
            self.read_verses = []
            with open(self.read_verses_file, "w") as f:
                f.write("Verse ID\n")

            # Reset notes
            self.notes = pd.DataFrame(columns=["Book Number", "Chapter", "Notes"])
            self.notes.to_csv(self.notes_file, index=False)

            # Reset settings to defaults
            self.config['Settings'] = {
                'Voice': self.default_voice,
                'SkipReadVerses': str(self.default_skip_read_verses),
                'TextSize': str(self.default_text_size),
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

            # Update GUI elements
            self.voice_var.set(self.default_voice)
            self.skip_read_verses.set(self.default_skip_read_verses)
            self.text_size.set(self.default_text_size)
            self.verse_display.configure(font=("TkDefaultFont", self.default_text_size))

            # Refresh display
            self.navigate()

    def stop(self):
        """Stop the current audio playback and reset reading state."""
        print("=== Stopping playback ===")

        # Set flags first
        self.reading = False
        self.audio_paused = False

        # Enable buttons
        try:
            print("Resetting button states...")
            self.read_button.config(state="normal")
            self.next_unread_button.config(state="normal")
        except Exception as e:
            print(f"Error resetting buttons: {e}")

        try:
            # Stop and close audio stream
            if hasattr(self, 'audio_stream') and self.audio_stream:
                print("Closing audio stream...")
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception as e:
                    print(f"Error closing audio stream: {e}")
                self.audio_stream = None

            # Close wave file
            if hasattr(self, 'audio_wave') and self.audio_wave:
                print("Closing wave file...")
                try:
                    self.audio_wave.close()
                except Exception as e:
                    print(f"Error closing wave file: {e}")
                self.audio_wave = None

            # Clean up PyAudio instance
            if hasattr(self, 'pyaudio_instance') and self.pyaudio_instance:
                print("Terminating PyAudio...")
                try:
                    self.pyaudio_instance.terminate()
                except Exception as e:
                    print(f"Error terminating PyAudio: {e}")
                self.pyaudio_instance = None

        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Reset audio variables
            self.audio_data = None
            self.audio_index = 0
            self.current_verse = None
            print("=== Stop completed ===")

    def read(self):
        """Handle the reading of verses."""
        print("=== Read method started ===")

        if self.audio_paused:
            print("Audio was paused, resuming...")
            self.resume()
            return

        # Get current verse information
        book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
        book_number = self.book_to_number[book_abbrev]
        chapter = int(self.chapter_var.get())
        verse = int(self.verse_var.get())

        current_verse_data = self.bible_data[
            (self.bible_data["Book Number"] == book_number) &
            (self.bible_data["Chapter"] == chapter) &
            (self.bible_data["Verse"] == verse)
        ]

        if current_verse_data.empty:
            print("No verse data found!")
            return

        verse_id = int(current_verse_data["Verse ID"].values[0])  # Get numeric Verse ID

        # Check if we should skip read verses
        if self.skip_read_verses.get() and verse_id in self.read_verses:
            print(f"Skipping read verse: {verse_id}")
            self.next_unread()
            return

        # Stop any existing reading before starting new one
        print("Stopping any existing playback...")
        self.stop()

        print("Setting up new reading...")
        self.reading = True

        # Mark verse as read if not already marked
        if verse_id not in self.read_verses:
            print(f"DEBUG - read() method writing verse_id: {verse_id}")  # Debug print
            self.read_verses.append(verse_id)
            # Save only the numeric Verse ID to CSV
            with open(self.read_verses_file, "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([verse_id])  # Only save the numeric ID

        text_to_speak = current_verse_data["Text"].values[0]
        self.current_verse = verse

        print(f"Starting text-to-speech for verse {verse_id}")
        print(f"Text to speak: {text_to_speak}")

        # Update the display to show the verse as read
        self.navigate()

        # Start new reading in a separate thread
        threading.Thread(target=self.speak_text, args=(text_to_speak,)).start()
        print("=== Read method completed ===")

    def speak_text(self, text):
        """Convert text to speech using edge-tts and play the audio."""
        print("DEBUG - speak_text() called")  # Debug print
        try:
            print("Starting speak_text")
            # Stop any existing playback
            self.stop()

            # Get the current script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Set full paths for temporary files
            self.temp_mp3 = os.path.join(script_dir, "temp.mp3")
            self.temp_wav = os.path.join(script_dir, "temp.wav")

            print(f"Using temp files: MP3={self.temp_mp3}, WAV={self.temp_wav}")
            # Create and play the audio
            asyncio.run(self.save_and_play_audio(text))
        except Exception as e:
            print(f"Error in speak_text: {e}")
            self.stop()

    async def save_and_play_audio(self, text):
        """Generate and play audio for the given text."""
        print("DEBUG - save_and_play_audio() called")  # Debug print
        try:
            print("Starting save_and_play_audio")
            # Clean up any existing temporary files
            for temp_file in [self.temp_mp3, self.temp_wav]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"Removed existing {temp_file}")
                    except Exception as e:
                        print(f"Error removing temporary file {temp_file}: {e}")

            # Generate MP3
            print("Generating MP3...")
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(self.temp_mp3)

            # Wait for MP3 file to be created
            print("Waiting for MP3 file...")
            for i in range(50):
                if os.path.exists(self.temp_mp3):
                    print("MP3 file created successfully")
                    break
                await asyncio.sleep(0.1)

            if not os.path.exists(self.temp_mp3):
                raise FileNotFoundError(f"MP3 file was not created at {self.temp_mp3}")

            # Convert to WAV
            print("Converting to WAV...")
            try:
                audio = AudioSegment.from_mp3(self.temp_mp3)
                audio.export(self.temp_wav, format="wav")
                print("WAV file created successfully")
            except Exception as e:
                raise Exception(f"Error converting MP3 to WAV: {e}")

            # Verify the WAV file
            print("Verifying WAV file...")
            try:
                with wave.open(self.temp_wav, 'rb') as test_wav:
                    frames = test_wav.getnframes()
                    print(f"WAV file frames: {frames}")
                    if frames == 0:
                        raise Exception("WAV file is empty")
            except Exception as e:
                raise Exception(f"Invalid WAV file: {e}")

            # Play the audio
            print("Starting playback...")
            if self.reading:
                print("Reading flag is True, calling play_audio...")
                # Use after to schedule playback in the main thread
                self.after(100, lambda: self.play_audio(self.temp_wav))
            else:
                print("Reading flag is False, setting it to True and calling play_audio...")
                self.reading = True
                self.after(100, lambda: self.play_audio(self.temp_wav))

        except Exception as e:
            print(f"Error in save_and_play_audio: {e}")
            self.stop()

    def convert_mp3_to_wav(self, mp3_file, wav_file):
        """Convert MP3 audio file to WAV format using pydub."""
        try:
            audio = AudioSegment.from_mp3(mp3_file)
            audio.export(wav_file, format="wav")
        except Exception as e:
            print(f"Error converting MP3 to WAV: {e}")

    def play_audio(self, filename):
        """Play audio file and handle verse progression."""
        print(f"=== Play_audio started with file: {filename} ===")

        try:
            if not os.path.exists(filename):
                print(f"Audio file not found: {filename}")
                return

            # Set reading state
            print("Setting reading state...")
            self.reading = True
            self.audio_paused = False

            # Update UI
            self.read_button.config(state="disabled")
            self.next_unread_button.config(state="disabled")

            # Start playback in a separate thread
            threading.Thread(target=self._play_audio_thread, args=(filename,), daemon=True).start()

        except Exception as e:
            print(f"Error in play_audio: {e}")
            import traceback
            traceback.print_exc()
            self.stop()

    def _play_audio_thread(self, filename):
        """Handle audio playback in a separate thread."""
        try:
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()

            # Open wave file
            self.audio_wave = wave.open(filename, 'rb')

            # Get wave file properties
            channels = self.audio_wave.getnchannels()
            width = self.audio_wave.getsampwidth()
            rate = self.audio_wave.getframerate()

            # Create audio stream
            self.audio_stream = self.pyaudio_instance.open(
                format=self.pyaudio_instance.get_format_from_width(width),
                channels=channels,
                rate=rate,
                output=True
            )

            # Read and play the audio data
            chunk_size = 1024
            data = self.audio_wave.readframes(chunk_size)

            while data and self.reading:
                if not self.audio_paused:
                    self.audio_stream.write(data)
                    data = self.audio_wave.readframes(chunk_size)
                else:
                    time.sleep(0.1)

            # After playback, schedule next verse in main thread
            if self.reading:
                self.after(100, self.progress_to_next_verse)

        except Exception as e:
            print(f"Error in _play_audio_thread: {e}")
        finally:
            self.after(100, self.stop)  # Schedule cleanup in main thread

    def progress_to_next_verse(self):
        """Progress to the next verse after current verse finishes."""
        try:
            print("=== Progressing to next verse ===")
            self.save_notes()  # Save any notes before progressing

            book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
            book_number = self.book_to_number[book_abbrev]
            chapter = int(self.chapter_var.get())
            current_verse = int(self.verse_var.get())

            # Get current verse ID
            current_verse_data = self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter) &
                (self.bible_data["Verse"] == current_verse)
            ]

            if not current_verse_data.empty:
                verse_id = int(current_verse_data["Verse ID"].values[0])

                # Mark current verse as read if not already marked
                if verse_id not in self.read_verses:
                    print(f"DEBUG - progress_to_next_verse() writing verse_id: {verse_id}")  # Debug print
                    self.read_verses.append(verse_id)
                    with open(self.read_verses_file, "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([verse_id])

            next_verse = current_verse + 1
            max_verse = max([int(v) for v in self.verse_dropdown['values']])

            if next_verse <= max_verse:
                print(f"Moving to next verse: {next_verse}")
                self.verse_var.set(str(next_verse))
                self.navigate()
                self.read()  # Start reading the next verse
            else:
                print("Reached end of chapter, moving to next chapter")
                self.next_chapter()

        except Exception as e:
            print(f"Error progressing to next verse: {e}")

    def check_pause(self):
        """Check if the audio should be resumed."""
        if not self.audio_paused and self.reading:
            self.audio_stream.start_stream()

    def pause(self):
        """Pause the current audio playback."""
        if self.reading:  # Ensure we are currently reading
            self.audio_paused = True
            self.read_button.config(state="normal")  # Re-enable the Read button
            self.next_unread_button.config(state="normal")  # Re-enable the Next Unread button

    def resume(self):
        """Resume paused audio playback."""
        if self.reading:  # Ensure we are currently reading
            self.audio_paused = False
            self.read_button.config(state="disabled")  # Disable the Read button while resuming
            self.next_unread_button.config(state="disabled")  # Disable the Next Unread button while resuming

            if self.audio_stream:
                self.audio_stream.start_stream()

    def save_notes(self):
        """Save notes for the current chapter."""
        print("Saving notes")
        book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
        book_number = self.book_to_number[book_abbrev]
        chapter = int(self.chapter_var.get())  # Convert chapter to integer
        notes_text = self.notes_text.get("1.0", tk.END).strip()

        if notes_text:  # Only save if there are notes
            # Remove existing notes for this chapter
            self.notes = self.notes[
                ~((self.notes["Book Number"] == book_number) & (self.notes["Chapter"] == chapter))
            ]

            # Add new note
            new_note = pd.DataFrame({
                "Book Number": [book_number],
                "Chapter": [chapter],
                "Notes": [notes_text]
            })
            self.notes = pd.concat([self.notes, new_note], ignore_index=True)
            self.notes.to_csv(self.notes_file, index=False)
            print("Notes saved to file")

    def load_notes(self):
        """Load notes for the current chapter."""
        print("Loading notes")
        self.notes_text.delete("1.0", tk.END)

        book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
        book_number = self.book_to_number[book_abbrev]
        chapter = int(self.chapter_var.get())  # Convert chapter to integer

        chapter_notes = self.notes[
            (self.notes["Book Number"] == book_number) &
            (self.notes["Chapter"] == chapter)
        ]

        if not chapter_notes.empty:
            latest_note = chapter_notes.iloc[-1]["Notes"]
            self.notes_text.insert("1.0", latest_note)
            print("Notes loaded from file")
        else:
            print("No notes found for this chapter")

    def copy_notes(self):
        """Copy the current chapter notes to the clipboard."""
        notes_text = self.notes_text.get("1.0", tk.END).strip()
        if notes_text:
            pyperclip.copy(notes_text)
            messagebox.showinfo("Notes Copied", "The notes have been copied to the clipboard.")

    def create_mp3(self):
        """Create an MP3 file for a selected range of verses."""
        # Create a dialog to select the starting and ending verses
        dialog = Toplevel(self)
        dialog.title("Create MP3")

        # Starting Verse Selection
        tk.Label(dialog, text="Starting Verse:").grid(row=0, column=0, padx=5, pady=5)  # Label for starting verse
        start_book_var = tk.StringVar()
        start_book_dropdown = ttk.Combobox(dialog, textvariable=start_book_var, state="readonly", width=20, height=15)
        start_book_dropdown['values'] = self.full_book_names  # Use the same book list
        start_book_dropdown.grid(row=0, column=1, padx=5, pady=5)  # Dropdown for starting book

        start_chapter_var = tk.StringVar()
        start_chapter_dropdown = ttk.Combobox(dialog, textvariable=start_chapter_var, state="readonly", width=5, height=15)
        start_chapter_dropdown.grid(row=0, column=2, padx=5, pady=5)  # Dropdown for starting chapter

        start_verse_var = tk.StringVar()
        start_verse_dropdown = ttk.Combobox(dialog, textvariable=start_verse_var, state="readonly", width=5, height=15)
        start_verse_dropdown.grid(row=0, column=3, padx=5, pady=5)  # Dropdown for starting verse

        # Ending Verse Selection
        tk.Label(dialog, text="Ending Verse:").grid(row=1, column=0, padx=5, pady=5)  # Label for ending verse
        end_book_var = tk.StringVar()
        end_book_dropdown = ttk.Combobox(dialog, textvariable=end_book_var, state="readonly", width=20, height=15)
        end_book_dropdown['values'] = self.full_book_names  # Use the same book list
        end_book_dropdown.grid(row=1, column=1, padx=5, pady=5)  # Dropdown for ending book

        end_chapter_var = tk.StringVar()
        end_chapter_dropdown = ttk.Combobox(dialog, textvariable=end_chapter_var, state="readonly", width=5, height=15)
        end_chapter_dropdown.grid(row=1, column=2, padx=5, pady=5)  # Dropdown for ending chapter

        end_verse_var = tk.StringVar()
        end_verse_dropdown = ttk.Combobox(dialog, textvariable=end_verse_var, state="readonly", width=5, height=15)
        end_verse_dropdown.grid(row=1, column=3, padx=5, pady=5)  # Dropdown for ending verse

        # Update chapter and verse dropdowns based on book selection
        def update_start_chapters(event):
            book_name = start_book_var.get()
            if not book_name:
                return
            book_abbrev = self.book_full_to_abbrev[book_name]
            book_number = self.book_to_number[book_abbrev]
            chapters = sorted(self.bible_data[self.bible_data["Book Number"] == book_number]["Chapter"].unique())
            start_chapter_dropdown['values'] = chapters
            if chapters:
                start_chapter_dropdown.set(chapters[0])
                update_start_verses(None)

        def update_start_verses(event):
            book_name = start_book_var.get()  # Get the selected book
            chapter = start_chapter_var.get()  # Get the selected chapter
            if not (book_name and chapter):  # Validate selections
                return
            book_abbrev = self.book_full_to_abbrev[book_name]  # Get the book abbreviation
            book_number = self.book_to_number[book_abbrev]  # Get the book number
            chapter = int(chapter)  # Convert chapter to integer
            # Filter verses for the selected book and chapter
            verses = sorted(self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter)
            ]["Verse"].unique())
            start_verse_dropdown['values'] = verses  # Update verse dropdown values
            if verses:
                start_verse_dropdown.set(verses[0])  # Set the first verse as default

        def update_end_chapters(event):  # Update chapter dropdown for ending verse
            book_name = end_book_var.get()
            if not book_name:
                return
            book_abbrev = self.book_full_to_abbrev[book_name]
            book_number = self.book_to_number[book_abbrev]
            chapters = sorted(self.bible_data[self.bible_data["Book Number"] == book_number]["Chapter"].unique())
            end_chapter_dropdown['values'] = chapters
            if chapters:
                end_chapter_dropdown.set(chapters[0])  # Set the first chapter as default
                update_end_verses(None)

        def update_end_verses(event):  # Update verse dropdown for ending verse
            book_name = end_book_var.get()  # Get the selected book
            chapter = end_chapter_var.get()  # Get the selected chapter
            if not (book_name and chapter):  # Validate selections
                return
            book_abbrev = self.book_full_to_abbrev[book_name]  # Get the book abbreviation
            book_number = self.book_to_number[book_abbrev]  # Get the book number
            chapter = int(chapter)  # Convert chapter to integer
            # Filter verses for the selected book and chapter
            verses = sorted(self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter)
            ]["Verse"].unique())
            end_verse_dropdown['values'] = verses  # Update verse dropdown values
            if verses:
                end_verse_dropdown.set(verses[-1])  # Set the last verse as default

        start_book_dropdown.bind('<<ComboboxSelected>>', update_start_chapters)
        start_chapter_dropdown.bind('<<ComboboxSelected>>', update_start_verses)
        end_book_dropdown.bind('<<ComboboxSelected>>', update_end_chapters)
        end_chapter_dropdown.bind('<<ComboboxSelected>>', update_end_verses)

        # Save Button
        def save_mp3():
            start_book = start_book_var.get()
            start_chapter = start_chapter_var.get()
            start_verse = start_verse_var.get()
            end_book = end_book_var.get()
            end_chapter = end_chapter_var.get()
            end_verse = end_verse_var.get()

            if not (start_book and start_chapter and start_verse and end_book and end_chapter and end_verse):
                messagebox.showerror("Invalid Input", "Please select a valid range of verses.")
                return

            start_book_abbrev = self.book_full_to_abbrev[start_book]
            start_book_number = self.book_to_number[start_book_abbrev]
            start_chapter = int(start_chapter)
            start_verse = int(start_verse)

            end_book_abbrev = self.book_full_to_abbrev[end_book]
            end_book_number = self.book_to_number[end_book_abbrev]
            end_chapter = int(end_chapter)
            end_verse = int(end_verse)

            if (start_book_number > end_book_number or
                (start_book_number == end_book_number and start_chapter > end_chapter) or
                (start_book_number == end_book_number and start_chapter == end_chapter and start_verse > end_verse)):
                messagebox.showerror("Invalid Range", "The starting verse must come before the ending verse.")
                return

            # Get the verses in the specified range
            selected_verses = self.bible_data[
                ((self.bible_data["Book Number"] >= start_book_number) &
                 (self.bible_data["Book Number"] <= end_book_number) &
                 (self.bible_data["Chapter"] >= start_chapter) &
                 (self.bible_data["Chapter"] <= end_chapter) &
                 (self.bible_data["Verse"].astype(int) >= start_verse) &
                 (self.bible_data["Verse"].astype(int) <= end_verse))
            ]

            if selected_verses.empty:
                messagebox.showerror("No Verses Found", "No verses found in the specified range.")
                return

            # Create the Saved_MP3s directory if it doesn't exist
            saved_mp3s_dir = os.path.join(os.path.dirname(__file__), "Saved_MP3s")
            if not os.path.exists(saved_mp3s_dir):
                os.makedirs(saved_mp3s_dir)

            # Format the MP3 filename
            start_verse_id = f"{start_book_abbrev}-{start_chapter}-{start_verse}"
            end_verse_id = f"{end_book_abbrev}-{end_chapter}-{end_verse}"
            filename = os.path.join(saved_mp3s_dir, f"{start_verse_id} to {end_verse_id}.mp3")

            # Combine the text of the selected verses
            text_to_speak = " ".join(selected_verses["Text"])

            # Create a progress bar dialog
            progress_dialog = Toplevel(dialog)
            progress_dialog.title("Creating MP3")
            progress_dialog.geometry("300x100")

            progress_label = Label(progress_dialog, text="Generating MP3...")
            progress_label.pack(pady=10)

            progress_bar = Progressbar(progress_dialog, mode='indeterminate')
            progress_bar.pack(pady=10)
            progress_bar.start()

            def update_progress():
                progress_bar.stop()
                progress_dialog.destroy()
                messagebox.showinfo("MP3 Created", f"MP3 file saved as {filename}")
                dialog.destroy()

            # Save the audio to a file in a separate thread
            threading.Thread(target=self.save_audio_threaded, args=(text_to_speak, filename, update_progress, progress_dialog, dialog)).start()

        save_button = ttk.Button(dialog, text="Save MP3", command=save_mp3)
        save_button.grid(row=2, column=0, columnspan=4, pady=10)

        # Set default values to the current book, chapter, and verse
        start_book_dropdown.set(self.book_var.get())  # Set the current book
        start_chapter_dropdown.set(self.chapter_var.get())  # Set the current chapter
        start_verse_dropdown.set(self.verse_var.get())  # Set the current verse
        end_book_dropdown.set(self.book_var.get())  # Set the current book
        end_chapter_dropdown.set(self.chapter_var.get())  # Set the current chapter
        end_verse_dropdown.set(self.verse_var.get())  # Set the current verse

        # Update chapter and verse dropdowns based on the default book selection
        update_start_chapters(None)
        update_start_verses(None)
        update_end_chapters(None)
        update_end_verses(None)

    def save_audio_threaded(self, text, filename, update_progress, progress_dialog, main_dialog):
        """Generate and save audio for the given text in a separate thread."""
        try:
            asyncio.run(self.save_audio(text, filename))
            update_progress()
        except Exception as e:
            progress_dialog.destroy()
            messagebox.showerror("Error", f"Failed to create MP3: {e}")

    async def save_audio(self, text, filename):
        """Generate and save audio for the given text."""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filename)

    def next_unread(self):
        """Navigate to the next unread verse."""
        print("=== Finding next unread verse ===")
        if self.reading:
            self.stop()

        try:
            book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
            book_number = self.book_to_number[book_abbrev]
            current_chapter = int(self.chapter_var.get())
            current_verse = int(self.verse_var.get())

            # Get current verse ID
            current_verse_data = self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == current_chapter) &
                (self.bible_data["Verse"] == current_verse)
            ]

            if not current_verse_data.empty:
                current_verse_id = int(current_verse_data["Verse ID"].values[0])

                # Find the next unread verse
                next_verses = self.bible_data[self.bible_data["Verse ID"] > current_verse_id]

                for _, verse_data in next_verses.iterrows():
                    verse_id = int(verse_data["Verse ID"])
                    if verse_id not in self.read_verses:
                        # Found next unread verse
                        self.book_var.set(self.full_book_names[verse_data["Book Number"] - 1])
                        self.update_chapters()
                        self.chapter_var.set(str(verse_data["Chapter"]))
                        self.update_verses()
                        self.verse_var.set(str(verse_data["Verse"]))
                        self.navigate()
                        self.read()
                        return

            print("No unread verses found")
            messagebox.showinfo("Complete", "No unread verses found!")

        except Exception as e:
            print(f"Error in next_unread: {e}")
            import traceback
            traceback.print_exc()

    def next_chapter(self):
        """Navigate to the next chapter or book if the current chapter is the last one."""
        if self.reading:
            self.stop()

        book_abbrev = self.book_full_to_abbrev[self.book_var.get()]
        book_number = self.book_to_number[book_abbrev]
        current_chapter = int(self.chapter_var.get())

        # Get the next chapter in the current book
        next_chapter = current_chapter + 1
        chapters = sorted(self.bible_data[self.bible_data["Book Number"] == book_number]["Chapter"].unique())
        if next_chapter in chapters:
            self.chapter_var.set(str(next_chapter))
            self.update_verses()
            self.verse_var.set("1")  # Start from the first verse of the next chapter
            self.navigate()
            self.read()  # Start reading the first verse of the next chapter
            return

        # If no next chapter in the current book, move to the next book
        next_book_index = self.full_book_names.index(self.book_var.get()) + 1
        if next_book_index < len(self.full_book_names):
            self.book_var.set(self.full_book_names[next_book_index])
            self.update_chapters()
            self.chapter_var.set("1")  # Start from the first chapter of the next book
            self.update_verses()
            self.verse_var.set("1")  # Start from the first verse of the first chapter of the next book
            self.navigate()
            self.read()  # Start reading the first verse of the first chapter of the next book
            return

        # If no next book, stay at the last verse
        self.verse_var.set(str(self.verse_dropdown['values'][-1]))
        self.navigate()
        self.pause()

    def create_mark_section_dialog(self):
        """Create a dialog to select a range of verses to mark as completed."""
        # Create a dialog to select the starting and ending verses
        dialog = Toplevel(self)
        dialog.title("Mark Section Completed")

        # Starting Verse Selection
        tk.Label(dialog, text="Starting Verse:").grid(row=0, column=0, padx=5, pady=5)
        start_book_var = tk.StringVar()
        start_book_dropdown = ttk.Combobox(dialog, textvariable=start_book_var, state="readonly", width=20, height=15)
        start_book_dropdown['values'] = self.full_book_names
        start_book_dropdown.grid(row=0, column=1, padx=5, pady=5)

        start_chapter_var = tk.StringVar()
        start_chapter_dropdown = ttk.Combobox(dialog, textvariable=start_chapter_var, state="readonly", width=5, height=15)
        start_chapter_dropdown.grid(row=0, column=2, padx=5, pady=5)

        start_verse_var = tk.StringVar()
        start_verse_dropdown = ttk.Combobox(dialog, textvariable=start_verse_var, state="readonly", width=5, height=15)
        start_verse_dropdown.grid(row=0, column=3, padx=5, pady=5)

        # Ending Verse Selection
        tk.Label(dialog, text="Ending Verse:").grid(row=1, column=0, padx=5, pady=5)
        end_book_var = tk.StringVar()
        end_book_dropdown = ttk.Combobox(dialog, textvariable=end_book_var, state="readonly", width=20, height=15)
        end_book_dropdown['values'] = self.full_book_names
        end_book_dropdown.grid(row=1, column=1, padx=5, pady=5)

        end_chapter_var = tk.StringVar()
        end_chapter_dropdown = ttk.Combobox(dialog, textvariable=end_chapter_var, state="readonly", width=5, height=15)
        end_chapter_dropdown.grid(row=1, column=2, padx=5, pady=5)

        end_verse_var = tk.StringVar()
        end_verse_dropdown = ttk.Combobox(dialog, textvariable=end_verse_var, state="readonly", width=5, height=15)
        end_verse_dropdown.grid(row=1, column=3, padx=5, pady=5)

        # Update chapter and verse dropdowns based on book selection
        def update_start_chapters(event):
            book_name = start_book_var.get()
            if not book_name:
                return
            book_abbrev = self.book_full_to_abbrev[book_name]
            book_number = self.book_to_number[book_abbrev]
            chapters = sorted(self.bible_data[self.bible_data["Book Number"] == book_number]["Chapter"].unique())
            start_chapter_dropdown['values'] = chapters
            if chapters:
                start_chapter_dropdown.set(chapters[0])
                update_start_verses(None)

        def update_start_verses(event):
            book_name = start_book_var.get()
            chapter = start_chapter_var.get()
            if not (book_name and chapter):
                return
            book_abbrev = self.book_full_to_abbrev[book_name]
            book_number = self.book_to_number[book_abbrev]
            chapter = int(chapter)
            verses = sorted(self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter)
            ]["Verse"].unique())
            start_verse_dropdown['values'] = verses
            if verses:
                start_verse_dropdown.set(verses[0])

        def update_end_chapters(event):
            book_name = end_book_var.get()
            if not book_name:
                return
            book_abbrev = self.book_full_to_abbrev[book_name]
            book_number = self.book_to_number[book_abbrev]
            chapters = sorted(self.bible_data[self.bible_data["Book Number"] == book_number]["Chapter"].unique())
            end_chapter_dropdown['values'] = chapters
            if chapters:
                end_chapter_dropdown.set(chapters[0])
                update_end_verses(None)

        def update_end_verses(event):
            book_name = end_book_var.get()
            chapter = end_chapter_var.get()
            if not (book_name and chapter):
                return
            book_abbrev = self.book_full_to_abbrev[book_name]
            book_number = self.book_to_number[book_abbrev]
            chapter = int(chapter)
            verses = sorted(self.bible_data[
                (self.bible_data["Book Number"] == book_number) &
                (self.bible_data["Chapter"] == chapter)
            ]["Verse"].unique())
            end_verse_dropdown['values'] = verses
            if verses:
                end_verse_dropdown.set(verses[-1])

        start_book_dropdown.bind('<<ComboboxSelected>>', update_start_chapters)
        start_chapter_dropdown.bind('<<ComboboxSelected>>', update_start_verses)
        end_book_dropdown.bind('<<ComboboxSelected>>', update_end_chapters)
        end_chapter_dropdown.bind('<<ComboboxSelected>>', update_end_verses)

        def mark_section():
            start_book = start_book_var.get()
            start_chapter = start_chapter_var.get()
            start_verse = start_verse_var.get()
            end_book = end_book_var.get()
            end_chapter = end_chapter_var.get()
            end_verse = end_verse_var.get()

            if not (start_book and start_chapter and start_verse and 
                    end_book and end_chapter and end_verse):
                messagebox.showerror("Invalid Input", "Please select a valid range of verses.")
                return

            # Convert selections to proper types
            start_book_number = self.book_to_number[self.book_full_to_abbrev[start_book]]
            end_book_number = self.book_to_number[self.book_full_to_abbrev[end_book]]
            start_chapter = int(start_chapter)
            end_chapter = int(end_chapter)
            start_verse = int(start_verse)
            end_verse = int(end_verse)

            # Validate range
            if (start_book_number > end_book_number or
                (start_book_number == end_book_number and start_chapter > end_chapter) or
                (start_book_number == end_book_number and start_chapter == end_chapter and start_verse > end_verse)):
                messagebox.showerror("Invalid Range", "The starting verse must come before the ending verse.")
                return

            # Get all verse IDs in the range
            verses_in_range = self.bible_data[
                ((self.bible_data["Book Number"] > start_book_number) |
                ((self.bible_data["Book Number"] == start_book_number) & 
                ((self.bible_data["Chapter"] > start_chapter) |
                ((self.bible_data["Chapter"] == start_chapter) & 
                    (self.bible_data["Verse"] >= start_verse))))) &
                ((self.bible_data["Book Number"] < end_book_number) |
                ((self.bible_data["Book Number"] == end_book_number) & 
                ((self.bible_data["Chapter"] < end_chapter) |
                ((self.bible_data["Chapter"] == end_chapter) & 
                    (self.bible_data["Verse"] <= end_verse)))))
            ]["Verse ID"].astype(int).tolist()

            # Add these verse IDs to read_verses if not already present
            new_verses = [v for v in verses_in_range if v not in self.read_verses]
            if new_verses:
                self.read_verses.extend(new_verses)
                with open(self.read_verses_file, "a", newline='') as f:
                    writer = csv.writer(f)
                    for verse_id in new_verses:
                        writer.writerow([verse_id])

            # Refresh display
            self.navigate()
            dialog.destroy()
            messagebox.showinfo("Success", "Selected verses have been marked as completed.")

        # Mark Section Button
        mark_button = ttk.Button(dialog, text="Mark Section", command=mark_section)
        mark_button.grid(row=2, column=0, columnspan=4, pady=10)

        # Set default values to the current book, chapter, and verse
        start_book_dropdown.set(self.book_var.get())
        start_chapter_dropdown.set(self.chapter_var.get())
        start_verse_dropdown.set(self.verse_var.get())
        end_book_dropdown.set(self.book_var.get())
        end_chapter_dropdown.set(self.chapter_var.get())
        end_verse_dropdown.set(self.verse_var.get())

        # Update chapter and verse dropdowns based on the default book selection
        update_start_chapters(None)
        update_start_verses(None)
        update_end_chapters(None)
        update_end_verses(None)

if __name__ == "__main__":
    app = BibleApp()
    app.mainloop()