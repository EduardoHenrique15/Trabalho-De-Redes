import socket

def iniciar_servidor():
    HOST = '127.0.0.1' 
    PORT = 5000
    JANELA_INICIAL = 5 

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    servidor.bind((HOST, PORT))
    servidor.listen(1)
    print(f"[*] Servidor aguardando handshake em {HOST}:{PORT}")

    conn, addr = servidor.accept()
    
    try:
        proposta = conn.recv(1024).decode()
        
        if proposta and ";" in proposta:
            tam_max, modo = proposta.split(';')
            print(f"[HANDSHAKE] Cliente definiu limite de {tam_max} caracteres e modo {modo}.")
            
            resposta = f"OK;{JANELA_INICIAL}"
            conn.send(resposta.encode())
            print(f"[*] Handshake concluído. Janela enviada: {JANELA_INICIAL}")
        else:
            print("[ERRO] Formato de handshake inválido.")
            conn.send("ERRO;FORMATO_INVALIDO".encode())

    except Exception as e:
        print(f"[ERRO] Falha: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    iniciar_servidor()