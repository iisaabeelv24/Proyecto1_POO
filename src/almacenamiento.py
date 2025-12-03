import json
import os
from datetime import datetime
import threading
from pathlib import Path 
from abc import ABC, abstractmethod # define interfaces

#from recibir_mensaje import RecibirMensaje
#rutas de archivos y directorios multiplataforma

#Clase con herencia multiple
class Logger:
    def log_info(self, mensaje):
        print(f" {mensaje}")
    def log_error(self, mensaje):
        print(f" ERROR: {mensaje}")
    def log(self, mensaje):
        print(f" {mensaje}")

#Clase abstracta con herencia multiple
class Almacenamiento(ABC, Logger):
    def __init__(self, directorio="logs"):
        #inicia logger
        super().__init__() if hasattr(super(), '__init__') else None
        self.directorio = Path(directorio)
        self.archivo_mensajes = self.directorio / "mensajes.json"
        self.archivo_posiciones = self.directorio / "posiciones.json"
        self.archivo_sensores = self.directorio / "sensores.json"

        # Crear directorio si no existe
        os.makedirs(directorio, exist_ok=True)
        
        # Inicializar archivos si no existen
        self._inicializar_archivos()
        
        # Lock para acceso thread-safe
        self.lock = threading.Lock()
    
    def _inicializar_archivos(self):
        """Inicializa los archivos JSON si no existen"""
        archivos = {
            self.archivo_mensajes: [],
            self.archivo_posiciones: [],
            self.archivo_sensores: []
        }
        
        for archivo, contenido_inicial in archivos.items():
            if not os.path.exists(archivo):
                with open(archivo, 'w', encoding='utf-8') as f:
                    json.dump(contenido_inicial, f, indent=2, ensure_ascii=False)
    
    def _obtener_timestamp(self):
        """Obtiene el timestamp actual formateado"""
        return datetime.now().isoformat()

#Metodos abstractos    
    @abstractmethod
    def guardar_mensaje(self, mensaje_texto, remitente, tipo="texto"):
        pass
    
    @abstractmethod
    def guardar_posicion(self, latitud, longitud, altitud, remitente, precision=None):
        pass
    
    @abstractmethod
    def guardar_dato_sensor(self, topic, datos, remitente=None):
        pass

