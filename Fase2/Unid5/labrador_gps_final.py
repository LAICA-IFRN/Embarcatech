#
# ============================================================================
# Prof EmbarcaTech - Unidade 5, Aula 4: Interfaces Seriais (UART, I²C, SPI) 
# ============================================================================
#
# Placa:      Caninos Loucos Labrador Core v2.2 (32-bits)
#
# Sensor:     GY-GPS6MV2 (baseado no U-blox NEO-6M) 
# Tipo:       Módulo Receptor GPS
# Protocolo:  UART (Serial TTL 3,3V)
#
# Autor:      Prof Leonardo Amorim
# Data:       26/10/2025
#
# Descrição:
# Este script configura a porta UART da Labrador para receber
# dados NMEA do módulo GPS. Ele faz o parsing (análise) das
# sentenças para extrair latitude, longitude e hora.
# 
# Conexão:
# VCC (GPS) -> Pino 5V (Labrador - Pino 2 ou 4) - Crucial, pois o módulo
# tem regulador e alimentar em 3,3V não resolverá​
# GND (GPS) -> Pino GND (Labrador)​
# TXD (GPS / Transmissão) -> Pino 10 (Labrador / UART0_RX)​
# RXD (GPS / Recepção) -> Pino 8 (Labrador / UART0_TX)​
# Antena GPS: Conectada firmemente e posicionada com boa visibilidade do céu.
#
# ============================================================================
#

import time
import serial
import sys
import pynmea2
from datetime import datetime, timedelta

# --- Configuração ---
SERIAL_PORT = "/dev/ttyS0"
BAUD_RATE = 9600
TIMEZONE_OFFSET = timedelta(hours=-3) # Offset para GMT-3
PRINT_INTERVAL = 30 # Intervalo de impressão em segundos

ser = None
last_print_time = 0 # Guarda o tempo da última impressão

# Variáveis para armazenar os últimos dados válidos
last_valid_data = {
    "utc_time": None,
    "local_time": None,
    "latitude": 0.0,
    "longitude": 0.0,
    "speed_kmh": 0.0,
    "num_sats": 0,
    "quality": "Inválido",
    "altitude": 0.0,
    "status": "V"
}

print(f"Iniciando exemplo GPS (Parte 4 - Filtrado) na porta {SERIAL_PORT} @ {BAUD_RATE} bps")
print(f"Imprimindo dados a cada {PRINT_INTERVAL} segundos quando o status for ATIVO.")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Porta serial aberta. Aguardando fix do GPS...")

    while True:
        line_bytes = ser.readline()
        current_time = time.monotonic() # Tempo atual para controle de impressão

        if line_bytes:
            try:
                line_str = line_bytes.decode('ascii').strip()
                if line_str.startswith('$'):
                    try:
                        msg = pynmea2.parse(line_str)

                        # Atualiza os dados armazenados conforme as mensagens chegam
                        if isinstance(msg, pynmea2.types.talker.RMC):
                            last_valid_data["status"] = msg.status
                            if hasattr(msg, 'timestamp') and msg.timestamp and \
                               hasattr(msg, 'datestamp') and msg.datestamp:
                                try:
                                    utc_datetime = datetime.combine(msg.datestamp, msg.timestamp)
                                    local_datetime = utc_datetime + TIMEZONE_OFFSET
                                    last_valid_data["utc_time"] = msg.timestamp
                                    last_valid_data["local_time"] = local_datetime.time() # Guarda como objeto time
                                except TypeError:
                                     last_valid_data["utc_time"] = None
                                     last_valid_data["local_time"] = None
                            # Atualiza lat/lon apenas se o status for A
                            if msg.status == 'A':
                                last_valid_data["latitude"] = msg.latitude
                                last_valid_data["longitude"] = msg.longitude
                            else: # Se perder o fix, zera lat/lon
                                last_valid_data["latitude"] = 0.0
                                last_valid_data["longitude"] = 0.0


                        elif isinstance(msg, pynmea2.types.talker.GGA):
                             if last_valid_data["status"] == 'A': # Usa dados GGA apenas com fix
                                qualidade_map = ["Inválido", "GPS fix", "DGPS fix", "PPS fix", "RTK", "Float RTK", "Estimado", "Manual", "Simulação"]
                                qual_idx = int(msg.gps_qual)
                                last_valid_data["num_sats"] = int(msg.num_sats) if msg.num_sats else 0
                                last_valid_data["quality"] = qualidade_map[qual_idx] if qual_idx < len(qualidade_map) else "Desconhecido"
                                last_valid_data["altitude"] = float(msg.altitude) if msg.altitude else 0.0
                             else:
                                last_valid_data["num_sats"] = 0
                                last_valid_data["quality"] = "Inválido"
                                last_valid_data["altitude"] = 0.0

                        elif isinstance(msg, pynmea2.types.talker.VTG):
                             if last_valid_data["status"] == 'A': # Usa velocidade apenas com fix
                                last_valid_data["speed_kmh"] = float(msg.spd_over_grnd_kmph) if msg.spd_over_grnd_kmph is not None else 0.0
                             else:
                                last_valid_data["speed_kmh"] = 0.0

                    except pynmea2.ParseError:
                        pass # Ignora erros de parse NMEA silenciosamente
            except UnicodeDecodeError:
                pass # Ignora erros de decodificacao silenciosamente

        # --- Lógica de Impressão ---
        # Verifica se o status é Ativo E se passou o intervalo de tempo
        if last_valid_data["status"] == 'A' and (current_time - last_print_time >= PRINT_INTERVAL):
            print("-" * 30)
            print(f"Hora UTC:   {last_valid_data['utc_time']}")
            print(f"Hora Local: {last_valid_data['local_time']}")
            print(f"Latitude:   {last_valid_data['latitude']:.6f}") # 6 casas decimais
            print(f"Longitude:  {last_valid_data['longitude']:.6f}") # 6 casas decimais
            print(f"Velocidade: {last_valid_data['speed_kmh']:.2f} km/h")
            print(f"Satélites:  {last_valid_data['num_sats']}")
            print(f"Qualidade:  {last_valid_data['quality']}")
            print(f"Altitude:   {last_valid_data['altitude']:.1f} M")
            
            last_print_time = current_time # Atualiza o tempo da última impressão

        elif current_time - last_print_time >= 5: # Imprime status a cada 5s se nao tiver fix
             if last_valid_data["status"] != 'A':
                 print(f"...aguardando fix do GPS (Status: {last_valid_data['status']})")
                 last_print_time = current_time # Atualiza para nao floodar

except serial.SerialException as e:
    print(f"\nERRO: Não foi possível abrir a porta serial {SERIAL_PORT}.")
except KeyboardInterrupt:
    print("\nLeitura interrompida pelo usuário.")
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
    import traceback
    traceback.print_exc()
finally:
    if ser and ser.is_open:
        ser.close()
        print("Porta serial fechada.")

print("Programa finalizado.")
