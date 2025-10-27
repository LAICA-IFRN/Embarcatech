#
# ============================================================================
# Prof EmbarcaTech - Unidade 5, Aula 4: Interfaces Seriais (UART, I²C, SPI) 
# ============================================================================
#
# Placa:      Caninos Loucos Labrador Core v2.2 (32-bits)
#
# Sensor:     BH1750  
# Tipo:       Sensor de Luminosidade Ambiente (Luxímetro)
# Protocolo:  I²C
#
# Autor:      Prof Leonardo Amorim
# Data:       27/10/2025
#
# Descrição:
# Este script inicializa o barramento I2C da Labrador e realiza
# leituras contínuas de iluminância (em Lux) do sensor BH1750.
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
# Importamos I2C e o Erro específico
from periphery import I2C, I2CError

BH1750_ADDR = 0x23  # Endereço (pino ADDR no GND)
MODE_ONE_TIME_HIGH_RES = 0x20 
I2C_BUS = "/dev/i2c-2" 

def ler_luminosidade():
    i2c = None 
    try:
        i2c = I2C(I2C_BUS)
        msg_escrita = I2C.Message([MODE_ONE_TIME_HIGH_RES])
        i2c.transfer(BH1750_ADDR, [msg_escrita])
        
        time.sleep(0.18) # Espera a medição

        msg_leitura = I2C.Message([0, 0], read=True)
        i2c.transfer(BH1750_ADDR, [msg_leitura])
        
        data = msg_leitura.data
        raw_value = (data[0] << 8) | data[1]
        lux = raw_value / 1.2

        return lux

    except I2CError as e:
        print(f"Erro de I2C: {e}")
        return None
    except Exception as e:
        print(f"Um erro inesperado ocorreu: {e}")
        return None
    finally:
        if i2c is not None:
            i2c.close()

if __name__ == "__main__":
    print("Iniciando monitor de luminosidade...")
    print("Pressione Ctrl+C para parar.")
    
    try:
        # Loop infinito
        while True:
            # Chama nossa função de leitura
            nivel_lux = ler_luminosidade()
            
            if nivel_lux is not None:
                # Limpa a linha anterior para uma saída mais limpa
                # (o \r volta ao início da linha, end="" não pula linha)
                print(f"Nível de Iluminância: {nivel_lux:7.2f} Lux", end="\r")
            
            # Pausa por 2 segundos
            time.sleep(2)

    except KeyboardInterrupt:
        # Quando o usuário pressionar Ctrl+C...
        print("\nMonitoramento interrompido pelo usuário.")
    except Exception as e:
        print(f"\nUm erro encerrou o programa: {e}")
