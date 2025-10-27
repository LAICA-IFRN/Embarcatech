#
# ============================================================================
# Prof EmbarcaTech - Unidade 5, aula 4: Interfaces Seriais (UART, I²C, SPI) 
# ============================================================================
#
# Placa:      Caninos Loucos Labrador Core v2.2 (32-bits)
# SDK:        Caninos SDK (https://github.com/caninos-loucos/caninos-sdk)
#
# Sensor:     VL53L0X 
# Tipo:       Sensor de distância a laser
# Protocolo:  Protocolo I²C
#
# Autor:      Prof Leonardo Amorim
# Data:       26/10/2025
#
# Descrição:
# Este script inicializa o barramento I2C da Labrador e realiza
# medições contínuas de distância a cada 1 segundo.
# 
# Conexão:
# SCL (Sensor) -> Pino 5 TWI2_SCLK (Labrador)​
# SDA (Sensor) -> Pino 3 TWI_SDATA (Labrador)​
# VCC (Sensor) -> Pino de 3.3V (Labrador)​
# GND (Sensor) -> Pino GND (Labrador)
#
# ============================================================================
#

import time
import sys
try:
    from smbus2 import SMBus, i2c_msg
except ImportError:
    print("Erro: Biblioteca 'smbus2' não encontrada.")
    print("Instale usando: pip3 install smbus2")
    sys.exit(1)

try:
    import adafruit_vl53l0x
    from adafruit_bus_device.i2c_device import I2CDevice
except ImportError:
    print("Erro: Biblioteca 'adafruit-circuitpython-vl53l0x' não encontrada.")
    print("Instale usando: pip3 install adafruit-circuitpython-vl53l0x")
    sys.exit(1)


# --- A CLASSE-PONTE (Wrapper) ---
# Esta classe "finge" ser um objeto busio.I2C
# traduzindo as chamadas para o smbus2
class SMBus2Wrapper:
    def __init__(self, smbus_bus):
        self.bus = smbus_bus

    def try_lock(self):
        return True # Kernel já gerencia o lock

    def unlock(self):
        pass 

    def __enter__(self):
        self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def writeto(self, address, buffer, *, start=0, end=None):
        if end is None:
            end = len(buffer)
        data_to_write = buffer[start:end]
        if not data_to_write:
            self.bus.write_quick(address)
            return
        reg = data_to_write[0]
        data = list(data_to_write[1:]) 
        if not data:
            self.bus.write_byte(address, reg)
        else:
            self.bus.write_i2c_block_data(address, reg, data)

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        if end is None:
            end = len(buffer)
        in_len = end - start
        in_start = start
        read_msg = i2c_msg.read(address, in_len)
        self.bus.i2c_rdwr(read_msg)
        data_read = list(read_msg)
        for i in range(in_len):
            buffer[in_start + i] = data_read[i]
            
    def writeto_then_readfrom(self, address, buffer_out, buffer_in, *,
                              out_start=0, out_end=None,
                              in_start=0, in_end=None):
        if out_end is None:
            out_end = len(buffer_out)
        if in_end is None:
            in_end = len(buffer_in)
        out_data = buffer_out[out_start:out_end]
        in_len = in_end - in_start
        write_msg = i2c_msg.write(address, out_data)
        read_msg = i2c_msg.read(address, in_len)
        self.bus.i2c_rdwr(write_msg, read_msg)
        data_read = list(read_msg)
        for i in range(in_len):
            buffer_in[in_start + i] = data_read[i]
# --- Fim da Classe-Ponte ---


print("Iniciando exemplo final VL53L0X na Labrador (Unidade 5)")

# --- Configuração ---
I2C_BUS_ID = 2       # /dev/i2c-2
VL53L0X_I2C_ADDR = 0x29

bus = None
vl53 = None

try:
    # 1. Abre o barramento I2C "nativo"
    bus = SMBus(I2C_BUS_ID)
    print(f"Barramento I2C /dev/i2c-{I2C_BUS_ID} aberto.")

    # 2. Cria nossa ponte
    i2c_ponte = SMBus2Wrapper(bus)
    print("Ponte de compatibilidade (Wrapper) criada.")

    # 3. Inicializa o sensor VL53L0X
    print("Inicializando o sensor VL53L0X...")
    vl53 = adafruit_vl53l0x.VL53L0X(i2c_ponte, address=VL53L0X_I2C_ADDR)
    print("Sensor inicializado com sucesso!")
    
    # --- AJUSTE FINO (TUNING) ---
    # Aumenta o tempo de medição para 200ms (200000 microsegundos)
    # O padrão (33000) é rápido, mas propenso a erros (leituras 8190).
    # 200000 é mais lento, porém muito mais estável e preciso.
    vl53.measurement_timing_budget = 200000
    print(f"Tempo de medição ajustado para: {vl53.measurement_timing_budget} us")
    
    # 4. Inicia o loop de medição
    print("\nIniciando medições (Pressione CTRL+C para parar)...")
    while True:
        distancia_mm = vl53.range
        
        if distancia_mm == 8190 or distancia_mm == 8191:
            print("Distância: Fora de alcance (Out of Range)")
        else:
            print(f"Distância: {distancia_mm} mm  ({distancia_mm / 10.0:.1f} cm)")
        
        time.sleep(1.0) # Espera 1 segundo

except IOError as e:
    print(f"\nErro de I/O (IOError): {e}")
except FileNotFoundError:
    print(f"Erro: Barramento /dev/i2c-{I2C_BUS_ID} não encontrado.")
except KeyboardInterrupt:
    print("\nMedição interrompida pelo usuário.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
    import traceback
    traceback.print_exc()
finally:
    if bus:
        bus.close()
        print("Barramento I2C fechado.")

print("Programa finalizado.")
