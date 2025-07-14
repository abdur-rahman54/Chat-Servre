import socket
import threading
import ssl
from datetime import datetime

class AWSChatServer:
    def __init__(self, host='0.0.0.0', port=5555, certfile=None, keyfile=None):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if certfile and keyfile:
            try:
                self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            except FileNotFoundError as e:
                raise Exception(f"SSL certificate error: {str(e)}")
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(100)
        self.clients = {}
        self.running = True
        self.log_file = "chat_server.log"
        self.lock = threading.Lock()
        
        print(f"\n🚀 Chat Server started on {host}:{port}")
        self.log(f"Server started at {datetime.now()}")

    def log(self, message):
        """Log server activities"""
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now()} - {message}\n")
        print(f"📝 {message}")

    def broadcast(self, message, sender=None):
        """Send message to all connected clients"""
        with self.lock:
            for client_socket in list(self.clients.keys()):
                if client_socket != sender:
                    try:
                        client_socket.send(message.encode('utf-8'))
                    except Exception as e:
                        self.log(f"Error broadcasting to {self.clients[client_socket]['nickname']}: {str(e)}")
                        self.remove_client(client_socket)

    def handle_client(self, conn, address):
        """Handle individual client connections with SSL"""
        client_socket = None
        try:
            client_socket = self.context.wrap_socket(conn, server_side=True)
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            
            if not nickname or not nickname.isprintable() or len(nickname) > 20:
                error_msg = "Invalid nickname (must be 1-20 printable chars)"
                client_socket.send(error_msg.encode('utf-8'))
                raise ValueError(error_msg)
            
            # Clean up any existing connection with same nickname
            with self.lock:
                for sock, info in list(self.clients.items()):
                    if info['nickname'] == nickname:
                        self.remove_client(sock)
            
            # Register new client
            with self.lock:
                self.clients[client_socket] = {'nickname': nickname, 'address': address}
            
            join_msg = f"{nickname} joined the chat!"
            self.broadcast(join_msg, client_socket)
            self.log(f"👋 {nickname} connected from {address[0]}")
            
            # Main message loop
            while self.running:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:  # Empty message means client disconnected
                        break
                        
                    message = message.strip()
                    if message.lower() == '/exit':
                        break
                        
                    full_msg = f"{nickname}: {message}"
                    self.broadcast(full_msg, client_socket)
                    self.log(f"💬 {nickname}: {message}")
                    
                except (ConnectionResetError, ssl.SSLError, socket.error) as e:
                    self.log(f"⚠️ Connection error with {nickname}: {str(e)}")
                    break
                    
        except Exception as e:
            self.log(f"❌ Error with {address[0]}: {str(e)}")
        finally:
            if client_socket:
                self.remove_client(client_socket)
            else:
                try:
                    conn.close()
                except:
                    pass

    def remove_client(self, client_socket):
        """Clean up disconnected clients"""
        with self.lock:
            if client_socket in self.clients:
                nickname = self.clients[client_socket]['nickname']
                leave_msg = f"{nickname} left the chat"
                try:
                    self.broadcast(leave_msg)
                    self.log(f"👋 {leave_msg}")
                    client_socket.close()
                except:
                    pass
                finally:
                    if client_socket in self.clients:
                        del self.clients[client_socket]

    def start(self):
        """Start accepting connections"""
        try:
            while self.running:
                try:
                    conn, address = self.server_socket.accept()
                    self.log(f"🔌 New connection from {address[0]}")
                    threading.Thread(
                        target=self.handle_client,
                        args=(conn, address),
                        daemon=True
                    ).start()
                except OSError as e:
                    if self.running:
                        self.log(f"⚠️ Accept error: {str(e)}")
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
        finally:
            self.running = False
            with self.lock:
                for client in list(self.clients.keys()):
                    self.remove_client(client)
            self.server_socket.close()
            self.log("🛑 Server stopped")

if __name__ == "__main__":
    try:
        print("\n" + "="*40)
        print("💻 AWS Chat Server Setup")
        print("="*40)
        
        host = input("Enter server IP [0.0.0.0]: ") or "0.0.0.0"
        port = input("Enter port [5555]: ") or "5555"
        use_ssl = input("Use SSL/TLS? [y/n]: ").lower() == 'y'
        
        certfile = keyfile = None
        if use_ssl:
            certfile = input("SSL cert file [cert.pem]: ") or "cert.pem"
            keyfile = input("SSL key file [key.pem]: ") or "key.pem"
        
        try:
            port = int(port)
            if not (0 < port < 65536):
                raise ValueError
        except ValueError:
            print("❌ Invalid port number. Using default 5555")
            port = 5555
        
        server = AWSChatServer(host=host, port=port, certfile=certfile, keyfile=keyfile)
        server.start()
    except Exception as e:
        print(f"\n❌ Failed to start server: {str(e)}")