import socket
import json
import random
import hashlib

TAXA_DE_PERDA = 0.3
CHAVE_SECRETA = "redes2026"

def decifrar_simetrico(texto_hex, chave):
    try:
        texto_original = ""
        bytes_lista = [int(texto_hex[i:i+2], 16) for i in range(0, len(texto_hex), 2)]
        for i, valor_byte in enumerate(bytes_lista):
            caractere_chave = chave[i % len(chave)]
            texto_original += chr(valor_byte ^ ord(caractere_chave))
        return texto_original
    except Exception:
        return "[ERRO AO DECIFRAR: Dados corrompidos de forma irrecuperável]"

def calcular_checksum_servidor(payload):
    return hashlib.md5(str(payload).encode('utf-8')).hexdigest()

def iniciar_servidor():
    HOST, PORT = '127.0.0.1', 5000
    JANELA_CONFIG = 5
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(1)
    
    print(f"[*] Servidor pronto em {HOST}:{PORT}")
    print(f"[*] Simulação de perda ativa: {TAXA_DE_PERDA * 100}% de chance de descarte.")

    conn, addr = servidor.accept()
    
    modo_operacao = "GBN"
    proximo_seq_esperado = 0  
    buffer_sr = {}            
    
    try:
        while True:
            raw_data = conn.recv(1024).decode()
            if not raw_data: break
            
            pacote = json.loads(raw_data)
            tipo = pacote.get("tipo")
            seq = pacote.get("seq")
            payload = pacote.get("payload")

            if tipo == "HANDSHAKE":
                _, modo_operacao = payload.split(';')
                print(f"\n[HANDSHAKE] Configurado Modo: {modo_operacao}")
                conn.send(f"OK;{JANELA_CONFIG}".encode())
                proximo_seq_esperado = 0
                buffer_sr.clear()
            
            elif tipo == "DATA":
                checksum_recebido = pacote.get("checksum")
                checksum_recalculado = calcular_checksum_servidor(payload)
                
                if checksum_recebido != checksum_recalculado:
                    print(f"❌ [ERRO DE INTEGRIDADE] Pacote Seq {seq} veio corrompido!")
                    print(f"   -> [AÇÃO] Descartando pacote modificado.")
                    if modo_operacao == "GBN":
                        ultimo_ack_valido = max(0, proximo_seq_esperado - 1)
                        resposta_ack = {"tipo": "ACK", "ack": ultimo_ack_valido}
                        conn.send(json.dumps(resposta_ack).encode())
                    continue 
                
                if random.random() < TAXA_DE_PERDA:
                    print(f"🔥 [PERDA SIMULADA] Pacote Seq {seq} foi 'perdido' no canal!")
                    continue 
                
                payload_decifrado = decifrar_simetrico(payload, CHAVE_SECRETA)
                print(f"[RECEBIDO COM SUCESSO] Seq: {seq}")
                print(f"   -> Texto Cifrado Recebido: '{payload}'")
                print(f"   -> Texto Decifrado com Sucesso: '{payload_decifrado}'")
                
                if modo_operacao == "GBN":
                    if seq == proximo_seq_esperado:
                        print(f"   -> [GBN] Sequência correta!")
                        proximo_seq_esperado += 1
                        resposta_ack = {"tipo": "ACK", "ack": seq}
                        conn.send(json.dumps(resposta_ack).encode())
                    else:
                        print(f"   -> [GBN] Fora de ordem! Esperado: {proximo_seq_esperado}. Descartando.")
                        ultimo_ack_valido = max(0, proximo_seq_esperado - 1)
                        resposta_ack = {"tipo": "ACK", "ack": ultimo_ack_valido}
                        conn.send(json.dumps(resposta_ack).encode())

                elif modo_operacao == "SR":
                    print(f"   -> [SR] Enviando ACK individual para Seq {seq}.")
                    buffer_sr[seq] = payload_decifrado
                    resposta_ack = {"tipo": "ACK", "ack": seq}
                    conn.send(json.dumps(resposta_ack).encode())
                                
    except Exception as e:
        print(f"[ERRO] {e}")
    finally:
        conn.close()
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()