import os
import re
import yt_dlp
from pytube import Playlist
import customtkinter as ctk
from tkinter import messagebox, Listbox, END, MULTIPLE, filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  

# Function to sanitize filenames
def sanitize_filename(filename):
    # Remove invalid characters using regex
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized

def get_playlist_videos(playlist_url):
    playlist = Playlist(playlist_url)
    videos = playlist.video_urls
    return playlist.title, videos

def download_audio(video_urls, download_directory, playlist_title, status_text):
    # Sanitize the playlist title to create a valid directory name
    sanitized_title = sanitize_filename(playlist_title)
    
    # Create directory for the playlist within the selected directory
    playlist_folder = os.path.join(download_directory, sanitized_title)
    if not os.path.exists(playlist_folder):
        os.makedirs(playlist_folder)

    ydl_opts = {
        'format': 'bestaudio/best',  
        'outtmpl': f'{playlist_folder}/%(title)s.%(ext)s',  # Save files in the selected folder
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for video_url in video_urls:
            ydl.download([video_url])
            status_text.insert(END, f"Downloaded: {video_url}\n")
            status_text.yview(END)  # Scroll to the bottom

# Function to update video list in Listbox
def update_video_list(playlist_url, video_listbox):
    playlist_title, videos = get_playlist_videos(playlist_url)
    video_listbox.delete(0, END)  # Clear any existing items
    for idx, video in enumerate(videos, start=1):
        video_listbox.insert(END, f"{idx}. {video}")
    return playlist_title, videos

def remove_and_download(playlist_url, video_listbox, status_text, download_directory):
    selected_indices = video_listbox.curselection()  # Get selected video indices
    remaining_videos = [video_listbox.get(idx).split('. ')[1] for idx in range(video_listbox.size()) if idx not in selected_indices]
    
    if not remaining_videos:
        messagebox.showerror("Error", "No videos left to download.")
        return
    
    playlist_title, _ = get_playlist_videos(playlist_url)
    video_listbox.delete(0, END)  # Clear the listbox after removal
    download_audio(remaining_videos, download_directory, playlist_title, status_text)

# CustomTkinter GUI setup
def setup_gui():
    root = ctk.CTk()
    root.title("Gr Playlist")

    # Playlist URL input
    ctk.CTkLabel(root, text="Enter YouTube Playlist URL:").pack(pady=5)
    url_entry = ctk.CTkEntry(root, width=200)
    url_entry.pack(pady=5)

    # Button to fetch videos
    def fetch_videos():
        playlist_url = url_entry.get()
        if not playlist_url:
            messagebox.showerror("Error", "Please enter a playlist URL.")
            return
        playlist_title, videos = update_video_list(playlist_url, video_listbox)

    ctk.CTkButton(root, text="Fetch Videos", command=fetch_videos).pack(pady=5)

    # Video listbox
    ctk.CTkLabel(root, text="Select Videos to Remove:").pack(pady=5)
    video_listbox = Listbox(root, selectmode=MULTIPLE, width=50, height=10)
    video_listbox.pack(pady=5)

    # Download status text area
    status_text = ctk.CTkTextbox(root, height=100, width=200, wrap="word")
    status_text.pack(pady=5)

    # Button to select download directory
    download_directory = ""

    def select_directory():
        nonlocal download_directory
        download_directory = filedialog.askdirectory(title="Select Download Directory")
        if download_directory:
            messagebox.showinfo("Directory Selected", f"Download directory set to:\n{download_directory}")

    ctk.CTkButton(root, text="Select Download Directory", command=select_directory).pack(pady=10)

    # Button to remove selected videos and start download
    def start_download():
        if not download_directory:
            messagebox.showerror("Error", "Please select a download directory.")
            return
        
        playlist_url = url_entry.get()
        if not playlist_url:
            messagebox.showerror("Error", "Please enter a playlist URL.")
            return
        remove_and_download(playlist_url, video_listbox, status_text, download_directory)

    ctk.CTkButton(root, text="Remove Selected Videos and Download", command=start_download).pack(pady=10)

    ctk.CTkLabel(root, text="Youssef Gr Application").pack(pady=10)

    root.mainloop()

# Run the GUI
if __name__ == "__main__":
    setup_gui()
