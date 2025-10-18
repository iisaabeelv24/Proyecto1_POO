####Para activar el entorno se necesitan estos comandos:
#Get-ExecutionPolicy
#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#pip install paho-mqtt
#Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#-----------------------------------------
#python -m venv venv  -creas entorno virtual

LIBRERIAS A INSTALAR
#pip install paho-mqtt  -instalas módulos
#pip install meshtastic
#pip install cryptography

#.\venv\Scripts\Activate.ps1  -activa el entorno powershell
#Activate.ps1 esta incluido en el .venv y activa los entornos.

-------------------------------

REQUIREMENTS
LAs librerias usadas son:
meshtastic y meshtastic.protobuf (envio de mensajes a nodos)
paho.mqtt.client  (cliente de mqtt)
cryptography (cifra y descifra mensajes)
base64 y hashlib (seguridad y funciones para archivos)
json,datetime y os (almacenan datos,tiempos y archivos)
ssl (para la seguridad de la comunicación mqtt)

MÓDULOS
-Dispositivo: almacena la información del nodo
-Comunicador:conecta mqtt con meshtastic y realiza el envío
            de mensajes, posiciones y la info.de sensores
-recibir_mensaje: procesa y descifra los mensajes
-mqtt_sensores: se conecta a MQTT y recibe los datos de sensores
-almacenamiento:guarda los mensajes posiciones y datos de sensores en
            un archivo JSON con historial
-menu=InterfazTerminal: proporciona el menu al usuario