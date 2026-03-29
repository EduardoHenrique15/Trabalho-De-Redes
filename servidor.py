import socket
import json

def iniciar_servidor():
    HOST, PORT = '127.0.0.1', 5000
    JANELA_CONFIG = 5
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(1)
    
    print(f"[*] Servidor pronto em {HOST}:{PORT}")

    conn, addr = servidor.accept()
    
    try:
        while True:
            raw_data = conn.recv(1024).decode()
            if not raw_data: break
            
            pacote = json.loads(raw_data)
            tipo = pacote.get("tipo")
            seq = pacote.get("seq")
            payload = pacote.get("payload")

            if tipo == "HANDSHAKE":
                print(f"[HANDSHAKE] Recebido: {payload}")
                conn.send(f"OK;{JANELA_CONFIG}".encode())
            
            elif tipo == "DATA":
                print(f"[DATA] Seq: {seq} | Payload: {payload} | Tam: {pacote['tamanho']}")
                
    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        conn.close()
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()