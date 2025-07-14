import socket
import ssl
import threading
import sys

class AWSChatClient:
    def __init__(self, host, port, nickname):
        self.nickname = nickname
        self.running = True
        
        # Set up SSL context
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE  # For self-signed certs
        
        try:
            print(f"\n🔗 Connecting to {host}:{port}...")
            self.sock = socket.create_connection((host, port))
            self.secure_sock = self.context.wrap_socket(self.sock, server_hostname=host)
            print("🔒 SSL connection established!")
            
            # Send nickname first
            self.secure_sock.sendall(nickname.encode('utf-8'))
            
            # Start receive thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            # Start sending messages
            self.send_messages()
            
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            self.cleanup()

    def receive_messages(self):
        while self.running:
            try:
                message = self.secure_sock.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"\r{message}\n> ", end="")
            except:
                break
        print("\n🔌 Disconnected from server")
        self.running = False

    def send_messages(self):
        try:
            while self.running:
                message = input("> ")
                if not self.running:
                    break
                if message.lower() == '/exit':
                    self.secure_sock.sendall(message.encode('utf-8'))
                    break
                self.secure_sock.sendall(message.encode('utf-8'))
        except KeyboardInterrupt:
            print("\n🛑 Closing connection...")
        except:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        try:
            self.secure_sock.close()
        except:
            pass
        try:
            self.sock.close()
        except:
            pass

def get_client_info():
    """Get connection details from user"""
    print("\n" + "="*40)
    print("💬 AWS Chat Client Setup")
    print("="*40)
    
    host = input("Enter server IP [localhost]: ") or "localhost"
    port = 5555
    nickname = input("Enter your nickname: ").strip()
    
    try:
        port = int(port)
        if not (0 < port < 65536):
            raise ValueError
    except ValueError:
        print("❌ Invalid port number. Using default 5555")
        port = 5555
    
    if not nickname or len(nickname) > 20:
        print("❌ Nickname must be 1-20 characters")
        sys.exit(1)
    
    return host, port, nickname

if __name__ == "__main__":
    host, port, nickname = get_client_info()
    client = AWSChatClient(host, port, nickname)