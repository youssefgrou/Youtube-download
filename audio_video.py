################# WORK PERFECTLY
import os
import re
import yt_dlp
from pytube import Playlist
import customtkinter as ctk
from tkinter import messagebox, Listbox, END, MULTIPLE, filedialog, StringVar, ttk
import time
import threading
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Add these variables before setup_gui
downloading = False
download_count = 0

# Function to sanitize filenames
def sanitize_filename(filename):
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized

def get_playlist_videos(playlist_url):
    playlist = Playlist(playlist_url)
    videos = playlist.video_urls
    return playlist.title, videos

def download_content(video_urls, download_directory, playlist_title, download_type, status_callback=None):
    total_videos = len(video_urls)
    current_video = 0

    def progress_hook(d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d and 'downloaded_bytes' in d:
                percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
                status_callback(f"Downloading video {current_video + 1}/{total_videos}: {percentage:.1f}%")
        elif d['status'] == 'finished':
            status_callback(f"Finished downloading video {current_video + 1}/{total_videos}")

    # Sanitize the playlist title to create a valid directory name
    sanitized_title = sanitize_filename(playlist_title)

    # Create directory for the playlist within the selected directory
    playlist_folder = os.path.join(download_directory, sanitized_title)
    if not os.path.exists(playlist_folder):
        os.makedirs(playlist_folder)

    # Set ydl_opts based on download type (audio or video)
    if download_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{playlist_folder}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'progress': True,
            'progress_hooks': [progress_hook] if status_callback else None
        }
    else:  # video
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Best video and audio quality
            'outtmpl': f'{playlist_folder}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': False,
            'progress': True,
            'progress_hooks': [progress_hook] if status_callback else None
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for video_url in video_urls:
            try:
                current_video += 1
                if status_callback:
                    status_callback(f"Starting download of video {current_video}/{total_videos}")
                ydl.download([video_url])
                if status_callback:
                    status_callback(f"Successfully downloaded video {current_video}/{total_videos}")
            except Exception as e:
                if status_callback:
                    status_callback(f"Failed to download video {current_video}: {str(e)}")
                continue

# Function to update video list in Listbox
def update_video_list(playlist_url, video_listbox):
    playlist_title, videos = get_playlist_videos(playlist_url)
    video_listbox.delete(0, END)  # Clear any existing items
    for idx, video in enumerate(videos, start=1):
        video_listbox.insert(END, f"{idx}. {video}")
    return playlist_title, videos

def remove_and_download(playlist_url, video_listbox, download_directory, download_type):
    selected_indices = video_listbox.curselection()  # Get selected video indices
    remaining_videos = [video_listbox.get(idx).split('. ')[1] for idx in range(video_listbox.size()) if idx not in selected_indices]
    
    if not remaining_videos:
        messagebox.showerror("Error", "No videos left to download.")
        return
    
    playlist_title, _ = get_playlist_videos(playlist_url)
    video_listbox.delete(0, END)  # Clear the listbox after removal
    download_content(remaining_videos, download_directory, playlist_title, download_type)

# Function to download a single video
def download_single_video(video_url, download_directory, download_type):
    video_folder = os.path.join(download_directory, "Single Videos")
    
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)
    
    # Set ydl_opts based on download type (audio or video)
    if download_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{video_folder}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'progress': True
        }
    else:  # video
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{video_folder}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': False,
            'progress': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            print(f"Successfully downloaded: {video_url}")
    except Exception as e:
        print(f"Failed to download {video_url}: {str(e)}")

def create_tooltip(widget, text):
    def show_tooltip(event):
        tooltip = ctk.CTkToplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = ctk.CTkLabel(tooltip, text=text, fg_color="gray30", corner_radius=8)
        label.pack(padx=4, pady=4)
        
        def hide_tooltip():
            tooltip.destroy()
        
        widget.tooltip = tooltip
        widget.bind('<Leave>', lambda e: hide_tooltip())
        
    widget.bind('<Enter>', show_tooltip)

