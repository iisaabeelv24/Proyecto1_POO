#!/usr/bin/env python3

from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import BROADCAST_NUM, protocols
import paho.mqtt.client as mqtt
import random
import time
import ssl
import base64
import re
import queue
import threading
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.DEBUG)



# MESHTASTIC 


class MeshtasticClient:
    def __init__(self, message_handler=None):
        """
        Initialize client with configuration.

        message_handler: callable(msg_dict) that will be called for each RX
        message processed in the RX thread. If None, messages are kept in
        `rx_queue` for the GUI to poll.
        """

        
        self.node_name = '!abcd9296'
        self.node_number = int(self.node_name.replace("!", ""), 16)
        self.global_message_id = random.getrandbits(32)
        self.client_short_name = "IVC"
        self.client_long_name = "Isabel"

        
        self.mqtt_broker = "mqtt.meshtastic.org"
        self.mqtt_port = 1883
        self.mqtt_username = "meshdev"
        self.mqtt_password = "large4cats"
        self.root_topic = "msh/EU_868/ES/2/e/"
        self.channel = "TestMQTT"
        self.key = "ymACgCy9Tdb8jHbLxUxZ/4ADX+BWLOGVihmKHcHTVyo="
        self.message_text = "Test---- Vive o Mueres"

        
        random_hex_chars = ''.join(random.choices('0123456789abcdef', k=4))
        self.node_name = '!abcd' + random_hex_chars
        self.node_number = int(self.node_name.replace('!', ''), 16)
        self.global_message_id = random.getrandbits(32)

        
        self.subscribe_topic = None
        self.publish_topic = None

    
        self.debug = True
        self.print_service_envelope = False
        self.print_message_packet = False

       
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="",
            clean_session=True,
            userdata=None
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message_mqtt

      
        self.rx_queue = queue.Queue()
        self._rx_thread = None
        self._rx_thread_stop = threading.Event()

        
        self.tx_queue = queue.Queue()
        self._tx_thread = None
        self._tx_thread_stop = threading.Event()

       
        self.message_handler = message_handler

        self.texto = ""

   

    def set_topic(self):
        node_name = '!' + hex(self.node_number)[2:]
        self.subscribe_topic = self.root_topic + self.channel + "/#"
        self.publish_topic = self.root_topic + self.channel + "/" + node_name

        if self.debug:
            logging.debug(f"subscribe: {self.subscribe_topic} publish: {self.publish_topic}")

    def xor_hash(self, data: bytes) -> int:
        result = 0
        for char in data:
            result ^= char
        return result

    def generate_hash(self, name: str, key: str) -> int:
        replaced_key = key.replace('-', '+').replace('_', '/')
        key_bytes = base64.b64decode(replaced_key.encode('utf-8'))
        h_name = self.xor_hash(name.encode('utf-8'))
        h_key = self.xor_hash(key_bytes)
        return h_name ^ h_key

    
    # MQTT: CONECTADO Y DESCONECTADO

    def connect(self):
        if not self.client.is_connected():
            try:
                if ':' in self.mqtt_broker:
                    self.mqtt_broker, self.mqtt_port = self.mqtt_broker.split(':')
                    self.mqtt_port = int(self.mqtt_port)

                if self.key == "AQ==":
                    if self.debug:
                        logging.debug("expanding default key")

                    self.key = "1PG7OiApB1nwvP+rz05pAQ=="

                padded_key = self.key.ljust(
                    len(self.key) + ((4 - (len(self.key) % 4)) % 4), '='
                )

                replaced_key = padded_key.replace('-', '+').replace('_', '/')
                self.key = replaced_key

                self.client.username_pw_set(self.mqtt_username, self.mqtt_password)

                if self.mqtt_port == 8883:
                    self.client.tls_set(
                        ca_certs="cacert.pem",
                        tls_version=ssl.PROTOCOL_TLSv1_2
                    )
                    self.client.tls_insecure_set(False)

                self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
                self.client.loop_start()

            except Exception as e:
                logging.exception("MQTT connect failed")

    def disconnect(self):
        if self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()

    

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.set_topic()

        if reason_code == 0:
            logging.info(f"Connected to server: {self.mqtt_broker}")
            client.subscribe(self.subscribe_topic)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        logging.warning("MQTT disconnected")

    def _on_message_mqtt(self, client, userdata, msg):
        try:
            self.rx_queue.put_nowait((msg.topic, msg.payload))
        except queue.Full:
            logging.warning("RX queue full, dropping message")

    
    # PROCESA MENSAJE
    

    def _process_incoming(self, topic, payload):
        se = mqtt_pb2.ServiceEnvelope()

        try:
            se.ParseFromString(payload)
            mp = se.packet

        except Exception as e:
            logging.exception(f"ServiceEnvelope parse failed: {e}")
            return None

        if mp.HasField("encrypted") and not mp.HasField("decoded"):
            try:
                mp = self._decode_encrypted(mp)
            except Exception:
                return None

        portNumInt = mp.decoded.portnum if mp.HasField("decoded") else None
        handler = protocols.get(portNumInt) if portNumInt else None

        pb = None
        if handler and handler.protobufFactory and mp.HasField("decoded"):
            try:
                pb = handler.protobufFactory()
                pb.ParseFromString(mp.decoded.payload)
            except Exception:
                pb = None

        pb_str = None
        if pb:
            pb_str = str(pb).replace('\n', ' ').replace('\r', ' ').strip()
            mp.decoded.payload = pb_str.encode('utf-8')

        msg_dict = {
            'topic': topic,
            'service_envelope': se,
            'mesh_packet': mp,
            'decoded_payload': (
                pb_str if pb_str else
                (mp.decoded.payload if mp.HasField('decoded') else None)
            )
        }

        return msg_dict

    def _decode_encrypted(self, mp):
        key_bytes = base64.b64decode(self.key.encode('ascii'))
        nonce_packet_id = getattr(mp, "id").to_bytes(8, "little")
        nonce_from_node = getattr(mp, "from").to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node

        cipher = Cipher(
            algorithms.AES(key_bytes),
            modes.CTR(nonce),
            backend=default_backend()
        )

        decryptor = cipher.decryptor()
        decrypted_bytes = decryptor.update(getattr(mp, "encrypted")) + decryptor.finalize()

        data = mesh_pb2.Data()
        data.ParseFromString(decrypted_bytes)
        mp.decoded.CopyFrom(data)
        return mp

    
    # RX HILO

    def start_rx_thread(self):
        if self._rx_thread and self._rx_thread.is_alive():
            return

        self._rx_thread_stop.clear()

        self._rx_thread = threading.Thread(
            target=self._rx_worker,
            daemon=True
        )
        self._rx_thread.start()

    def stop_rx_thread(self):
        if self._rx_thread:
            self._rx_thread_stop.set()
            self._rx_thread.join(timeout=2)

    def _rx_worker(self):
        while not self._rx_thread_stop.is_set():

            try:
                topic, payload = self.rx_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                msg = self._process_incoming(topic, payload)

                if msg:
                    if self.message_handler:
                        try:
                            self.message_handler(msg)
                        except Exception:
                            logging.exception("message_handler raised")

                    else:
                        if not hasattr(self, 'rx_queue_processed'):
                            self.rx_queue_processed = queue.Queue()

                        try:
                            self.rx_queue_processed.put_nowait(msg)
                        except queue.Full:
                            logging.warning("Processed queue full, dropping message")

            finally:
                self.rx_queue.task_done()

    
    # TX HILO
    

    def start_tx_thread(self):
        if self._tx_thread and self._tx_thread.is_alive():
            return

        self._tx_thread_stop.clear()

        self._tx_thread = threading.Thread(
            target=self._tx_worker,
            daemon=True
        )
        self._tx_thread.start()

    def stop_tx_thread(self):
        if self._tx_thread:
            self._tx_thread_stop.set()
            self._tx_thread.join(timeout=2)

    def _tx_worker(self):
        while not self._tx_thread_stop.is_set():
            self.send_message(BROADCAST_NUM, "[IVC]: " + self.texto)

    
    # EVIO MENSAJES
    

    def _generate_mesh_packet(self, destination_id, encoded_message):
        mesh_packet = mesh_pb2.MeshPacket()

        mesh_packet.id = self.global_message_id
        self.global_message_id += 1

        setattr(mesh_packet, "from", self.node_number)
        mesh_packet.to = destination_id
        mesh_packet.want_ack = False
        mesh_packet.channel = self.generate_hash(self.channel, self.key)
        mesh_packet.hop_limit = 3

        if self.key == "":
            mesh_packet.decoded.CopyFrom(encoded_message)
        else:
            mesh_packet.encrypted = self._encrypt_message(mesh_packet, encoded_message)

        service_envelope = mqtt_pb2.ServiceEnvelope()
        service_envelope.packet.CopyFrom(mesh_packet)
        service_envelope.channel_id = self.channel
        service_envelope.gateway_id = self.node_name

        payload = service_envelope.SerializeToString()
        self.client.publish(self.publish_topic, payload)

    def _encrypt_message(self, mesh_packet, encoded_message):
        mesh_packet.channel = self.generate_hash(self.channel, self.key)

        key_bytes = base64.b64decode(self.key.encode('ascii'))

        nonce_packet_id = mesh_packet.id.to_bytes(8, "little")
        nonce_from_node = self.node_number.to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node

        cipher = Cipher(
            algorithms.AES(key_bytes),
            modes.CTR(nonce),
            backend=default_backend()
        )

        encryptor = cipher.encryptor()
        encrypted_bytes = (
            encryptor.update(encoded_message.SerializeToString()) +
            encryptor.finalize()
        )

        return encrypted_bytes

    def send_message(self, message_text):
        destination_id = BROADCAST_NUM

        if not self.client.is_connected():
            self.connect()

        if message_text:
            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.TEXT_MESSAGE_APP
            encoded_message.payload = message_text.encode('utf-8')

            self._generate_mesh_packet(destination_id, encoded_message)

    def send_node_info(self, destination_id, want_response=False):
        if self.client.is_connected():
            user_payload = mesh_pb2.User()

            setattr(user_payload, "id", self.node_name)
            setattr(user_payload, "long_name", self.client_long_name)
            setattr(user_payload, "short_name", self.client_short_name)
            setattr(user_payload, "hw_model", 255)

            user_payload = user_payload.SerializeToString()

            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.NODEINFO_APP
            encoded_message.payload = user_payload
            encoded_message.want_response = want_response

            self._generate_mesh_packet(destination_id, encoded_message)

    def send_position(self, destination_id):
        if self.client.is_connected():
            pos_time = int(time.time())

            latitude = int(float(self.lat) * 1e7)
            longitude = int(float(self.lon) * 1e7)

            altitude_units = 1 / 3.28084 if 'ft' in str(self.alt) else 1.0
            altitude = int(
                altitude_units * float(
                    re.sub('[^0-9.]', '', str(self.alt))
                )
            )

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

            self._generate_mesh_packet(destination_id, encoded_message)


# MAIN EJEMPLO

'''
def print_handler(msg):
    print("RX:", msg.get('decoded_payload'))
    time.sleep(3)

if __name__ == "__main__":
    client = MeshtasticClient(message_handler=print_handler)
    client.connect()
    client.start_rx_thread()
    client.start_tx_thread()

    try:
        print("Meshtastic client running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.stop_rx_thread()
        client.disconnect()
'''