class AlmacenamientoJSON(Almacenamiento):
    def __init__(self, directorio="logs"):
        super().__init__(directorio)

    
    def guardar_mensaje(self, mensaje_texto, remitente, tipo="texto"):
        """Guarda un mensaje de texto en el archivo JSON"""
        with self.lock:
            try:
                # Lee mensajes existentes
                if self.archivo_mensajes.exists():
                    with open(self.archivo_mensajes, 'r', encoding='utf-8') as f:
                        mensajes = json.load(f)
                else:
                    mensajes = []
                
                # Agregar nuevo mensaje
                nuevo_mensaje = {
                    "timestamp": self._obtener_timestamp(),
                    "tipo": tipo,
                    "remitente": remitente,
                    "mensaje": mensaje_texto
                }
                
                mensajes.append(nuevo_mensaje)#añade mensajes nuevos
                
                # Guardar de vuelta
                with open(self.archivo_mensajes, 'w', encoding='utf-8') as f:
                    json.dump(mensajes, f, indent=2, ensure_ascii=False, default=str)
                
                self.log(f" Mensaje guardado: {mensaje_texto[:50]}...")

                return True
                
            except Exception as e:
                self.log(f"Error guardando mensaje: {e}")
                return False
    
    
    def guardar_posicion(self, latitud, longitud, altitud, remitente, precision=None):
        """Guarda una posición GPS en el archivo JSON"""
        with self.lock:
            try:
                # Leer posiciones existentes
                if self.archivo_posiciones.exists():
                    with open(self.archivo_posiciones, 'r', encoding='utf-8') as f:
                        posiciones = json.load(f)
                else:
                    posiciones = []

                # Agregar nueva posición
                nueva_posicion = {
                    "timestamp": self._obtener_timestamp(),
                    "remitente": remitente,
                    "coordenadas": {
                        "latitud": latitud,
                        "longitud": longitud,
                        "altitud": altitud
                    },
                    "precision": precision
                }
                
                posiciones.append(nueva_posicion)
                
                # Guardar de vuelta
                with open(self.archivo_posiciones, 'w', encoding='utf-8') as f:
                    json.dump(posiciones, f, indent=2, ensure_ascii=False, default=str)
                
                self.log(f" Posición guardada: {latitud}, {longitud}")
                return True
                
            except Exception as e:
                self.log(f" Error guardando posición: {e}")
                return False
    
    
    def guardar_dato_sensor(self, topic, datos, remitente=None):
        """Guarda datos de sensores en el archivo JSON"""
        with self.lock:
            try:
                # Leer datos existentes
                if self.archivo_sensores.exists():
                    with open(self.archivo_sensores, 'r', encoding='utf-8') as f:
                        sensores = json.load(f)
                else:
                    sensores = []

                # Agregar nuevo dato
                nuevo_dato = {
                    "timestamp": self._obtener_timestamp(),
                    "topic": topic,
                    "remitente": remitente or "sensor",
                    "datos": datos
                }
                
                sensores.append(nuevo_dato)
                
                # Guardar de vuelta
                with open(self.archivo_sensores, 'w', encoding='utf-8') as f:
                    json.dump(sensores, f, indent=2, ensure_ascii=False, default=str)
                
                self.log(f"Dato de sensor guardado: {topic}")
                return True
                
            except Exception as e:
                self.log(f"Error guardando dato de sensor: {e}")
                return False
    
   
    def obtener_estadisticas(self):
        """Obtiene estadísticas de los datos almacenados"""
        try:
            mensajes=[]
            if self.archivo_mensajes.exists():
                with open(self.archivo_mensajes, 'r', encoding='utf-8') as f:
                    mensajes = json.load(f)
            posiciones = []
            if self.archivo_posiciones.exists():
                with open(self.archivo_posiciones, 'r', encoding='utf-8') as f:
                    posiciones = json.load(f)

            sensores = []
            if self.archivo_sensores.exists():
                with open(self.archivo_sensores, 'r', encoding='utf-8') as f:
                    sensores = json.load(f)
            
            return {
                "total_mensajes": len(mensajes),
                "total_posiciones": len(posiciones),
                "total_sensores": len(sensores),
                "ultimo_mensaje": mensajes[-1] if mensajes else None,
                "ultima_posicion": posiciones[-1] if posiciones else None
            }
            
        except Exception as e:
            self.log(f"Error obteniendo estadísticas: {e}")
            return {}
    
    
    def exportar_txt(self, archivo_salida="datos_exportados.txt"):
        """Exporta todos los datos a un archivo de texto legible"""
        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                f.write("="*50 + "\n")
                f.write("       DATOS MESHTASTIC EXPORTADOS\n")
                f.write("="*50 + "\n\n")
                
                # Estadísticas
                stats = self.obtener_estadisticas()
                f.write(f"ESTADÍSTICAS:\n")
                f.write(f"- Total mensajes: {stats.get('total_mensajes', 0)}\n")
                f.write(f"- Total posiciones: {stats.get('total_posiciones', 0)}\n")
                f.write(f"- Total datos sensores: {stats.get('total_sensores', 0)}\n\n")
                
                # Mensajes
                with open(self.archivo_mensajes, 'r', encoding='utf-8') as mf:
                    mensajes = json.load(mf)
                    f.write("MENSAJES:\n")
                    f.write("-" * 30 + "\n")
                    for msg in mensajes[-20:]:  # Últimos 20 mensajes
                        f.write(f"[{msg.get('timestamp', '')}] {msg.get('remitente', '')}: {msg.get('mensaje', '')}\n")
                    f.write("\n")
                
                # Posiciones
                with open(self.archivo_posiciones, 'r', encoding='utf-8') as pf:
                    posiciones = json.load(pf)
                    f.write("POSICIONES GPS:\n")
                    f.write("-" * 30 + "\n")
                    for pos in posiciones[-10:]:  # Últimas 10 posiciones
                        coords = pos.get('coordenadas', {})
                        f.write(f"[{pos.get('timestamp', '')}] {pos.get('remitente', '')}: ")
                        f.write(f"Lat={coords.get('latitud', 'N/A')}, Lon={coords.get('longitud', 'N/A')}, Alt={coords.get('altitud', 'N/A')}\n")
                
            self.log(f"Datos exportados a: {archivo_salida}")
            return True
            
        except Exception as e:
            self.log(f" Error exportando datos: {e}")
            return False

#Generador       
    def generar_mensajes_recientes(self, limite=10):
    
            try:
                if not self.archivo_mensajes.exists():
                    self.log_info("No hay mensajes para generar")
                    return
                
                with open(self.archivo_mensajes, 'r', encoding='utf-8') as f:
                    mensajes = json.load(f)
                
                # Ordenar por timestamp (más recientes primero)
                mensajes_ordenados = sorted(mensajes, 
                                        key=lambda x: x.get('timestamp', ''), 
                                        reverse=True)
                
                for i, mensaje in enumerate(mensajes_ordenados):
                    if i >= limite:
                        break
                    yield mensaje  # ← GENERADOR con yield
                    
            except Exception as e:
                self.log_error(f"Generando mensajes: {e}")
                yield from []  # Generador vacío en caso de error