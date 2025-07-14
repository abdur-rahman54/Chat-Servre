import socket
import threading
import ssl
from datetime import datetime

class AWSChatServer:
    def __init__(self, host='0.0.0.0', port=5555, certfile=None, keyfile=None):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if certfile and keyfile:
            self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(100)  # Higher connection limit
        self.clients = {}
        self.running = True
        self.log_file = "chat_server.log"
        
        print(f"AWS Chat Server started on {host}:{port}")
        self.log(f"Server started at {datetime.now()}")

    def log(self, message):
        """Log server activities"""
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now()} - {message}\n")

    def broadcast(self, message, sender=None):
        """Send message to all connected clients"""
        for client_socket in list(self.clients.keys()):
            if client_socket != sender:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    self.remove_client(client_socket)

    def handle_client(self, conn, address):
        """Handle individual client connections with SSL"""
        try:
            client_socket = self.context.wrap_socket(conn, server_side=True)
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            
            if not nickname or len(nickname) > 20:
                client_socket.send("Invalid nickname".encode('utf-8'))
                client_socket.close()
                return
                
            self.clients[client_socket] = {'nickname': nickname, 'address': address}
            join_msg = f"{nickname} joined the chat!"
            self.broadcast(join_msg, client_socket)
            self.log(f"{nickname} connected from {address}")
            
            while self.running:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if not message:
                    break
                if message.lower() == '/exit':
                    break
                    
                full_msg = f"{nickname}: {message}"
                self.broadcast(full_msg, client_socket)
                self.log(f"Message from {nickname}: {message}")
                
        except Exception as e:
            self.log(f"Error with {address}: {str(e)}")
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        """Clean up disconnected clients"""
        if client_socket in self.clients:
            nickname = self.clients[client_socket]['nickname']
            leave_msg = f"{nickname} left the chat"
            self.broadcast(leave_msg)
            self.log(leave_msg)
            try:
                client_socket.close()
            except:
                pass
            del self.clients[client_socket]

    def start(self):
        """Start accepting connections"""
        try:
            while self.running:
                conn, address = self.server_socket.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(conn, address),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.running = False
            for client in list(self.clients.keys()):
                self.remove_client(client)
            self.server_socket.close()
            self.log("Server stopped")

if __name__ == "__main__":
    # Generate certs first: openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    server = AWSChatServer(
        port=5555,
        certfile="cert.pem",  # Path to your certificate
        keyfile="key.pem"     # Path to your private key
    )
    server.start()
