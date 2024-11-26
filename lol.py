import asyncio
import websockets
import json
import threading
import socket

class UDPChatServer:
    def __init__(self, host='localhost', udp_port=9999, ws_port=8765):
        self.host = host
        self.udp_port = udp_port
        self.ws_port = ws_port
        self.clients = set()
        
        # Sockets UDP e WebSocket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.udp_port))
        
        # Preparar threads
        self.stop_event = threading.Event()
        self.udp_thread = threading.Thread(target=self.handle_udp_messages)
        
    def handle_udp_messages(self):
        """Lida com mensagens recebidas via UDP"""
        print(f"Servidor UDP aguardando mensagens na porta {self.udp_port}")
        while not self.stop_event.is_set():
            try:
                self.udp_socket.settimeout(1)  # Timeout para verificar stop_event
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode('utf-8')
                print(f"Mensagem UDP recebida de {addr}: {message}")
                
                # Usar run_coroutine_threadsafe para chamar broadcast de forma segura
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(json.dumps({
                        'username': 'UDP',
                        'message': message
                    })), 
                    self.loop
                )
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erro no recebimento UDP: {e}")
    
    async def handle_websocket(self, websocket, path=None):
        """Lida com conexões WebSocket"""
        try:
            self.clients.add(websocket)
            async for message in websocket:
                await self.process_websocket_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print("Conexão WebSocket fechada")
        finally:
            self.clients.remove(websocket)
    
    async def process_websocket_message(self, websocket, message):
        """Processa mensagens recebidas via WebSocket"""
        try:
            data = json.loads(message)
            username = data.get('username', 'Anônimo')
            msg_text = data.get('message', '')
            
            # Enviar para socket UDP
            udp_message = f"{username}: {msg_text}".encode('utf-8')
            self.udp_socket.sendto(udp_message, (self.host, self.udp_port))
            
            # Broadcast para outros clientes WebSocket
            await self.broadcast(json.dumps({
                'username': username, 
                'message': msg_text
            }))
        except Exception as e:
            print(f"Erro no processamento da mensagem: {e}")
    
    async def broadcast(self, message):
        """Envia mensagem para todos clientes WebSocket"""
        if self.clients:
            await asyncio.wait([
                client.send(message) for client in self.clients
            ])
    
    async def start_websocket_server(self):
        """Inicializa o servidor WebSocket"""
        server = await websockets.serve(
            self.handle_websocket, 
            self.host, 
            self.ws_port
        )
        await server.wait_closed()
    
    def start_server(self):
        """Inicializa o servidor"""
        # Criar loop de eventos
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Iniciar thread UDP
        self.udp_thread.start()
        
        # Iniciar servidor WebSocket
        try:
            print(f"Servidor rodando - UDP:{self.udp_port}, WebSocket:{self.ws_port}")
            self.loop.run_until_complete(self.start_websocket_server())
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")
        finally:
            # Parar threads e fechar sockets
            self.stop_event.set()
            self.udp_thread.join()
            self.udp_socket.close()
            self.loop.close()

def main():
    server = UDPChatServer()
    server.start_server()

if __name__ == "__main__":
    main()