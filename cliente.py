import socket

def realizar_handshake():
    HOST = '127.0.0.1'
    PORT = 5000
    
    # Parâmetros obrigatórios [cite: 7, 33]
    limite_texto = 50  # Deve ser >= 30 [cite: 7]
    modo = "GBN"       # GBN ou SR [cite: 33]

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORT))

    # Envia handshake inicial 
    mensagem = f"{limite_texto};{modo}"
    cliente.send(mensagem.encode())

    # Recebe confirmação e tamanho da janela do servidor [cite: 27, 44]
    confirmacao = cliente.recv(1024).decode()
    status, janela = confirmacao.split(';')
    
    if status == "OK":
        print(f"[SUCCESS] Conectado! Modo: {modo}, Janela do Servidor: {janela}")

    cliente.close()

if __name__ == "__main__":
    realizar_handshake()