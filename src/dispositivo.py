#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import BROADCAST_NUM, protocols
import paho.mqtt.client as mqtt
import random
import __pycache__
import time
import ssl
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import re



#################################
# Program Base Functions
    
class Dispositivo:
    def __init__(self):
       
        
        # Generate 4 random hexadecimal characters to create a unique node name
        self.random_hex_chars = ''.join(random.choices('0123456789abcdef', k=4))
        self.node_name = '!abcd9296' #+ self.random_hex_chars
        self.node_number = int(self.node_name.replace("!", ""), 16)
        self.global_message_id = random.getrandbits(32)
        self.client_short_name = "IVC"
        self.client_long_name = "Isabel"
        self.lat = "0"
        self.lon = "0"
        self.alt = "0"
        self.client_hw_model = 255


        
        #################################
        ### Program variables

        self.default_key = "1PG7OiApB1nwvP+rz05pAQ==" # AKA AQ==
    