#MESHTASTIC
from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import BROADCAST_NUM
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import threading
import time



class RecibirMensaje:  
    def __init__(self, comunicador, dispositivo, almacenamiento): 
        self.comunicador = comunicador
        self.dispositivo = dispositivo
        self.almacenamiento = almacenamiento
        #self.gui_callback = self.set_gui_callback
        self.debug = True
        self.print_service_envelope = False
        self.print_message_packet = False
        self.algo = None

        self.mp_1 = None

        
        # Creamos el hilo con nombre 'recibir_mesh'
        self.hilomesh = threading.Thread(target=self.main_thread, name="recibir_mesh", daemon=True)

    def set_gui_callback(self, callback):
        """Asigna el callback para la interfaz gráfica"""
        self.gui_callback = callback


    def set_almacenamiento(self, almacenamiento):
        """Asigna el sistema de almacenamiento de datos"""
        self.almacenamiento = almacenamiento

    def on_message(self, client, userdata, msg):
        """Maneja los mensajes MQTT entrantes"""
        if self.debug:
            print(f" Mensaje recibido en topic: {msg.topic}")
        
        se = mqtt_pb2.ServiceEnvelope()
        try:
            se.ParseFromString(msg.payload)
            if self.print_service_envelope:
                print("")
                print("Service Envelope:")
                print(se)
            mp = se.packet
            if self.print_message_packet: 
                print("")
                print("Message Packet:")
                print(mp)
        except Exception as e:
            print(f"*** Error ServiceEnvelope: {str(e)}")
            return
            
        if mp.HasField("encrypted") and not mp.HasField("decoded"):
            self.decode_encrypted(mp)

        # Procesar el mensaje
        #self.procesar_mensaje(mp)
        self.mp_1 = mp

    def procesar_mensaje(self, mp):
        """Procesa los mensajes según su tipo (portnum)"""
        if not mp.HasField("decoded"):
            return

        portnum = mp.decoded.portnum
        remitente = f"!{hex(getattr(mp, 'from'))[2:]}"
        mensaje_gui = ""

        if portnum == portnums_pb2.TEXT_MESSAGE_APP:
            mensaje = mp.decoded.payload.decode('utf-8', errors='ignore')
            mensaje_gui = f" Mensaje de texto de {remitente}: {mensaje}"
            print(f" Mensaje de texto de {remitente}: {mensaje}")
            # guarda mensajes
            if self.almacenamiento:
                self.almacenamiento.guardar_mensaje(mensaje, remitente, "texto")
            
        elif portnum == portnums_pb2.NODEINFO_APP:
            user = mesh_pb2.User()
            user.ParseFromString(mp.decoded.payload)
            nombre_nodo = user.long_name or user.short_name or "Desconocido"
            mensaje_gui = f" Información de nodo {remitente}: {nombre_nodo}"
            print(f"  Información de nodo {remitente}: {nombre_nodo}")
            
            #  guarda info del nodo
            if self.almacenamiento:
                info_nodo = f"Nombre: {nombre_nodo}, HW: {user.hw_model}"
                self.almacenamiento.guardar_mensaje(info_nodo, remitente, "nodeinfo")
                
        elif portnum == portnums_pb2.POSITION_APP:
            position = mesh_pb2.Position()
            position.ParseFromString(mp.decoded.payload)
            lat = position.latitude_i / 1e7
            lon = position.longitude_i / 1e7
            alt = position.altitude
            print(f" Posición de {remitente}: Lat={lat}, Lon={lon}, Alt={alt}m")
            
            # guarda pos.gps
            if self.almacenamiento:
                self.almacenamiento.guardar_posicion(lat, lon, alt, remitente)
                
        elif portnum == portnums_pb2.TELEMETRY_APP:
            telemetry = mesh_pb2.Telemetry()
            telemetry.ParseFromString(mp.decoded.payload)
            if telemetry.HasField("device_metrics"):
                bateria = telemetry.device_metrics.battery_level
                print(f" Telemetría de {remitente}: Batería={bateria}%")

                #  guarda telemetría
                if self.almacenamiento:
                    telemetria_info = f"Batería: {bateria}%"
                    self.almacenamiento.guardar_mensaje(telemetria_info, remitente, "telemetria")
                
        elif portnum == portnums_pb2.TRACEROUTE_APP:
            print(f" Traceroute recibido de {remitente}")
            
        elif portnum == portnums_pb2.ROUTING_APP:
            print(f" Mensaje de routing/ACK de {remitente}")
            
        elif portnum == portnums_pb2.ADMIN_APP:
            mensaje_gui = f"  Mensaje administrativo de {remitente}"
            print(f"  Mensaje administrativo de {remitente}")
            
        else:
            mensaje_gui = f"TIPO {portnum} de {remitente}"
            print(f" Mensaje tipo {portnum} de {remitente}: {mp.decoded.payload}")

        #print(f" Procesado mensaje del puerto {portnum} de {remitente}")
        #print(f"Payload bruto: {mp.decoded.payload}")
        self.algo = mp.decoded.payload
        #if self.gui_callback and mensaje_gui:
        #self.gui_callback(mensaje_gui)

    def decode_encrypted(self, mp):
        """Descifra mensajes encriptados"""
        try:
            #  Usa la key del comunicador
            key_bytes = base64.b64decode(self.comunicador.key.encode('ascii'))
            nonce_packet_id = getattr(mp, "id").to_bytes(8, "little")
            nonce_from_node = getattr(mp, "from").to_bytes(8, "little")
            nonce = nonce_packet_id + nonce_from_node
            cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_bytes = decryptor.update(getattr(mp, "encrypted")) + decryptor.finalize()
            data = mesh_pb2.Data()
            data.ParseFromString(decrypted_bytes)
            mp.decoded.CopyFrom(data)
        except Exception as e:
            if self.print_message_packet:
                print(f" No se pudo descifrar: {mp}")
            if self.debug: 
                print(f"Error de descifrado: {str(e)}")
            return

    def configurar_debug(self, service_envelope=False, message_packet=False):
        """Configura opciones de debug"""
        self.print_service_envelope = service_envelope
        self.print_message_packet = message_packet

    def main_thread(self):
        
        while True:
            try:
                #print(f"Ejecutando en el hilo: {threading.current_thread().name}")
                if self.mp_1 != None:
                    self.procesar_mensaje(self.mp_1)
                time.sleep(2)
            except KeyboardInterrupt:
                print("Saliendo...")
        


    def init_thread(self):
        self.hilomesh.start()
        self.hilomesh.join()




def main():
    #comunicador = comunicador(dispositivo)
    #dispositivo = dispositivo()
    #almacenamiento = almacenamiento()
    
    rx_messsgr = RecibirMensaje()
    rx_messsgr.init_thread()
    



    print("El hilo ha finalizado.")  

if __name__ == "__main__":
    main()