import socket
import json
import time
import hashlib

CHAVE_SECRETA = "redes2026"

class ProtocoloTransporte:
    def __init__(self, limite, modo):
        self.limite = limite
        self.modo = modo
        self.seq_num = 0
        self.janela_tamanho = 0

    def cifrar_simetrico(self, texto, chave):
        texto_cifrado = ""
        for i, caractere in enumerate(texto):
            caractere_chave = chave[i % len(chave)]
            xor_resultado = ord(caractere) ^ ord(caractere_chave)
            texto_cifrado += f"{xor_resultado:02x}"
        return texto_cifrado

    def calcular_checksum(self, payload):
        return hashlib.md5(str(payload).encode('utf-8')).hexdigest()

    def criar_pacote(self, tipo, payload, seq=None):
        num_seq = seq if seq is not None else self.seq_num
        
        if tipo == "DATA":
            payload_final = self.cifrar_simetrico(payload, CHAVE_SECRETA)
        else:
            payload_final = payload
            
        chk = self.calcular_checksum(payload_final) if tipo == "DATA" else "0"
        
        pacote = {
            "tipo": tipo,
            "seq": num_seq,
            "payload": payload_final,
            "tamanho": len(str(payload_final)),
            "checksum": chk
        }
        if tipo == "DATA" and seq is None:
            self.seq_num += 1
        return json.dumps(pacote).encode()

    def fragmentar_mensagem(self, texto):
        return [texto[i:i+self.limite] for i in range(0, len(texto), self.limite)]

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
            print(f"\n[SISTEMA] Handshake aceito. Janela: {proto.janela_tamanho}")
            
            cliente.settimeout(3.0) 
            
            while True:
                texto = input("\nMensagem > ")
                if texto.lower() == 'sair': break
                
                fragmentos = proto.fragmentar_mensagem(texto)
                pacotes_enviar = []
                
                for frag in fragmentos:
                    pacotes_enviar.append({
                        "seq": proto.seq_num,
                        "payload": frag,
                        "ack_recebido": False
                    })
                    proto.criar_pacote("DATA", frag) 

                base = 0
                total_pacotes = len(pacotes_enviar)
                
                while base < total_pacotes:
                    fim_janela = min(base + proto.janela_tamanho, total_pacotes)
                    for i in range(base, fim_janela):
                        if proto.modo == "GBN" or (proto.modo == "SR" and not pacotes_enviar[i]["ack_recebido"]):
                            p = pacotes_enviar[i]
                            
                            pacote_bytes = proto.criar_pacote("DATA", p["payload"], seq=p["seq"])
                            pacote_dicionario = json.loads(pacote_bytes.decode())
                            
                            print(f"\n[ENVIO] Enviando Seq {p['seq']} | Texto Original: '{p['payload']}'")
                            print(f"        -> Payload Cifrado na rede: '{pacote_dicionario['payload']}'")
                            
                            corromper = input("Deseja corromper a integridade deste pacote cifrado? (s/N): ").lower()
                            if corromper == 's':
                                pacote_dicionario["payload"] = pacote_dicionario["payload"] + "ff"
                                print("⚠️ [TESTE] Payload cifrado alterado para quebrar o checksum!")
                            
                            cliente.send(json.dumps(pacote_dicionario).encode())
                            time.sleep(0.2)
                    
                    try:
                        for _ in range(base, fim_janela):
                            ack_raw = cliente.recv(1024).decode()
                            ack_json = json.loads(ack_raw)
                            ack_seq = ack_json.get("ack")
                            
                            print(f"[ACK] Recebido ACK do Seq: {ack_seq}")
                            
                            if proto.modo == "GBN":
                                for idx in range(base, total_pacotes):
                                    if pacotes_enviar[idx]["seq"] == ack_seq:
                                        base = idx + 1
                                        break
                            
                            elif proto.modo == "SR":
                                for p in pacotes_enviar:
                                    if p["seq"] == ack_seq:
                                        p["ack_recebido"] = True
                                while base < total_pacotes and pacotes_enviar[base]["ack_recebido"]:
                                    base += 1
                                    
                    except socket.timeout:
                        print("\n[TIMEOUT] Tempo esgotado esperando ACK! Retransmitindo janela...\n")
                        
            print("[SISTEMA] Conexão encerrada pelo usuário.")
                
    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        cliente.close()

if __name__ == "__main__":
     realizar_handshake()