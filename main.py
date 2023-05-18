import os
import glob
import gzip
import json
import requests
import sys
import tkinter as tk
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor

class ConsoleRedirector:
    def __init__(self, console_text_widget):
        self.console_text_widget = console_text_widget

    def write(self, message):
        self.console_text_widget.insert(tk.END, message)
        self.console_text_widget.see(tk.END)

def search_files(keyword, directory):
    matching_files = []
    for filepath in glob.glob(directory + '**/*', recursive=True):
        if os.path.isfile(filepath):
            try:
                if filepath.endswith('.gz'):
                    with gzip.open(filepath, 'rt') as file:
                        content = file.read()
                        if keyword in content:
                            matching_files.append(filepath)
                elif filepath.endswith('.json'):
                    with open(filepath, 'r') as file:
                        try:
                            content = json.load(file)
                            if keyword in str(content):
                                matching_files.append(filepath)
                        except json.JSONDecodeError:
                            file.seek(0)
                            for line in file:
                                content = json.loads(line)
                                if keyword in str(content):
                                    matching_files.append(filepath)
                                    break
                else:
                    with open(filepath, 'r') as file:
                        content = file.read()
                        if keyword in content:
                            matching_files.append(filepath)
            except UnicodeDecodeError:
                pass

    return matching_files

def write_to_file(file_list, output_file):
    with open(output_file, 'w') as f:
        for file in file_list:
            f.write(file + '\n')

def download_file(url):
    download_folder = 'index_files/'
    local_filename = download_folder + url.split('/')[-1]

    # Create the folder if it doesn't exist
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)

    # Check if file already exists
    if os.path.exists(local_filename):
        sys.stdout.write(f"File {local_filename} already exists. Skipping download.\n")
        return

    # If not, download it
    for i in range(3):  # Attempt download 3 times
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            sys.stdout.write(f"Downloaded {local_filename}\n")
            break  # If the download was successful, break out of the loop
        except requests.exceptions.HTTPError as err:
            sys.stdout.write(f"HTTP error occurred: {err}. Retrying.\n")
        except Exception as err:
            sys.stdout.write(f"An error occurred: {err}. Retrying.\n")
        if i == 2:  # After 3 attempts, give up
            sys.stdout.write(f"Failed to download {local_filename} after 3 attempts.\n")

def start_download():
    with open('urls.json') as json_file:
        data = json.load(json_file)
        # Create a thread pool of ??? threads
        with ThreadPoolExecutor(max_workers=25) as executor:
            executor.map(download_file, data['urls'])

def gui():
    window = tk.Tk()
    window.title("Index")

    tk.Label(window, text="Keyword:").grid(row=0)
    keyword_entry = tk.Entry(window)
    keyword_entry.grid(row=0, column=1)
    
    directory = 'index_files'
    
    def run_search():
        keyword = keyword_entry.get()
        output_file = f'{keyword}_output.txt'
        matching_files = search_files(keyword, directory)
        write_to_file(matching_files, output_file)
        messagebox.showinfo("Info", "Search Complete. Check the output file.")
    
    tk.Button(window, text="Start Search", command=run_search).grid(row=1, column=0, columnspan=2)
    
    # New section
    tk.Label(window, text="").grid(row=2)
    
    log_text = tk.Text(window)
    log_text.grid(row=3, column=0, columnspan=2)
    
    sys.stdout = ConsoleRedirector(log_text)
    
    start_button = tk.Button(window, text="Download Indexes (Only use once)", command=start_download)
    start_button.grid(row=4, column=0, columnspan=2)

    window.mainloop()

if __name__ == "__main__":
    gui()
