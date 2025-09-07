import socket
import ssl
import threading
import tkinter as tk
from tkinter import colorchooser, messagebox
import tkinter.font as tkFont
from PIL import Image, ImageTk
import json

SERVER_LIST = [
    ("Server 1", "192.168.226.143", 5555),
    ("Server 2", "192.168.112.143", 5555),
    ("Server 3", "192.168.155.143", 5555)
]

class WhiteboardClient:
    def __init__(self):
        self.selected_server_ip = None
        self.selected_server_port = None
        self.username = ""
        self.mode = "draw"
        self.color = "black"
        self.old_x = None
        self.old_y = None
        self.stroke_size = None
        self.eraser_size = None

        self.action_history = []
        self.redo_stack = []

        self.bg_owner = None  # Tracks who owns the last background color
        self.drawing_users = set()  # Track usernames currently drawing

        self.select_server_window()#pops up to select server 

        self.root = tk.Tk()
        self.root.title("🎨 Collaborative Whiteboard")
        self.root.geometry("1600x900")
        self.root.configure(bg="#f0f8ff")
        self.custom_font = tkFont.Font(family="Arial Black", size=10, weight="bold")
        self.root.withdraw()
        self.show_login_window()

        self.canvas = tk.Canvas(self.root, bg="white", width=1300, height=800)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.reset_position)
        self.canvas.bind("<Button-1>", self.fill_area)

        self.sidebar = tk.Frame(self.root, width=200, bg="light blue")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self.sidebar, text="👥 Connected Users", bg="#d6eaf8", font=("Arial", 12, "bold")).pack(pady=10)
        self.user_listbox = tk.Listbox(self.sidebar, width=25)
        self.user_listbox.pack(padx=10, pady=5, fill=tk.Y)

        self.status_label = tk.Label(self.sidebar, text="", bg="light blue", fg="dark green", font=("Arial", 10, "italic"))
        self.status_label.pack(pady=5)

        tk.Button(self.sidebar, text="🎨 Pick Color", command=self.choose_color).pack(pady=5)

        self.stroke_size = tk.Scale(self.sidebar, from_=1, to=30, orient=tk.HORIZONTAL, label="✏ Stroke Size", bg="white")
        self.stroke_size.set(2)
        self.stroke_size.pack(pady=5)

        self.eraser_size = tk.Scale(self.sidebar, from_=5, to=30, orient=tk.HORIZONTAL, label="🪝 Eraser Size", bg="white")
        self.eraser_size.set(10)
        self.eraser_size.pack(pady=5)

        self.draw_btn = tk.Button(self.sidebar, text="✏ Draw", command=self.set_draw_mode)
        self.draw_btn.pack(pady=5)

        self.erase_btn = tk.Button(self.sidebar, text="❌ Erase", command=self.set_erase_mode)
        self.erase_btn.pack(pady=5)

        self.fill_btn = tk.Button(self.sidebar, text="🖌 Background Color", command=self.set_fill_mode)
        self.fill_btn.pack(pady=5)
        
        self.mode_buttons = {
            "draw": (self.draw_btn, "white"),
            "erase": (self.erase_btn, "white"),
            "fill": (self.fill_btn, "white")
        }

        tk.Button(self.sidebar, text="↩ Undo", command=self.undo_last).pack(pady=5)
        tk.Button(self.sidebar, text="↪ Redo", command=self.redo_last).pack(pady=5)

        context = ssl._create_unverified_context()#TCP SOCKET
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client = context.wrap_socket(raw_socket, server_hostname=self.selected_server_ip)
        self.client.connect((self.selected_server_ip, self.selected_server_port))

        self.client.sendall((self.username + "\n").encode())
        threading.Thread(target=self.receive_data, daemon=True).start()
        self.root.mainloop()

    def select_server_window(self):
        window = tk.Tk()
        window.title("Choose Server")
        window.geometry("400x300")
        window.resizable(False, False)
        tk.Label(window, text="Select a server:", font=("Arial", 14)).pack(pady=20)
        for name, ip, port in SERVER_LIST:
            def connect(ip=ip, port=port):
                self.selected_server_ip = ip
                self.selected_server_port = port
                window.destroy()
            tk.Button(window, text=name + f" ({ip})", command=connect, font=("Arial", 12)).pack(pady=5)
        window.mainloop()

    def show_login_window(self):
        # login = tk.Toplevel()
        # login.title("Enter your name")
        # login.geometry("400x200")
        login_window = tk.Toplevel()
        login_window.title("\U0001f3a8 Collaborative Whiteboard")
        login_window.geometry("600x400")
        login_window.resizable(False, False)
        
        bg_img = Image.open("C:/python3/python/17.jpeg")
        bg_img = bg_img.resize((600, 400), Image.LANCZOS)
        bg_photo = ImageTk.PhotoImage(bg_img)

        bg_label = tk.Label(login_window, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        tk.Label(login_window, text="Collaborative Whiteboard", font=("Arial Black", 20, "bold"), bg="#ffffff").place(relx=0.5, rely=0.25, anchor="center")
        tk.Label(login_window, text="Enter your name:", font=("Arial Black", 16, "bold"), bg="#ffffff").place(relx=0.5, rely=0.45, anchor="center")
        name_entry = tk.Entry(login_window, font=("Arial", 12))
        name_entry.place(relx=0.5, rely=0.53, anchor="center", width=160)

        def submit():
            self.username = name_entry.get().strip()
            if self.username:
                login_window.destroy()
                self.root.deiconify()
            else:
                messagebox.showerror("Error", "Please enter a name.")

        tk.Button(login_window, text="JOIN", command=submit, font=("Arial", 10, "bold")).place(relx=0.5, rely=0.61, anchor="center")
        login_window.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.wait_window(login_window)

    def draw(self, event):
        if self.mode not in ["draw", "erase"]:
            return
        if self.old_x and self.old_y:
            width = self.stroke_size.get() if self.mode == "draw" else self.eraser_size.get()
            color = self.color if self.mode == "draw" else "white"
            self.canvas.create_line(self.old_x, self.old_y, event.x, event.y, fill=color, width=width, capstyle=tk.ROUND, smooth=True)
            action = {
                "type": "erase" if self.mode == "erase" else "draw",
                "user": self.username,
                "x1": self.old_x, "y1": self.old_y,
                "x2": event.x, "y2": event.y,
                "color": color,
                "width": width
            }
            self.action_history.append(action)
            self.redo_stack.clear()
            self.send(action)
        self.old_x = event.x
        self.old_y = event.y
        self.send({"type": "status", "user": self.username, "status": "drawing"})

    def reset_position(self, event):
        self.old_x = None
        self.old_y = None
        self.send({"type": "status", "user": self.username, "status": "idle"})

    def choose_color(self):
        color = colorchooser.askcolor(color=self.color)[1]
        if color:
            self.color = color

    def set_draw_mode(self):
        self.mode = "draw"
        self.highlight_selected_mode("draw")
        
    def set_erase_mode(self):
        self.mode = "erase"
        self.highlight_selected_mode("erase")
        
    def set_fill_mode(self):
        self.mode = "fill"
        self.highlight_selected_mode("fill")
        
    def highlight_selected_mode(self, selected_mode):
        for mode, (btn, color) in self.mode_buttons.items():
            btn.configure(bg="red" if mode == selected_mode else color)
            
    def fill_area(self, event):
        if self.mode != "fill":
            return
        old_bg = self.canvas["bg"]
        self.canvas.configure(bg=self.color)
        action = {
            "type": "fill",
            "user": self.username,
            "color": self.color,
            "prev_color": old_bg
        }
        self.bg_owner = self.username
        self.action_history.append(action)
        self.redo_stack.clear()
        self.send(action)

    def undo_last(self):
        if not self.action_history:
            return
        last = self.action_history[-1]
        if last["type"] == "fill" and last["user"] != self.bg_owner:
            return
        if last["type"] in ["draw", "erase"] and last["user"] != self.username:
            return
        self.action_history.pop()
        self.redo_stack.append(last)
        self.send({"type": "undo", "action": last})

    def redo_last(self):
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        if action["type"] == "fill" and action["user"] != self.bg_owner:
            return
        if action["type"] in ["draw", "erase"] and action["user"] != self.username:
            return
        self.action_history.append(action)
        self.send({"type": "redo", "action": action})

    def send(self, data):
        try:
            self.client.sendall((json.dumps(data) + "\n").encode())
        except:
            pass

    def receive_data(self):
        buffer = ""
        while True:
            try:
                chunk = self.client.recv(1024).decode()
                if not chunk:
                    break
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_message(json.loads(line))
            except:
                break

    def handle_message(self, msg):
        if msg["type"] == "userlist":
            self.user_listbox.delete(0, tk.END)
            for user in msg["users"]:
                self.user_listbox.insert(tk.END, user)
        elif msg["type"] in ["draw", "erase"]:
            self.canvas.create_line(msg["x1"], msg["y1"], msg["x2"], msg["y2"],
                                    fill=msg["color"], width=msg["width"], capstyle=tk.ROUND, smooth=True)
        elif msg["type"] == "fill":
            self.canvas.configure(bg=msg["color"])
        elif msg["type"] == "undo":
            self.handle_undo_redo(msg["action"], undo=True)
        elif msg["type"] == "redo":
            self.handle_undo_redo(msg["action"], undo=False)
        elif msg["type"] == "status":
            if msg["status"] == "drawing":
                self.drawing_users.add(msg["user"])
            else:
                self.drawing_users.discard(msg["user"])
            self.update_status()

    def handle_undo_redo(self, action, undo):
        if action["type"] == "fill":
            color = action["prev_color"] if undo else action["color"]
            self.canvas.configure(bg=color)
        elif action["type"] in ["draw", "erase"]:
            if undo:
                # no way to remove exact lines, hide by drawing white
                self.canvas.create_line(action["x1"], action["y1"], action["x2"], action["y2"],
                                        fill="white", width=action["width"], capstyle=tk.ROUND, smooth=True)
            else:
                self.canvas.create_line(action["x1"], action["y1"], action["x2"], action["y2"],
                                        fill=action["color"], width=action["width"], capstyle=tk.ROUND, smooth=True)

    def update_status(self):
        if self.drawing_users:
            text = "\n".join([f"{u} is drawing now..." for u in self.drawing_users])
            self.status_label.config(text=text)
        else:
            self.status_label.config(text="")

if __name__ == "__main__":
    WhiteboardClient()