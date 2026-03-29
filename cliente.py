import socket
import json

class ProtocoloTransporte:
    def __init__(self, limite, modo):
        self.limite = limite
        self.modo = modo
        self.seq_num = 0
        self.janela_tamanho = 0

    def criar_pacote(self, tipo, payload):
        pacote = {
            "tipo": tipo,
            "seq": self.seq_num,
            "payload": payload,
            "tamanho": len(str(payload))
        }
        if tipo == "DATA":
            self.seq_num += 1
        return json.dumps(pacote).encode()

def realizar_handshake():
    HOST, PORT = '127.0.0.1', 5000
    
    print("--- Configuração do Cliente ---")
    while True:
        try:
            limite = int(input("Limite de caracteres (mínimo 30): "))
            if limite >= 30: break
            print("Erro: O limite deve ser >= 30.")
        except ValueError:
            print("Erro: Insira um número inteiro.")
    
    while True:
        modo = input("Modo de operação (GBN ou SR): ").upper()
        if modo in ["GBN", "SR"]: break
        print("Erro: Escolha GBN ou SR.")
    
    proto = ProtocoloTransporte(limite, modo)
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        cliente.connect((HOST, PORT))
        pacote_handshake = proto.criar_pacote("HANDSHAKE", f"{limite};{modo}")
        cliente.send(pacote_handshake)
        
        resposta_raw = cliente.recv(1024).decode()
        if "OK" in resposta_raw:
            _, jan = resposta_raw.split(';')
            proto.janela_tamanho = int(jan)
            print(f"\n[SISTEMA] Handshake aceito. Janela: {jan}")
            
            while True:
                texto = input("Mensagem > ")
                if texto.lower() == 'sair': break
                
                pacote_dados = proto.criar_pacote("DATA", texto)
                cliente.send(pacote_dados)
                
    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        cliente.close()

if __name__ == "__main__":
    realizar_handshake()