import json
import paho.mqtt.client as mqtt
import time

class MQTTsensores:
    def __init__(self, comunicador,almacenamiento):
        self.comunicador = comunicador
        self.almacenamiento=almacenamiento
        self.debug = True
        
        # Configuración MQTT 
        self.broker_sensores = "broker.emqx.io"
        self.port_sensores = 1883
        self.topics_sensores = [
            "sensor/data/sen55", 
            "sensor/data/gas_sensor",
            "sensor/data/temperatura",
            "sensor/data/humedad"
        ]
        
        # Crear cliente MQTT para sensores
        self.client_sensores = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client_sensores.on_connect = self.on_connect_sensores
        self.client_sensores.on_message = self.on_message_sensores
        
        self.conectado = False

    def set_almacenamiento(self, almacenamiento):
        """Asignar sistema de almacenamiento"""
        self.almacenamiento = almacenamiento

    def conectar_sensores(self):
        #Conectar al broker MQTT de sensores
        try:
            self.client_sensores.connect(self.broker_sensores, self.port_sensores, 60)
            self.client_sensores.loop_start()
            self.conectado = True
            if self.debug:
                print("Conectado al broker MQTT de sensores")
            return True
        except Exception as e:
            print(f"Error conectando a MQTT sensores: {e}")
            return False

    def desconectar_sensores(self):
        # Desconectar del broker MQTT de sensores
        if self.conectado:
            self.client_sensores.loop_stop()
            self.client_sensores.disconnect()
            self.conectado = False
            if self.debug:
                print(" Desconectado del broker MQTT de sensores")

    def on_connect_sensores(self, client, userdata, flags, reason_code, properties):
        """Callback cuando se conecta al broker de sensores"""
        if reason_code == 0:
            if self.debug:
                print("Conexión exitosa al broker MQTT de sensores")
            # Suscribirse a los temas
            for topic in self.topics_sensores:
                client.subscribe(topic)
                if self.debug:
                    print(f" Suscrito al tema: {topic}")
        else:
            print(f"Error de conexión MQTT sensores, código: {reason_code}")

    def on_message_sensores(self, client, userdata, msg):
        """Callback cuando llegan mensajes de sensores"""
        try:
            # Decodificar mensaje JSON
            payload = json.loads(msg.payload.decode("utf-8"))
            
            print(f"\n DATOS DE SENSOR RECIBIDOS:")
            print(f"   Tema: {msg.topic}")
            print(f"   Datos: {json.dumps(payload, indent=2)}")
            
            # GUARDAR DATOS DE SENSOR
            if self.almacenamiento:
                self.almacenamiento.guardar_dato_sensor(msg.topic, payload)

            # Enviar datos importantes por Meshtastic
            self.enviar_por_meshtastic(msg.topic, payload)
            
        except json.JSONDecodeError as e:
            print(f"Error decodificando JSON: {e}")
        except Exception as e:
            print(f"Error procesando mensaje de sensor: {e}")

    def enviar_por_meshtastic(self, topic, datos):
        """Enviar datos importantes por la red Meshtastic"""
        try:
            mensaje = f"Sensor: {topic} - "
            
            if "temperature" in datos:
                mensaje += f"Temp: {datos['temperature']}°C "
            if "humidity" in datos:
                mensaje += f"Hum: {datos['humidity']}% "
            if "co2" in datos:
                mensaje += f"CO2: {datos['co2']}ppm "
            if "pm2_5" in datos:
                mensaje += f"PM2.5: {datos['pm2_5']}µg/m³"
                
            # Limitar longitud del mensaje
            if len(mensaje) > 200:
                mensaje = mensaje[:197] + "..."
                
            # Enviar por Meshtastic si hay datos relevantes
            if len(mensaje) > 15:  # Si hay datos suficientes
                from meshtastic import BROADCAST_NUM
                self.comunicador.send_message(BROADCAST_NUM, mensaje)
                if self.debug:
                    print(f"Enviado por Meshtastic: {mensaje}")
                    
        except Exception as e:
            print(f" Error enviando por Meshtastic: {e}")

    def agregar_topic(self, nuevo_topic):
        """Agregar un nuevo tema a la suscripción"""
        if nuevo_topic not in self.topics_sensores:
            self.topics_sensores.append(nuevo_topic)
            if self.conectado:
                self.client_sensores.subscribe(nuevo_topic)
            if self.debug:
                print(f" Nuevo tema agregado: {nuevo_topic}")