from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import BROADCAST_NUM
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class RecibirMensaje:  
    def __init__(self, comunicador, dispositivo, almacenamiento): 
        self.comunicador = comunicador
        self.dispositivo = dispositivo
        self.almacenamiento = almacenamiento  
        self.debug = True
        self.print_service_envelope = False
        self.print_message_packet = False

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
        self.procesar_mensaje(mp)

    def procesar_mensaje(self, mp):
        """Procesa los mensajes según su tipo (portnum)"""
        if not mp.HasField("decoded"):
            return

        portnum = mp.decoded.portnum
        remitente = f"!{hex(getattr(mp, 'from'))[2:]}"
        
        if portnum == portnums_pb2.TEXT_MESSAGE_APP:
            mensaje = mp.decoded.payload.decode('utf-8', errors='ignore')
            print(f" Mensaje de texto de {remitente}: {mensaje}")
            
            # guarda mensajes
            if self.almacenamiento:
                self.almacenamiento.guardar_mensaje(mensaje, remitente, "texto")
            
        elif portnum == portnums_pb2.NODEINFO_APP:
            user = mesh_pb2.User()
            user.ParseFromString(mp.decoded.payload)
            nombre_nodo = user.long_name or user.short_name or "Desconocido"
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
            print(f"  Mensaje administrativo de {remitente}")
            
        else:
            print(f" Mensaje tipo {portnum} de {remitente}: {mp.decoded.payload}")

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