def setup_gui():
    # Create the main window
    root = ctk.CTk()
    root.title("YouTube Downloader Pro")
    root.geometry("1100x800")
    root.minsize(800, 600)

    # Configure grid weights for responsiveness
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Create sidebar
    sidebar = ctk.CTkFrame(root, width=200, corner_radius=0)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_rowconfigure(4, weight=1)

    # App logo/title in sidebar
    logo_label = ctk.CTkLabel(sidebar, text="YT Downloader", font=ctk.CTkFont(size=20, weight="bold"))
    logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

    # Define functions first
    def change_appearance_mode(new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode.lower())

    def show_frame(frame_name):
        # Hide all frames
        for f in frames.values():
            f.grid_forget()
        # Show selected frame
        frames[frame_name].grid(row=0, column=0, sticky="nsew")

    # Sidebar buttons
    sidebar_button_1 = ctk.CTkButton(sidebar, text="Single Video", 
                                    command=lambda: show_frame("single"))
    sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
    
    sidebar_button_2 = ctk.CTkButton(sidebar, text="Playlist", 
                                    command=lambda: show_frame("playlist"))
    sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)

    # Appearance mode switch in sidebar
    appearance_mode_label = ctk.CTkLabel(sidebar, text="Appearance Mode:", anchor="w")
    appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
    appearance_mode_menu = ctk.CTkOptionMenu(sidebar, values=["Dark", "Light", "System"],
                                           command=change_appearance_mode)
    appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(10, 10))

    # Create main content area
    main_content = ctk.CTkFrame(root, corner_radius=0)
    main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_content.grid_columnconfigure(0, weight=1)
    main_content.grid_rowconfigure(1, weight=1)

    # Frames dictionary to hold different views
    frames = {}
    
    # Single Video Frame
    single_frame = ctk.CTkFrame(main_content)
    frames["single"] = single_frame
    
    # Single video content
    ctk.CTkLabel(single_frame, text="Single Video Download", 
                 font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))

    # URL Entry with icon-like prefix and clear button
    url_frame = ctk.CTkFrame(single_frame)
    url_frame.pack(fill="x", padx=30, pady=10)
    
    url_prefix = ctk.CTkLabel(url_frame, text="🔗", font=("Helvetica", 16))
    url_prefix.pack(side="left", padx=(10, 0))
    
    single_url_entry = ctk.CTkEntry(url_frame, placeholder_text="Paste YouTube URL here...",
                                   height=40, font=("Helvetica", 12))
    single_url_entry.pack(side="left", fill="x", expand=True, padx=10)
    
    def clear_url():
        single_url_entry.delete(0, END)
    
    clear_btn = ctk.CTkButton(url_frame, text="✕", width=40, height=40,
                             command=clear_url)
    clear_btn.pack(side="right", padx=5)
    
    create_tooltip(clear_btn, "Clear URL")
    create_tooltip(single_url_entry, "Enter the YouTube video URL here")

    # Format Selection
    format_frame = ctk.CTkFrame(single_frame)
    format_frame.pack(fill="x", padx=30, pady=20)
    
    format_var = StringVar(value="audio")
    
    ctk.CTkLabel(format_frame, text="Download Format:").pack(side="left", padx=10)
    
    audio_btn = ctk.CTkRadioButton(format_frame, text="MP3 Audio", variable=format_var, 
                                  value="audio", font=("Helvetica", 12))
    audio_btn.pack(side="left", padx=20)
    
    video_btn = ctk.CTkRadioButton(format_frame, text="MP4 Video", variable=format_var, 
                                  value="video", font=("Helvetica", 12))
    video_btn.pack(side="left", padx=20)

    # Directory Selection
    dir_frame = ctk.CTkFrame(single_frame)
    dir_frame.pack(fill="x", padx=30, pady=10)
    
    download_directory = [""]
    dir_label = ctk.CTkLabel(dir_frame, text="📁", font=("Helvetica", 16))
    dir_label.pack(side="left", padx=(10, 0))
    
    dir_path_label = ctk.CTkLabel(dir_frame, text="No folder selected", 
                                 font=("Helvetica", 12))
    dir_path_label.pack(side="left", padx=10)
    
    def update_dir_label():
        dir_path = filedialog.askdirectory(title="Select Download Directory")
        if dir_path:
            download_directory[0] = dir_path
            dir_path_label.configure(text=f"...{dir_path[-30:]}" if len(dir_path) > 30 
                                   else dir_path)
            update_status(f"Download directory set to: {dir_path}")

    dir_button = ctk.CTkButton(dir_frame, text="Choose Folder", 
                              command=update_dir_label,
                              width=120)
    dir_button.pack(side="right", padx=10)

    # Status Area with Progress Bar
    status_frame = ctk.CTkFrame(single_frame)
    status_frame.pack(fill="x", padx=30, pady=20)
    
    progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
    progress_bar.pack(fill="x", padx=10, pady=(10,0))
    
    status_text = ctk.CTkTextbox(status_frame, height=100, font=("Helvetica", 11))
    status_text.pack(fill="x", padx=10, pady=10)

    # Add download counter and time
    info_frame = ctk.CTkFrame(single_frame)
    info_frame.pack(fill="x", padx=30, pady=5)
    
    downloads_label = ctk.CTkLabel(info_frame, text="Downloads: 0", 
                                 font=("Helvetica", 12))
    downloads_label.pack(side="left", padx=10)
    
    time_label = ctk.CTkLabel(info_frame, text="", font=("Helvetica", 12))
    time_label.pack(side="right", padx=10)

    def update_time():
        current_time = datetime.now().strftime("%H:%M:%S")
        time_label.configure(text=f"Time: {current_time}")
        root.after(1000, update_time)  # Update every second
    
    update_time()

    def update_status(message):
        status_text.insert(END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        status_text.see(END)
        root.update()

    # Download Button
    download_btn = ctk.CTkButton(single_frame, text="Download", 
                                font=ctk.CTkFont(size=15, weight="bold"),
                                height=50, fg_color="#28a745", hover_color="#218838",
                                command=lambda: start_download(False))
    download_btn.pack(pady=30)

    # Playlist Frame
    playlist_frame = ctk.CTkFrame(main_content)
    frames["playlist"] = playlist_frame
    
    # Playlist content
    ctk.CTkLabel(playlist_frame, text="Playlist Download", 
                 font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))

    # URL Entry
    playlist_url_frame = ctk.CTkFrame(playlist_frame)
    playlist_url_frame.pack(fill="x", padx=30, pady=10)
    
    url_prefix = ctk.CTkLabel(playlist_url_frame, text="🔗", font=("Helvetica", 16))
    url_prefix.pack(side="left", padx=(10, 0))
    
    playlist_url_entry = ctk.CTkEntry(playlist_url_frame, 
                                    placeholder_text="Paste YouTube Playlist URL here...",
                                    height=40, font=("Helvetica", 12))
    playlist_url_entry.pack(side="left", fill="x", expand=True, padx=10)

    # Format Selection for Playlist
    playlist_format_frame = ctk.CTkFrame(playlist_frame)
    playlist_format_frame.pack(fill="x", padx=30, pady=20)
    
    playlist_format_var = StringVar(value="audio")
    
    ctk.CTkLabel(playlist_format_frame, text="Download Format:").pack(side="left", padx=10)
    
    audio_btn = ctk.CTkRadioButton(playlist_format_frame, text="MP3 Audio", 
                                  variable=playlist_format_var, value="audio",
                                  font=("Helvetica", 12))
    audio_btn.pack(side="left", padx=20)
    
    video_btn = ctk.CTkRadioButton(playlist_format_frame, text="MP4 Video", 
                                  variable=playlist_format_var, value="video",
                                  font=("Helvetica", 12))
    video_btn.pack(side="left", padx=20)

    # Video List with Scrollbar
    list_frame = ctk.CTkFrame(playlist_frame)
    list_frame.pack(fill="both", expand=True, padx=30, pady=10)
    
    ctk.CTkLabel(list_frame, text="Select Videos to Exclude:", 
                 font=("Helvetica", 14)).pack(pady=5)
    
    # Create a frame for listbox and scrollbar
    list_container = ctk.CTkFrame(list_frame)
    list_container.pack(fill="both", expand=True, padx=10, pady=5)
    
    video_listbox = Listbox(list_container, selectmode=MULTIPLE, 
                           font=("Helvetica", 10),
                           bg='#2b2b2b', fg='white', 
                           selectbackground='#4a4a4a')
    video_listbox.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(list_container, orient="vertical", 
                             command=video_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    video_listbox.configure(yscrollcommand=scrollbar.set)

    # Fetch and Download Buttons
    button_frame = ctk.CTkFrame(playlist_frame)
    button_frame.pack(fill="x", padx=30, pady=20)
    
    fetch_btn = ctk.CTkButton(button_frame, text="Fetch Playlist", 
                             command=lambda: fetch_videos(),
                             width=200)
    fetch_btn.pack(side="left", padx=10)
    
    playlist_download_btn = ctk.CTkButton(button_frame, text="Download Playlist",
                                        command=lambda: start_download(True),
                                        width=200, fg_color="#28a745", 
                                        hover_color="#218838")
    playlist_download_btn.pack(side="right", padx=10)

    # Show default frame
    show_frame("single")

    # Download functions
    def start_download(is_playlist=True):
        global downloading, download_count
        
        if downloading:
            messagebox.showwarning("Download in Progress", 
                                 "Please wait for the current download to finish.")
            return

        if not download_directory[0]:
            messagebox.showerror("Error", "Please select a download directory.")
            return
        
        url = playlist_url_entry.get() if is_playlist else single_url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        def download_thread():
            global downloading, download_count
            downloading = True
            try:
                progress_bar.pack(fill="x", padx=10, pady=(10,0))  # Show progress bar
                progress_bar.start(10)
                download_type = playlist_format_var.get() if is_playlist else format_var.get()
                
                if is_playlist:
                    update_status(f"Starting playlist download in {download_type} format...")
                    remove_and_download(url, video_listbox, download_directory[0], download_type)
                    update_status("Playlist download completed!")
                else:
                    update_status(f"Starting single video download in {download_type} format...")
                    download_single_video(url, download_directory[0], download_type)
                    update_status("Single video download completed!")
                
                download_count += 1
                downloads_label.configure(text=f"Downloads: {download_count}")
                
                progress_bar.stop()
                messagebox.showinfo("Success", "Download completed successfully!")
            except Exception as e:
                error_message = f"Download failed: {str(e)}"
                update_status(error_message)
                messagebox.showerror("Error", error_message)
            finally:
                downloading = False
                progress_bar.stop()
                progress_bar.pack_forget()

        # Disable buttons during download
        download_btn.configure(state="disabled")
        if is_playlist:
            playlist_download_btn.configure(state="disabled")
            fetch_btn.configure(state="disabled")
        
        # Start download thread
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
        
        # Check thread status and re-enable buttons
        def check_thread():
            if thread.is_alive():
                root.after(1000, check_thread)
            else:
                download_btn.configure(state="normal")
                if is_playlist:
                    playlist_download_btn.configure(state="normal")
                    fetch_btn.configure(state="normal")
        
        check_thread()

    def fetch_videos():
        playlist_url = playlist_url_entry.get()
        if not playlist_url:
            messagebox.showerror("Error", "Please enter a playlist URL.")
            return
        
        try:
            update_status("Fetching playlist videos...")
            playlist_title, videos = update_video_list(playlist_url, video_listbox)
            update_status(f"Found {len(videos)} videos in playlist: {playlist_title}")
        except Exception as e:
            error_msg = f"Error fetching playlist: {str(e)}"
            update_status(error_msg)
            messagebox.showerror("Error", error_msg)

    # Add a clear status button
    def clear_status():
        status_text.delete(1.0, END)
        update_status("Status cleared.")

    clear_status_btn = ctk.CTkButton(status_frame, text="Clear Status",
                                   command=clear_status, width=100,
                                   height=30)
    clear_status_btn.pack(side="bottom", padx=10, pady=5)

    # Add keyboard shortcuts
    def handle_keypress(event):
        if event.state == 4:  # Ctrl key
            if event.keysym == 'v':  # Ctrl+V
                try:
                    url = root.clipboard_get()
                    if "youtube.com" in url or "youtu.be" in url:
                        if show_frame == "single":
                            single_url_entry.delete(0, END)
                            single_url_entry.insert(0, url)
                        else:
                            playlist_url_entry.delete(0, END)
                            playlist_url_entry.insert(0, url)
                except:
                    pass

    root.bind('<Key>', handle_keypress)

    # Add more tooltips
    create_tooltip(clear_status_btn, "Clear the status messages")
    create_tooltip(fetch_btn, "Fetch videos from playlist")
    create_tooltip(playlist_download_btn, "Start downloading the playlist")
    create_tooltip(downloads_label, "Total number of successful downloads")

    # Style the scrollbar to match dark theme
    style = ttk.Style()
    style.configure("TScrollbar", background="#2b2b2b", troughcolor="#2b2b2b",
                   bordercolor="#2b2b2b", arrowcolor="white")
    style.configure("TProgressbar", background="#28a745", troughcolor="#2b2b2b",
                   bordercolor="#2b2b2b")

    root.mainloop()

if __name__ == "__main__":
    setup_gui()