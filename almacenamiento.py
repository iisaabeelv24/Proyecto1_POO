import json
import os
from datetime import datetime
import threading

class Almacenamiento:
    def __init__(self, directorio="datos"):
        self.directorio = directorio
        self.archivo_mensajes = os.path.join(directorio, "mensajes.json")
        self.archivo_posiciones = os.path.join(directorio, "posiciones.json")
        self.archivo_sensores = os.path.join(directorio, "sensores.json")
        
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
    
    def guardar_mensaje(self, mensaje_texto, remitente, tipo="texto"):
        """Guarda un mensaje de texto en el archivo JSON"""
        with self.lock:
            try:
                # Leer mensajes existentes
                with open(self.archivo_mensajes, 'r', encoding='utf-8') as f:
                    mensajes = json.load(f)# lee todos los mensajes
                
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
                
                print(f" Mensaje guardado: {mensaje_texto[:50]}...")
                return True
                
            except Exception as e:
                print(f"Error guardando mensaje: {e}")
                return False
    
    def guardar_posicion(self, latitud, longitud, altitud, remitente, precision=None):
        """Guarda una posición GPS en el archivo JSON"""
        with self.lock:
            try:
                # Leer posiciones existentes
                with open(self.archivo_posiciones, 'r', encoding='utf-8') as f:
                    posiciones = json.load(f)
                
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
                
                print(f" Posición guardada: {latitud}, {longitud}")
                return True
                
            except Exception as e:
                print(f" Error guardando posición: {e}")
                return False
    
    def guardar_dato_sensor(self, topic, datos, remitente=None):
        """Guarda datos de sensores en el archivo JSON"""
        with self.lock:
            try:
                # Leer datos existentes
                with open(self.archivo_sensores, 'r', encoding='utf-8') as f:
                    sensores = json.load(f)
                
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
                
                print(f"Dato de sensor guardado: {topic}")
                return True
                
            except Exception as e:
                print(f"Error guardando dato de sensor: {e}")
                return False
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas de los datos almacenados"""
        try:
            with open(self.archivo_mensajes, 'r', encoding='utf-8') as f:
                mensajes = json.load(f)
            
            with open(self.archivo_posiciones, 'r', encoding='utf-8') as f:
                posiciones = json.load(f)
            
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
            print(f"Error obteniendo estadísticas: {e}")
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
                
            print(f"Datos exportados a: {archivo_salida}")
            return True
            
        except Exception as e:
            print(f" Error exportando datos: {e}")
            return False