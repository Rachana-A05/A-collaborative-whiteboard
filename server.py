import socket
import threading
import json
import ssl

clients = []  # List of (socket, username)
background_stack = []
background_redo_stack = []
drawing_stacks = {}  # username -> list of drawing actions
drawing_redo_stacks = {}  # username -> list of redo actions
drawing_status = set()
bg_owner = None

def broadcast_user_list():
    usernames = [uname for _, uname in clients]
    message = json.dumps({"type": "userlist", "users": usernames}) + "\n"
    for client_socket, _ in clients:
        try:
            client_socket.sendall(message.encode())
        except Exception as e:
            print(f"❌ Error sending user list: {e}")


def broadcast_message(message, exclude_socket=None):
    if isinstance(message, dict):
        message = json.dumps(message)
    message += "\n"
    for client_socket, _ in clients:
        if client_socket != exclude_socket:
            try:
                client_socket.sendall(message.encode())
            except Exception as e:
                print(f"❌ Error broadcasting message: {e}")

def handle_client(client_socket, address):
    global bg_owner

    try:
        username = client_socket.recv(1024).decode().strip()
        if not username:
            raise ValueError("Empty username")
        print(f"✅ New connection from {address} as '{username}'")
        clients.append((client_socket, username))
        drawing_stacks[username] = []
        drawing_redo_stacks[username] = []
        broadcast_user_list()
    except Exception as e:
        print(f"❌ Failed to receive username: {e}")
        client_socket.close()
        return

    buffer = ""
    while True:
        try:
            chunk = client_socket.recv(4096).decode()
            if not chunk:
                break
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    message = json.loads(line)
                    msg_type = message.get("type")

                    if msg_type in ["draw", "erase"]:
                        drawing_stacks[message["user"]].append(message)
                        drawing_redo_stacks[message["user"]].clear()
                        broadcast_message(message, exclude_socket=client_socket)

                    elif msg_type == "fill":
                        bg_owner = message["user"]
                        background_stack.append(message["color"])
                        background_redo_stack.clear()
                        broadcast_message(message)

                    elif msg_type == "undo":
                        action = message.get("action")
                        user = action.get("user")
                        if action["type"] == "fill":
                            if user == bg_owner and background_stack:
                                last = background_stack.pop()
                                background_redo_stack.append(last)
                                prev = background_stack[-1] if background_stack else "white"
                                broadcast_message({"type": "fill", "color": prev})
                        elif action["type"] in ["draw", "erase"]:
                            if user in drawing_stacks and drawing_stacks[user]:
                                drawing_redo_stacks[user].append(action)
                                drawing_stacks[user].remove(action)
                                broadcast_message({"type": "undo", "action": action})

                    elif msg_type == "redo":
                        action = message.get("action")
                        user = action.get("user")
                        if action["type"] == "fill":
                            if user == bg_owner and background_redo_stack:
                                color = background_redo_stack.pop()
                                background_stack.append(color)
                                broadcast_message({"type": "fill", "color": color})
                        elif action["type"] in ["draw", "erase"]:
                            if user in drawing_redo_stacks and action in drawing_redo_stacks[user]:
                                drawing_redo_stacks[user].remove(action)
                                drawing_stacks[user].append(action)
                                broadcast_message({"type": "redo", "action": action})

                    elif msg_type == "status":
                        if message["status"] == "drawing":
                            drawing_status.add(message["user"])
                        else:
                            drawing_status.discard(message["user"])
                        for sock, _ in clients:
                            try:
                                sock.sendall((json.dumps(message) + "\n").encode())
                            except:
                                pass

                except json.JSONDecodeError:
                    continue

        except Exception as e:
            print(f"❌ Error from {username}: {e}")
            break

    print(f"❌ Client '{username}' at {address} disconnected.")
    clients.remove((client_socket, username))
    drawing_stacks.pop(username, None)
    drawing_redo_stacks.pop(username, None)
    drawing_status.discard(username)
    client_socket.close()
    broadcast_user_list()

def start_server():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=r"C:\python3\python\OpenSSL-Win64\bin\cert.pem",
                            keyfile=r"C:\python3\python\OpenSSL-Win64\bin\key.pem")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    SERVER_IP = "0.0.0.0"
    SERVER_PORT = 5555

    try:
        server_socket.bind((SERVER_IP, SERVER_PORT))
    except socket.error as e:
        print(f"❌ Bind failed: {e}")
        return

    server_socket.listen(5)
    print(f"✅ Secure Server started on {SERVER_IP}:{SERVER_PORT}")

    try:
        while True:
            try:
                client_socket, address = server_socket.accept()
                secure_socket = context.wrap_socket(client_socket, server_side=True)
                threading.Thread(target=handle_client, args=(secure_socket, address), daemon=True).start()
            except ssl.SSLError as e:
                print(f"❌ SSL error: {e}")
            except Exception as e:
                print(f"❌ Accept error: {e}")
    except KeyboardInterrupt:
        print("❌ Server shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
