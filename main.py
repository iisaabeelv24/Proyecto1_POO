import time
from dispositivo import Dispositivo
from comunicador import Comunicador
from recibir_mensaje import RecibirMensaje
from mqtt_sensores import MQTTsensores
from almacenamiento import Almacenamiento
from menu import InterfazTerminal
from meshtastic import BROADCAST_NUM

def main():
    # Crear instancias
    dispositivo = Dispositivo()
    comunicador = Comunicador(dispositivo)
    #Crear almacenamiento y receptor y sensores con almacenamiento
    almacenamiento = Almacenamiento()
    receptor = RecibirMensaje(comunicador, dispositivo,almacenamiento)
    mqtt_sensores = MQTTsensores(comunicador,almacenamiento)


    #Conectar receptor a comunicador
    comunicador.set_receptor(receptor)
    
    # Configurar topic
    comunicador.set_topic()
    
    # Conectar al broker MQTT
    comunicador.connect_mqtt()
    time.sleep(2)  # Esperar más tiempo para la conexión
    
    # Verificar si está conectado antes de enviar mensajes
    if comunicador.client.is_connected():
        print(" Conectado al broker MQTT")
        
        # Enviar información inicial
        comunicador.send_node_info(BROADCAST_NUM, want_response=False)
        time.sleep(2)
        
        comunicador.send_position(BROADCAST_NUM)
        time.sleep(2)
        
        comunicador.send_message(BROADCAST_NUM, 'Hola soy Isabel')
        time.sleep(2)
        
        print("Mensajes iniciales enviados. Iniciando interfaz...")
        
        # Iniciar la interfaz de usuario
        interfaz = InterfazTerminal(comunicador,receptor,mqtt_sensores,almacenamiento)
        interfaz.ejecutar_menu()
        
    else:
        print("No se pudo conectar al broker MQTT")
        # Iniciar interfaz aunque no haya conexión
        interfaz = InterfazTerminal(comunicador,receptor,mqtt_sensores,almacenamiento)
        interfaz.ejecutar_menu()

if __name__ == "__main__":
    main()