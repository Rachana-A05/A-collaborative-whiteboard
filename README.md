# 🎨 Collaborative Whiteboard

A **real-time multiplayer collaborative whiteboard application** built using Python.  
This application allows multiple users to connect to a shared canvas, draw together, erase content, change backgrounds, and see updates instantly.

The system uses a **client-server architecture** with **SSL-encrypted socket communication** to provide secure real-time collaboration.

---

## ✨ Features

### 👥 Real-Time Collaboration
- Multiple users can connect to a shared whiteboard
- Drawing actions are synchronized instantly
- Central server manages all connected clients

### ✏ Drawing Tools
- Freehand drawing
- Adjustable brush size
- Color selection
- Smooth canvas interaction

### 🧹 Editing Features
- Eraser tool with adjustable size
- Background color fill
- Undo and redo support
- Maintains drawing history

### 🔒 Secure Communication
- Socket-based client-server communication
- SSL encryption for secure data transfer
- Reliable communication between users

### 🖥 User Interface
- Interactive GUI using Tkinter
- Simple and user-friendly design

---

## 🏗️ Architecture

```
              Client 1
                  |
                  |
              Client 2
                  |
                  |
          SSL Socket Server
                  |
                  |
          Shared Whiteboard State
                  |
                  |
              Client 3
```

### Server
- Accepts multiple client connections
- Receives drawing events
- Broadcasts updates
- Handles communication between users

### Client
- Provides the drawing interface
- Sends user actions
- Receives updates from other users

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3 | Application development |
| Tkinter | GUI interface |
| Socket Programming | Networking |
| SSL | Secure communication |
| Pillow (PIL) | Image processing |
| JSON | Message formatting |

---

## 📂 Project Structure

```
Collaborative-Whiteboard
│
├── client.py          # Client-side GUI application
├── server.py          # Server-side connection handler
├── certificates/      # SSL certificate files
│
├── README.md          # Project documentation
└── requirements.txt   # Dependencies
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/your-username/A-collaborative-whiteboard.git
```

### Navigate to project folder

```bash
cd A-collaborative-whiteboard
```

### Install dependencies

```bash
pip install pillow
```

---

## ▶️ How to Run

### Start Server

```bash
python server.py
```

### Start Client

Open another terminal:

```bash
python client.py
```

Run the client multiple times to connect multiple users.

---

## 🎯 Applications

- Online collaborative drawing
- Virtual classrooms
- Remote team meetings
- Brainstorming sessions
- Interactive learning platforms

---

## 🚀 Future Enhancements

- User authentication
- Integrated chat system
- Save/export drawings
- Cloud deployment
- More drawing tools
- Database support

---

## 👩‍💻 Authors

**Rachana A**  
**Priyanka M P**

---

⭐ Developed as a collaborative networking project using Python socket programming.
