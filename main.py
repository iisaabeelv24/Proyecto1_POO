#!/usr/bin/env python3
import time
from pathlib import Path
import os
import threading
from src.jara_comunicador import MeshtasticClient
from src.interfazgrafica import TUFInterface, TUFCommunicator


def main():

    directorio = Path("logs")
    if not directorio.exists():
        print("El directorio 'logs' no existe, creando...")
        directorio.mkdir(parents=True, exist_ok=True)
    else:
        print("El directorio 'logs' existe.")

    print(f"Usando directorio de almacenamiento: {directorio.resolve()}")

    #  INICIA COMUNICADOR MQTT/MESHTASTIC 
    print("Inicializando MeshtasticClient...")
    comunicador_meshtastic = MeshtasticClient()

    comunicador_meshtastic.connect()          # conectar MQTT
    comunicador_meshtastic.start_rx_thread()  # iniciar hilo RX
    #comunicador_meshtastic.start_tx_thread() 

    time.sleep(1)

   
    print("Iniciando Communicador")
    tuf_com = TUFCommunicator("TUF-01", comunicador_meshtastic)

    # INICIA INTERFAZ
    print("Iniciando interfaz gráfica...")
    app = TUFInterface()
    app.mainloop()


if __name__ == "__main__":
    main()
