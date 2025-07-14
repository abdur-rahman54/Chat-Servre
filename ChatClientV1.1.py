import socket
import ssl
import threading
import sys
import time

class AWSChatClient:
    def __init__(self, host, port, nickname):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.running = False
        self.max_retries = 3
        self.retry_delay = 5
        self.connect()
        
    def connect(self):
        """Establish connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.running = True
                
                # Set up SSL context
                self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                self.context.check_hostname = False
                self.context.verify_mode = ssl.CERT_NONE
                
                print(f"\n🔗 Connecting to {self.host}:{self.port} (Attempt {attempt + 1})...")
                self.sock = socket.create_connection((self.host, self.port))
                self.secure_sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
                print("🔒 SSL connection established!")
                
                # Send nickname first
                self.secure_sock.sendall(self.nickname.encode('utf-8'))
                
                # Start receive thread
                threading.Thread(target=self.receive_messages, daemon=True).start()
                
                # Start sending messages
                self.send_messages()
                break
                
            except Exception as e:
                print(f"❌ Connection error: {str(e)}")
                if attempt == self.max_retries - 1:
                    print("🛑 Max retries reached. Giving up.")
                    sys.exit(1)
                
                print(f"⏳ Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                self.cleanup()

    def receive_messages(self):
        while self.running:
            try:
                message = self.secure_sock.recv(1024).decode('utf-8')
                if not message:
                    print("\n🔌 Server closed the connection")
                    break
                print(f"\r{message}\n> ", end="")
            except Exception as e:
                if self.running:  # Only print error if we didn't initiate disconnect
                    print(f"\n⚠️ Receive error: {str(e)}")
                break
        self.running = False

    def send_messages(self):
        try:
            while self.running:
                try:
                    message = input("> ")
                    if not self.running:
                        break
                        
                    if message.lower() == '/exit':
                        self.cleanup()
                        break
                        
                    self.secure_sock.sendall(message.encode('utf-8'))
                except (EOFError, KeyboardInterrupt):
                    print("\n🛑 Disconnecting...")
                    self.cleanup()
                    break
                    
        except Exception as e:
            print(f"\n⚠️ Send error: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        if not self.running:
            return
            
        self.running = False
        try:
            self.secure_sock.sendall('/exit'.encode('utf-8'))
        except:
            pass
        try:
            self.secure_sock.close()
        except:
            pass
        try:
            self.sock.close()
        except:
            pass

if __name__ == "__main__":
    print("\n" + "="*40)
    print("💬 AWS Chat Client")
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
    
    client = AWSChatClient(host, port, nickname)