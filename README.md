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
MÓDULOS
-Dispositivo
-Comunicador
-recibir_mensaje
-mqtt_sensores
-almacenamiento
-menu=InterfazTerminal
#------------------------------------
MESHTASTIC COMUNICACIÓN
El sistema cliente para la red Meshtastic que permite la comunicación mesh, 
permitiendo el envío y recepción de mensajes, gestiona las posiciones GPS 
y aporta datos de sensores mediante MQTT.

Tiene una serie de caracteísticas, como:
-Comunicación de mensajes:envia y recibe mensajes en tiempo real,
cifra los mensajes y los almacena en un .JSON
-Gestiona posiciones: envia coordenadas GPS,
recibe posiciones de otros nodos
y almacena los datos en un .JSON
-Datos de sensores:se conectan a MQTT y se reciben datos de ellos.
-Almacenamiento: se crean 3 archivos .JSON para mensajes, posiciones y sensores.

