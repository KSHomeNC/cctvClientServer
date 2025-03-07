import paramiko
import os
import posixpath
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from threading import Thread

# SFTP client class
class SFTPClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KSHome SFTP Client Version 1.0")
        self.root.geometry("800x600")
        self.root.configure(bg='light blue')  # Set background color to light blue

        # SFTP server details with default values
        self.hostname = tk.StringVar(value='192.168.12.218')
        self.port = tk.IntVar(value=22)
        self.username = tk.StringVar(value='pi')
        self.password = tk.StringVar(value='pawan@158')
        self.remote_directory = tk.StringVar(value='/mnt/hd/Seagate/KSHome/capture')
        self.local_directory = tk.StringVar()
        self.frame_rate = tk.IntVar(value=35)  # Default frame rate

        # Create GUI elements
        self.create_widgets()

        # SFTP client
        self.client = None
        self.sftp = None

    def create_widgets(self):
        # Server details frame
        server_frame = ttk.LabelFrame(self.root, text="Server Details")
        server_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        server_frame.configure(style="ServerDetails.TLabelframe")

        # Configure style for the server details frame
        style = ttk.Style()
        style.configure("ServerDetails.TLabelframe", background="light green")
        style.configure("ServerDetails.TLabelframe.Label", background="light green")

        # Configure style for the labels and entries inside the server details frame
        style.configure("ServerDetails.TLabel", background="light green")
        style.configure("ServerDetails.TEntry", fieldbackground="light green")

        ttk.Label(server_frame, text="Hostname:", style="ServerDetails.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(server_frame, textvariable=self.hostname, style="ServerDetails.TEntry").grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(server_frame, text="Port:", style="ServerDetails.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(server_frame, textvariable=self.port, style="ServerDetails.TEntry").grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(server_frame, text="Username:", style="ServerDetails.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(server_frame, textvariable=self.username, style="ServerDetails.TEntry").grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(server_frame, text="Password:", style="ServerDetails.TLabel").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(server_frame, textvariable=self.password, show="*", style="ServerDetails.TEntry").grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.connect_button = ttk.Button(server_frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        self.disconnect_button = ttk.Button(server_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.disconnect_button.state(['disabled'])

        # Remote directory frame
        remote_frame = ttk.LabelFrame(self.root, text="Remote Directory")
        remote_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.remote_text = tk.Text(remote_frame, height=20, width=100)  # Increased width
        self.remote_text.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.remote_text.bind('<Double-1>', self.on_remote_text_double_click)

        self.refresh_button = ttk.Button(remote_frame, text="Refresh", command=self.refresh)
        self.refresh_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.refresh_button.state(['disabled'])

        self.delete_button = ttk.Button(remote_frame, text="Delete", command=self.delete_selected_items)
        self.delete_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.delete_button.state(['disabled'])

        # Frame rate input
        ttk.Label(remote_frame, text="Frame Rate:", style="ServerDetails.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(remote_frame, textvariable=self.frame_rate, style="ServerDetails.TEntry").grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Define tags for styling
        self.remote_text.tag_configure('folder', font=('TkDefaultFont', 10, 'bold'), foreground='black')
        self.remote_text.tag_configure('file', font=('TkDefaultFont', 10), foreground='blue')

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.hostname.get(), self.port.get(), self.username.get(), self.password.get())
            self.sftp = self.client.open_sftp()
            messagebox.showinfo("Connection", "Connected to the SFTP server successfully.")
            self.remote_text.delete('1.0', tk.END)
            self._list_files_recursive(self.remote_directory.get())  # Show the default remote folder contents on connect
            self.connect_button.state(['disabled'])
            self.disconnect_button.state(['!disabled'])
            self.refresh_button.state(['!disabled'])
            self.delete_button.state(['!disabled'])
        except Exception as e:
            messagebox.showerror("Connection Error", f"An error occurred while connecting to the SFTP server: {e}")

    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        messagebox.showinfo("Disconnection", "Disconnected from the SFTP server.")
        self.sftp = None
        self.client = None
        self.remote_text.delete('1.0', tk.END)
        self.connect_button.state(['!disabled'])
        self.disconnect_button.state(['disabled'])
        self.refresh_button.state(['disabled'])
        self.delete_button.state(['disabled'])

    def refresh(self):
        if self.sftp:
            self.remote_text.delete('1.0', tk.END)
            self._list_files_recursive(self.remote_directory.get())

    def _list_files_recursive(self, remote_path):
        try:
            files = self.sftp.listdir(remote_path)
            for file in files:
                file_path = posixpath.join(remote_path, file)
                try:
                    if self.is_directory(file_path):
                        relative_path = posixpath.relpath(file_path, self.remote_directory.get())
                        self.remote_text.insert(tk.END, f"[DIR] {relative_path}\n", 'folder')
                        self._list_files_recursive(file_path)  # Recursively list files in subdirectory
                    else:
                        file_size = self.sftp.stat(file_path).st_size
                        relative_path = posixpath.relpath(file_path, self.remote_directory.get())
                        self.remote_text.insert(tk.END, f"{relative_path} ({file_size} bytes)\n", 'file')
                except IOError as e:
                    self.remote_text.insert(tk.END, f"Could not access {file_path}: {e}\n")
        except Exception as e:
            self.remote_text.insert(tk.END, f"An error occurred while listing files: {e}\n")

    def on_remote_text_double_click(self, event):
        index = self.remote_text.index("@%s,%s" % (event.x, event.y))
        line = self.remote_text.get(f"{index} linestart", f"{index} lineend")
        selected_item = line.split(' ')[0].replace("[DIR] ", "")
        full_path = posixpath.join(self.remote_directory.get(), selected_item)
        if self.is_directory(full_path):
            self.remote_text.delete('1.0', tk.END)
            self._list_files_recursive(full_path)
        elif selected_item.endswith('.h264'):
            print(f"Attempting to play video: {full_path}")  # Log the full path
            self.play_video(full_path)

    def delete_selected_items(self):
        try:
            selected_text = self.remote_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            selected_lines = selected_text.strip().split('\n')
            for line in selected_lines:
                selected_item = line.split(' ')[0].replace("[DIR] ", "")
                full_path = posixpath.join(self.remote_directory.get(), selected_item)
                self._delete_recursive(full_path)
            messagebox.showinfo("Deletion", "Selected items deleted successfully.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Deletion Error", f"An error occurred while deleting items: {e}")

    def _delete_recursive(self, path):
        if self.is_directory(path):
            files = self.sftp.listdir(path)
            for file in files:
                file_path = posixpath.join(path, file)
                self._delete_recursive(file_path)
            self.sftp.rmdir(path)
        else:
            self.sftp.remove(path)

    def is_directory(self, path):
        try:
            return self.sftp.stat(path).st_mode & 0o170000 == 0o040000
        except IOError:
            return False

    def play_video(self, video_path):
        local_video_path = os.path.join(os.getcwd(), os.path.basename(video_path))
        try:
            self.sftp.get(video_path, local_video_path)
            Thread(target=self._play_video_thread, args=(local_video_path,)).start()
        except FileNotFoundError as e:
            messagebox.showerror("File Not Found", f"Could not find the file: {video_path}\n{e}")

    def _play_video_thread(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = self.frame_rate.get()
        delay = int(1000 / fps) if fps > 0 else 40  # Default to 25 FPS if FPS is not available
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow('Video Player', frame)
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def browse_local_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.local_directory.set(directory)
            self.remote_text.delete('1.0', tk.END)
            self._list_local_files_recursive(directory, directory)

    def _list_local_files_recursive(self, local_path, base_path):
        for root, dirs, files in os.walk(local_path):
            for file in files:
                file_path = os.path.join(root, file)
                display_path = os.path.relpath(file_path, base_path)
                self.remote_text.insert(tk.END, display_path + '\n', 'file')

# Main function
if __name__ == "__main__":
    root = tk.Tk()
    app = SFTPClientApp(root)
    root.mainloop()