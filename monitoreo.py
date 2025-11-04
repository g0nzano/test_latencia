import mysql.connector
import datetime
import subprocess
import platform
import re
import time
import sys

# --- 1. CONFIGURACIÓN DEL HOST Y DB ---
TARGET_HOST = "sitio o ip " 
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "monitoreo_red" 
TABLE_NAME = "latencia_registros" 

def obtener_latencia(host):
    """
    Ejecuta un comando ping, maneja la salida en español de Windows
    y extrae la latencia promedio.
    """
    # Define el comando ping: -n 1 para Windows, -c 1 para Linux/macOS
    parametro_ping = '-n' if platform.system().lower() == 'windows' else '-c'
    comando = ['ping', parametro_ping, '1', host]
    
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=5, 
            check=False # No lanzar error por fallo de ping, lo manejamos con el resultado
        )
        
        # Si el ping falla (timeout o host no encontrado)
        if resultado.returncode != 0:
            print(f"❌ Fallo al hacer ping a {host}. Código de error: {resultado.returncode}")
            return None
        
        # --- Extracción de la Latencia (CORREGIDA) ---
        if platform.system().lower() == 'windows':
            
            # 1. Intenta buscar el valor de la Media (más fiable)
            # Busca 'Media = 30ms' (o 'Media = 30 ms', ignorando espacios y caracteres especiales)
            # La regex busca la palabra 'Media' seguida de cero o más caracteres, hasta el número.
            # Usamos `.*?` para una búsqueda no codiciosa.
            match = re.search(r'Media\s*[=|\s][\s]*(\d+)ms', resultado.stdout, re.IGNORECASE)
            
            if match:
                print(f"DEBUG: Latencia extraída con regex (Media): {match.group(1)}ms")
                return float(match.group(1))

            # 2. Intenta buscar el tiempo individual de la primera respuesta (como respaldo)
            match_individual = re.search(r'tiempo=(\d+)ms', resultado.stdout, re.IGNORECASE)
            if match_individual:
                 print(f"DEBUG: Latencia extraída con regex (Individual): {match_individual.group(1)}ms")
                 return float(match_individual.group(1))

        else: # Linux/macOS (Se deja la regex original, que funciona mejor en ASCII)
            match = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', resultado.stdout)
            if match:
                return float(match.group(1))

        print(f"⚠️ No se pudo extraer la latencia del host {host}. Verifique el formato de salida del ping.")
        return None
    
    except subprocess.TimeoutExpired:
        print(f"❌ Tiempo de espera agotado al hacer ping a: {host}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al hacer ping: {e}")
        return None

def ejecutar_monitoreo_y_guardar():
    """Ejecuta el ping y guarda el resultado en la BD."""
    
    print(f"\n[INICIO] Ejecutando prueba a {TARGET_HOST}...")
    latencia_ms = obtener_latencia(TARGET_HOST)
    
    if latencia_ms is None:
        print("⛔ No se pudo obtener la latencia. No se guardará el registro.")
        return

    fecha_registro = datetime.datetime.now()
    print(f"✅ Latencia obtenida: {latencia_ms:.2f} ms")
    
    # --- 2. CONEXIÓN Y GUARDADO ---
    
    try:
        print(f"DEBUG: Intentando conectar a la BD '{DB_NAME}'...")
        mydb = mysql.connector.connect(
          host=DB_HOST,
          user=DB_USER,
          password=DB_PASSWORD,
          database=DB_NAME
        )
        print("DEBUG: Conexión exitosa. Preparando inserción...")
        
        cursor = mydb.cursor()
        
        # Usamos los nombres de columna correctos: timestamp y latencia_ms
        sql = f"INSERT INTO {TABLE_NAME} (timestamp, latencia_ms) VALUES (%s, %s)"
        val = (fecha_registro, latencia_ms)
        
        cursor.execute(sql, val)
        mydb.commit() # Confirma la inserción
        
        print(f"💾 {cursor.rowcount} registro INSERTADO. ¡ÉXITO!")
        
    except mysql.connector.Error as err:
        print(f"❌ Error de MySQL al conectar o insertar:")
        # Imprime el código de error para un diagnóstico preciso
        print(f"   Código de Error: {err.errno}")
        print(f"   Mensaje: {err.msg}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al guardar: {e}")
    finally:
        if 'mydb' in locals() and mydb.is_connected():
            cursor.close()
            mydb.close()
            print("DEBUG: Conexión a la BD cerrada.")

if __name__ == "__main__":
    intervalo_segundos = 300 # 5 minutos
    print(f"Monitoreo de {TARGET_HOST} iniciado. Ejecutando cada {intervalo_segundos/60:.0f} minutos.")
    try:
        while True:
            ejecutar_monitoreo_y_guardar()
            print(f"Esperando {intervalo_segundos} segundos antes del siguiente ping...")
            time.sleep(intervalo_segundos)
    except KeyboardInterrupt:
        print("\nMonitoreo detenido por el usuario.")
        sys.exit(0)