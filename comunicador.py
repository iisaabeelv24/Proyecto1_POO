from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import BROADCAST_NUM, protocols
import paho.mqtt.client as mqtt
import random
import time
import ssl
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import re


class Comunicador:
    def __init__(self, dispositivo):
            self.dispositivo = dispositivo
            #### Debug Options
            self.debug = True
            self.auto_reconnect = True
            self.auto_reconnect_delay = 1 # seconds
            self.print_service_envelope = False
            self.print_message_packet = False

            self.print_node_info =  True
            self.print_node_position = True
            self.print_node_telemetry = True

            self.lat = dispositivo.lat
            self.lon = dispositivo.lon
            self.alt = dispositivo.alt

            ### Default settings
            self.mqtt_broker = "mqtt.meshtastic.org"
            self.mqtt_port = 1883
            self.mqtt_username = "meshdev"
            self.mqtt_password = "large4cats"
            # root_topic = "msh/US/2/e/"
            self.root_topic = "msh/EU_868/ES/2/e/"
            self.channel = "TestMQTT"
            self.key = "ymACgCy9Tdb8jHbLxUxZ/4ADX+BWLOGVihmKHcHTVyo="
            self.message_text = "Person man, person man Hit on the head with a frying pan Lives his life in a garbage can"


            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=True, userdata=None)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
           # self.client.on_message = self.on_message
            self.receptor=None

    def set_receptor(self,receptor):
        self.receptor=receptor
        self.client.on_message = self.receptor.on_message
    
    #configuracion no tocar
    def set_topic(self):
        if self.debug: print("set_topic")
        global subscribe_topic, publish_topic
        node_name = '!' + hex(self.dispositivo.node_number)[2:]
        subscribe_topic = self.root_topic + self.channel + "/#"
        self.publish_topic = self.root_topic + self.channel + "/" + node_name
        publish_topic=self.publish_topic
        
    def xor_hash(self,data):
        result = 0
        for char in data:
            result ^= char
        return result

    def generate_hash(self,name, key):
        replaced_key = key.replace('-', '+').replace('_', '/')
        key_bytes = base64.b64decode(replaced_key.encode('utf-8'))
        h_name = self.xor_hash(bytes(name, 'utf-8'))
        h_key = self.xor_hash(key_bytes)
        result = h_name ^ h_key
        return result
    
    
    #################################
    # MQTT Server 
        
    def connect_mqtt(self):
        ##if "tls_configured" not in self.connect_mqtt.__dict__:          #Persistent variable to remember if we've configured TLS yet
          ##  self.connect_mqtt.tls_configured = False

        if self.debug: print("connect_mqtt")
        #global mqtt_broker, mqtt_port, mqtt_username, mqtt_password, root_topic, channel, node_number, db_file_path, key
        if not self.client.is_connected():
            try:
                if ':' in self.mqtt_broker:
                    self.mqtt_broker,self.mqtt_port = self.mqtt_broker.split(':')
                    self.mqtt_port = int(self.mqtt_port)

                if self.key == "AQ==":
                    if self.debug: print("key is default, expanding to AES128")
                    self.key = "1PG7OiApB1nwvP+rz05pAQ=="

                padded_key = self.key.ljust(len(self.key) + ((4 - (len(self.key) % 4)) % 4), '=')
                replaced_key = padded_key.replace('-', '+').replace('_', '/')
                key = replaced_key

                self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
                if self.mqtt_port == 8883:
                    self.client.tls_set(ca_certs="cacert.pem", tls_version=ssl.PROTOCOL_TLSv1_2)
                    self.client.tls_insecure_set(False)
                    ##self.connect_mqtt.tls_configured = True
                self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
                self.client.loop_start()

            except Exception as e:
                print (e)

    def disconnect_mqtt(self):
        if self.debug: print("disconnect_mqtt")
        if self.client.is_connected():
            self.client.disconnect()

    def on_connect(self,client, userdata, flags, reason_code, properties):
        self.set_topic()
        if client.is_connected():
            print("client is connected")
        
        if reason_code == 0:
            if self.debug: print(f"Connected to sever: {self.mqtt_broker}")
            if self.debug: print(f"Subscribe Topic is: {subscribe_topic}")
            if self.debug: print(f"Publish Topic is: {publish_topic}\n")
            client.subscribe(subscribe_topic)

    def on_disconnect(self,client, userdata, flags, reason_code, properties):
        if self.debug: print("on_disconnect")
        if reason_code != 0:
            if self.auto_reconnect == True:
                print("attempting to reconnect in " + str(self.auto_reconnect_delay) + " second(s)")
                time.sleep(self.auto_reconnect_delay)
                self.connect_mqtt()

   
    #################################
    # Send Messages

    def direct_message(self,destination_id):
        if self.debug: print("direct_message")
        if destination_id:
            try:
                destination_id = int(destination_id[1:], 16)
                self.send_message(destination_id)
            except Exception as e:
                if self.debug: print(f"Error converting destination_id: {e}")

    def send_message(self,destination_id, message_text):
        if not self.client.is_connected():
            self.connect_mqtt

        if message_text:
             #Convierte destination_id a entero
            if isinstance(destination_id,str)and destination_id.startswith('!'):
                destination_id=int(destination_id[1:],16)
            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.TEXT_MESSAGE_APP 
            encoded_message.payload = message_text.encode("utf-8")
            self.generate_mesh_packet(destination_id, encoded_message)
  
        else:
            return

    def send_traceroute(self,destination_id):
        if not self.client.is_connected():
            self.connect_mqtt()
        if self.debug: print(f"Sending Traceroute Packet to {str(destination_id)}")

        if isinstance(destination_id,str)and destination_id.startswith('!'):
            destination_id=int(destination_id[1:],16)
        encoded_message = mesh_pb2.Data()
        encoded_message.portnum = portnums_pb2.TRACEROUTE_APP
        encoded_message.want_response = True

        destination_id = int(destination_id[1:], 16)
        self.generate_mesh_packet(destination_id, encoded_message)

    def send_node_info(self,destination_id, want_response):
        if self.client.is_connected():
            if isinstance(destination_id,str)and destination_id.startswith('!'):
                destination_id=int(destination_id[1:],16)
            user_payload = mesh_pb2.User()
            setattr(user_payload, "id", self.dispositivo.node_name)
            setattr(user_payload, "long_name", self.dispositivo.client_long_name)
            setattr(user_payload, "short_name", self.dispositivo.client_short_name)
            setattr(user_payload, "hw_model", self.dispositivo.client_hw_model)

            user_payload = user_payload.SerializeToString()

            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.NODEINFO_APP
            encoded_message.payload = user_payload
            encoded_message.want_response = want_response  # Request NodeInfo back
            self.generate_mesh_packet(destination_id, encoded_message)

    def send_position(self,destination_id):
        if self.client.is_connected():
            if isinstance(destination_id,str)and destination_id.startswith('!'):
                destination_id=int(destination_id[1:],16)
            pos_time = int(time.time())
            latitude = int(float(self.lat) * 1e7)
            longitude = int(float(self.lon) * 1e7)
            altitude_units = 1 / 3.28084 if 'ft' in str(self.alt) else 1.0
            altitude = int(altitude_units * float(re.sub('[^0-9.]', '', str(self.alt))))

            position_payload = mesh_pb2.Position()
            setattr(position_payload, "latitude_i", latitude)
            setattr(position_payload, "longitude_i", longitude)
            setattr(position_payload, "altitude", altitude)
            setattr(position_payload, "time", pos_time)

            position_payload = position_payload.SerializeToString()

            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.POSITION_APP
            encoded_message.payload = position_payload
            encoded_message.want_response = True

            self.generate_mesh_packet(destination_id, encoded_message)

    def generate_mesh_packet(self,destination_id, encoded_message):
        ##global global_message_id
        mesh_packet = mesh_pb2.MeshPacket()

        if isinstance(destination_id,str)and destination_id.startswith('!'):
                destination_id=int(destination_id[1:],16)

        # Use the global message ID and increment it for the next call
        mesh_packet.id = self.dispositivo.global_message_id
        self.dispositivo.global_message_id += 1
        
        setattr(mesh_packet, "from", self.dispositivo.node_number)
        mesh_packet.to = destination_id
        mesh_packet.want_ack = False
        mesh_packet.channel = self.generate_hash(self.channel, self.key)
        mesh_packet.hop_limit = 3

        if self.key == "":
            mesh_packet.decoded.CopyFrom(encoded_message)
        else:
            mesh_packet.encrypted = self.encrypt_message(self.channel, self.key, mesh_packet, encoded_message)

        service_envelope = mqtt_pb2.ServiceEnvelope()
        service_envelope.packet.CopyFrom(mesh_packet)
        service_envelope.channel_id = self.channel
        service_envelope.gateway_id = self.dispositivo.node_name

        payload = service_envelope.SerializeToString()
        self.client.publish(self.publish_topic, payload)

    def encrypt_message(self,channel, key, mesh_packet, encoded_message):
        mesh_packet.channel = self.generate_hash(channel, key)
        key_bytes = base64.b64decode(key.encode('ascii'))
        nonce_packet_id = mesh_packet.id.to_bytes(8, "little")
        nonce_from_node = self.dispositivo.node_number.to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node
        cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_bytes = encryptor.update(encoded_message.SerializeToString()) + encryptor.finalize()
        return encrypted_bytes

    def send_ack(self,destination_id, message_id):
        if self.debug: print("Sending ACK")
        encoded_message = mesh_pb2.Data()
        encoded_message.portnum = portnums_pb2.ROUTING_APP
        encoded_message.request_id = message_id
        encoded_message.payload = b"\030\000"
        self.generate_mesh_packet(destination_id, encoded_message)

