from meshtastic import BROADCAST_NUM

class InterfazTerminal:
    def __init__(self, comunicador, receptor, mqtt_sensores, almacenamiento):
        self.comunicador = comunicador
        self.receptor = receptor
        self.mqtt_sensores = mqtt_sensores
        self.almacenamiento = almacenamiento
        self.modo_actual = "meshtastic"  # meshtastic, sensores, ambos
    
    def ejecutar_menu(self):
        while True:
            print("\n" + "="*40)
            print("       MESHTASTIC CLIENT")
            print("="*40)
            print(f"Modo actual: {self.modo_actual.upper()}")
            print("="*40)
            print("1.  Enviar mensaje")
            print("2.  Cambiar modo recepción")
            print("3.  Ver datos guardados")
            print("4.  Salir")
            print("="*40)
            
            opcion = input("Selecciona una opción: ")
            
            if opcion == "1":
                self.enviar_mensaje()
            elif opcion == "2":
                self.cambiar_modo_recepcion()
            elif opcion == "3":
                self.ver_datos_guardados()
            elif opcion == "4":
                self.salir()
                break
            else:
                print(" Opción no válida")
    
    def cambiar_modo_recepcion(self):
        print("\n---  SELECCIONAR MODO DE RECEPCIÓN ---")
        print("\n2.  Sensores MQTT ")
        print("\n3.  Ambos modos")
        
        
        opcion = input("\nElige el modo (1-3): ")
        
        if opcion == "1":
            self.activar_meshtastic()
        elif opcion == "2":
            self.activar_sensores()
        elif opcion == "3":
            self.activar_ambos()
        else:
            print(" Opción no válida")
    
    def activar_meshtastic(self):
        """Activa solo recepción Meshtastic"""
        if self.mqtt_sensores and self.mqtt_sensores.conectado:
            self.mqtt_sensores.desconectar_sensores()
            print("🔌 Sensores MQTT desconectados")
        
        if not self.comunicador.client.is_connected():
            self.comunicador.connect_mqtt()
            print(" Conectando a Meshtastic...")
        
        self.modo_actual = "meshtastic"
        print(" Modo: Red Meshtastic activado")
    
    def activar_sensores(self):
        """Activa solo recepción de sensores MQTT"""
        if self.comunicador.client.is_connected():
            self.comunicador.disconnect_mqtt()
            print(" Meshtastic desconectado")
        
        if self.mqtt_sensores and not self.mqtt_sensores.conectado:
            if self.mqtt_sensores.conectar_sensores():
                self.modo_actual = "sensores"
                print(" Modo: Sensores MQTT activado")
            else:
                print(" No se pudo conectar a sensores MQTT")
        elif self.mqtt_sensores:
            self.modo_actual = "sensores"
            print(" Modo: Sensores MQTT activado")
        else:
            print(" Servicio de sensores no disponible")
    
    def activar_ambos(self):
        """Activa ambos modos de recepción"""
        # Conectar Meshtastic si no está conectado
        if not self.comunicador.client.is_connected():
            self.comunicador.connect_mqtt()
            print(" Conectando a Meshtastic...")
        
        # Conectar sensores si están disponibles
        if self.mqtt_sensores and not self.mqtt_sensores.conectado:
            if self.mqtt_sensores.conectar_sensores():
                print(" Conectando a sensores MQTT...")
            else:
                print("  No se pudo conectar a sensores MQTT")
        
        self.modo_actual = "ambos"
        print(" Modo: Meshtastic + Sensores activado")
    
    def enviar_mensaje(self):
        """Envía un mensaje por la red Meshtastic"""
        if not self.comunicador.client.is_connected():
            print(" No conectado a Meshtastic")
            return
        
        mensaje = input("Escribe tu mensaje: ")
        if mensaje:
            self.comunicador.send_message(BROADCAST_NUM, mensaje)
            print(" Mensaje enviado a la red")
            
            # Guardar el mensaje enviado
            if self.almacenamiento:
                nombre_usuario = self.comunicador.dispositivo.client_long_name
                self.almacenamiento.guardar_mensaje(mensaje, nombre_usuario, "enviado")
        else:
            print(" El mensaje no puede estar vacío")
    
    def ver_datos_guardados(self):
        """Muestra estadísticas de datos almacenados"""
        if not self.almacenamiento:
            print(" Sistema de almacenamiento no disponible")
            return
        
        stats = self.almacenamiento.obtener_estadisticas()
        
        print("\n---  DATOS GUARDADOS ---")
        print(f" Mensajes: {stats.get('total_mensajes', 0)}")
        print(f" Posiciones GPS: {stats.get('total_posiciones', 0)}")
        print(f" Datos de sensores: {stats.get('total_sensores', 0)}")
        
        # Mostrar último mensaje
        if stats.get('ultimo_mensaje'):
            ultimo = stats['ultimo_mensaje']
            print(f"\nÚltimo mensaje:")
            print(f"  De: {ultimo.get('remitente', 'Desconocido')}")
            print(f"  Mensaje: {ultimo.get('mensaje', '')}")
            print(f"  Hora: {ultimo.get('timestamp', '')}")
        
        # Mostrar última posición
        if stats.get('ultima_posicion'):
            ultima = stats['ultima_posicion']
            coords = ultima.get('coordenadas', {})
            print(f"\nÚltima posición:")
            print(f"  De: {ultima.get('remitente', 'Desconocido')}")
            print(f"  Lat: {coords.get('latitud', 'N/A')}")
            print(f"  Lon: {coords.get('longitud', 'N/A')}")
            print(f"  Hora: {ultima.get('timestamp', '')}")
        
        # Opción para exportar
        exportar = input("\n¿Exportar a archivo TXT? (s/n): ").lower()
        if exportar == 's':
            if self.almacenamiento.exportar_txt():
                print(" Datos exportados correctamente")
            else:
                print(" Error al exportar datos")
    
    def salir(self):
        """Cierra todas las conexiones y sale"""
        print("\n Cerrando aplicación...")
        
        # Desconectar sensores MQTT
        if self.mqtt_sensores and self.mqtt_sensores.conectado:
            self.mqtt_sensores.desconectar_sensores()
            print(" Sensores MQTT desconectados")
        
        # Desconectar Meshtastic
        if self.comunicador.client.is_connected():
            self.comunicador.disconnect_mqtt()
            print(" Meshtastic desconectado")
        
        # Mostrar estadísticas finales
        if self.almacenamiento:
            stats = self.almacenamiento.obtener_estadisticas()
            print(f"\nResumen de datos guardados:")
            print(f"   Mensajes: {stats.get('total_mensajes', 0)}")
            print(f"   Posiciones: {stats.get('total_posiciones', 0)}")
            print(f"   Sensores: {stats.get('total_sensores', 0)}")
        
        print(" Saliendo...")