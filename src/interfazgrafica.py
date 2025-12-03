import tkinter as tk
from tkinter import ttk
from tkhtmlview import HTMLLabel
from tkintermapview import TkinterMapView
import folium
import base64
import threading
from abc import ABC, abstractmethod
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import BROADCAST_NUM
from src.jara_comunicador import MeshtasticClient


# DECORADORES Y CONSTANTES

def log_action(func):
    def wrapper(*args, **kwargs):
        print(f"Ejecutando: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

BROADCAST_NUM = "broadcast"


# CLASE BASE ABSTRACTA

class TUFDevice(ABC):
    def __init__(self, name):
        self.name = name
        self.receive_callback = None

    @abstractmethod
    def connect(self):
        ...

    @abstractmethod
    def send_data(self, data):
        ...

    @abstractmethod
    def receive_data(self):
        ...

    def set_receive_callback(self, callback):
        self.receive_callback = callback


# MQTT Y MESHTASTIC

class MQTTHandler:
    def connect_mqtt(self):
        print("Conectando a MQTT...")


class MeshtasticHandler:
    def connect_meshtastic(self):
        print("Conectando a Meshtastic...")


# COMUNICADOR 

class TUFCommunicator(TUFDevice, MQTTHandler, MeshtasticHandler):
    def __init__(self, name, comunicador_real=None):
        TUFDevice.__init__(self, name)
        MQTTHandler.__init__(self)
        MeshtasticHandler.__init__(self)

        self.comunicador_real = comunicador_real
        self.key = "1PG7OiApB1nwvP+rz05pAQ=="

    def connect(self):
        if self.comunicador_real:
            try:
                self.comunicador_real.connect_mqtt()
                print(f"{self.name} conectado correctamente.")
                return True
            except Exception as e:
                print(f"Error al conectar: {e}")
                return False
        else:
            print("Conectando a MQTT...")
            print("Conectando a Meshtastic...")
            print(f"{self.name} conectado correctamente.")
            return True

    def send_data(self, data):
        if self.comunicador_real:
            try:
                self.comunicador_real.send_message(BROADCAST_NUM, data)
                print(f"Enviando datos: {data}")
                return True
            except Exception as e:
                print(f"Error al enviar datos: {e}")
                return False
        else:
            print(f"Enviando datos: {data}")
            return True

    def receive_data(self):
        if self.comunicador_real:
            try:
                print("Sistema listo para recibir mensajes...")
                return "Sistema de recepción activo"
            except Exception as e:
                print(f"Error al recibir datos: {e}")
                return f"Error: {e}"
        else:
            print("Recibiendo datos...")
            return "Datos de prueba recibidos"



# RECIBIR MENSAJE
# INTERFAZ GRAFICA 

class TUFInterface(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Interfaz Grafica Meshtastic")
        self.geometry("500x450")

        self.meshtasticd_client = MeshtasticClient(message_handler=self.print_handler)
        self.meshtasticd_client.connect()
        self.meshtasticd_client.start_rx_thread()

        self.temporal_data = ""

        self.create_widgets()

    # INTERFAZ
    def create_widgets(self):
        tk.Label(self, text="Interfaz gráfica Meshtastic", font=("Arial", 14)).pack(pady=10)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        #  PESTAÑA MENSAJES 
        self.tab_mensajes = tk.Frame(self.notebook)
        self.notebook.add(self.tab_mensajes, text="Mensajes")

        tk.Label(self.tab_mensajes, text="Mensajes Recibidos:", font=("Arial", 12)).pack(anchor="w", padx=20)

        frame_mensajes = tk.Frame(self.tab_mensajes)
        frame_mensajes.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(frame_mensajes)
        scrollbar.pack(side="right", fill="y")

        self.lista_mensajes = tk.Listbox(frame_mensajes, yscrollcommand=scrollbar.set, height=15)
        self.lista_mensajes.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.lista_mensajes.yview)

        frame_envio = tk.Frame(self.tab_mensajes)
        frame_envio.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_envio, text="Mensaje a enviar:").pack(anchor="w")
        self.entrada_mensaje = tk.Entry(frame_envio, width=50)
        self.entrada_mensaje.pack(fill="x", pady=2)
        self.entrada_mensaje.bind("<Return>", self.enviar_enter)

        frame_botones = tk.Frame(self.tab_mensajes)
        frame_botones.pack(fill="x", padx=20, pady=10)

        tk.Button(frame_botones, text="Conectar", command=self.connect).pack(side="left", padx=5)
        tk.Button(frame_botones, text="Enviar mensaje", command=self.enviar_mensaje).pack(side="left", padx=5)
        tk.Button(frame_botones, text="Recibir mensajes", command=self.receive_data).pack(side="left", padx=5)
        tk.Button(frame_botones, text="Limpiar", command=self.limpiar_mensajes).pack(side="right", padx=5)

        # PESTAÑA MAPA 
        self.tab_mapa = tk.Frame(self.notebook)
        self.notebook.add(self.tab_mapa, text="Mapa")

        tk.Label(self.tab_mapa, text="MAPA", font=("Arial", 12)).pack(pady=15)

        self.map_widget = TkinterMapView(self.tab_mapa, width=700, height=400, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True, padx=10, pady=10)
        self.map_widget.set_position(19.4326, -99.1332) #coordenadas mexico
        self.map_widget.set_zoom(5)

   
    def print_handler(self, msg):
        texto = msg.get("decoded_payload")
        if isinstance(texto, bytes):
            texto = texto.decode("utf-8", errors="ignore")

        self.after(0, lambda: self.mostrar_mensaje(f"RX: {texto}"))

    def mostrar_mensaje(self, mensaje: str):
        self.lista_mensajes.insert(tk.END, mensaje)
        self.lista_mensajes.see(tk.END)
        try: #extrae coordenadas
            # mensaje tipo JSON
            if isinstance(mensaje, dict) and "lat" in mensaje and "lon" in mensaje:
                self.marcar_en_mapa(mensaje["lat"], mensaje["lon"])
            
            # mensaje en texto 
            elif isinstance(mensaje, str) and "POS:" in mensaje:
                coords = mensaje.replace("POS:", "").split(",")
                lat = float(coords[0])
                lon = float(coords[1])
                self.marcar_en_mapa(lat, lon)

        except Exception as e:
            print(f"Error procesando coordenadas: {e}")


    def marcar_en_mapa(self, lat, lon):
        try:
            if hasattr(self, "mapa") and self.mapa:
            # Centrar el mapa en las coordenadas
                self.mapa.set_position(lat, lon)
                self.mapa.set_zoom(15)
            # Crear marcador visual
                self.mapa.set_marker(lat, lon, text="Última posición")
                print(f"[MAPA] Marcador añadido en: {lat}, {lon}")
            else:
                print("[MAPA] ERROR: self.mapa no existe o no está inicializado")
        except Exception as e:
            print(f"[MAPA ERROR] {e}")

    # ENVIAR
    def enviar_enter(self, event):
        self.enviar_mensaje()

    def enviar_mensaje(self):
        self.temporal_data = self.entrada_mensaje.get().strip()
        if self.temporal_data:
            self.meshtasticd_client.send_message("[IVC]: " + self.temporal_data)
            self.mostrar_mensaje(f"YO: {self.temporal_data}")
            self.entrada_mensaje.delete(0, tk.END)

    
    def limpiar_mensajes(self):
        self.lista_mensajes.delete(0, tk.END)

    @log_action
    def connect(self):
        self.mostrar_mensaje("Sistema conectado")

    @log_action
    def receive_data(self):
        self.mostrar_mensaje("Escuchando mensajes...")

    #  MAPA  
    def cargar_mapa(self, lat, lon):
        mapa = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], popup="Nodo").add_to(mapa)
        mapa.save("mapa_temp.html")

        for widget in self.mapa_frame.winfo_children():
            widget.destroy()

        html_label = HTMLLabel(self.mapa_frame, html=open("mapa_temp.html").read())
        html_label.pack(fill="both", expand=True)



# CLASE DE ALMACENAMIENTO

class AlmacenamientoSimulado:
    def guardar_mensaje(self, mensaje, remitente, tipo):
        print(f"Almacenado {tipo} de {remitente}: {mensaje}")

    def guardar_posicion(self, lat, lon, alt, remitente):
        print(f"Almacenada posicion de {remitente}: {lat}, {lon}, {alt}")



# EJECUCIÓN PRINCIPAL
'''
if __name__ == "__main__":
    app = TUFInterface()
    app.mainloop()
'''
