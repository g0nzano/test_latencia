import mysql.connector
import pandas as pd
import plotly.express as px
from plotly.offline import plot
import warnings
import sys

# Suprimir advertencias de Plotly (opcional, para una salida más limpia)
# La advertencia de Pandas sobre el conector directo es normal y se ignora aquí.
warnings.filterwarnings('ignore', category=UserWarning, module='plotly.express._core')

# --- CONFIGURACIÓN DE LA BASE DE DATOS DE XAMPP ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "monitoreo_red"
TARGET_HOST = "sistema.hostbrs.com.br" # Host para el título del gráfico
UMBRAL_ALERTA = 100 # Latencia en ms para el umbral visual de alerta

def crear_dashboard_latencia():
    """
    Se conecta a la BD, extrae los datos de latencia y genera un gráfico interactivo.
    """
    print("Iniciando generación de Dashboard...")
    
    try:
        # 1. Conexión a la base de datos MySQL/MariaDB (XAMPP)
        mydb = mysql.connector.connect(
          host=DB_HOST,
          user=DB_USER,
          password=DB_PASSWORD,
          database=DB_NAME
        )
        
        # Consulta SQL para obtener TODOS los registros ordenados por tiempo
        query = "SELECT timestamp, latencia_ms FROM latencia_registros ORDER BY timestamp ASC"
        
        # 2. Leer los datos directamente en un DataFrame de Pandas
        # pd.read_sql maneja la conexión y la consulta
        df = pd.read_sql(query, mydb)
        
        mydb.close()
        
        if df.empty:
            print("❌ No hay datos en la tabla 'latencia_registros'. Asegúrate de que 'monitoreo_host.py' se haya ejecutado con éxito.")
            return

        print(f"✅ Se cargaron {len(df)} registros para graficar.")
        
        # 3. Crear el Gráfico Interactivo con Plotly
        fig = px.line(
            df, 
            x='timestamp', 
            y='latencia_ms',
            title=f'📈 Latencia de Red (Ping) Histórica para {TARGET_HOST}',
            labels={
                'timestamp': 'Fecha y Hora del Registro',
                'latencia_ms': 'Latencia (ms)'
            }
        )
        
        # Añadir la línea de Umbral de Alerta
        fig.add_hline(y=UMBRAL_ALERTA, line_dash="dash", line_color="red", 
                      annotation_text=f"Umbral de Alerta ({UMBRAL_ALERTA}ms)",
                      annotation_position="top left")

        # Mejorar el diseño del gráfico
        fig.update_traces(mode='lines+markers', marker=dict(size=4))
        fig.update_layout(xaxis_title='Tiempo', yaxis_title='Latencia (ms)', hovermode="x unified")
        
        # 4. Mostrar el gráfico en el navegador
        # 'plot' guarda el gráfico como un archivo HTML temporal y lo abre automáticamente.
        plot(fig, auto_open=True)
        
        print("\n🎉 Dashboard generado y abierto en tu navegador.")
        
    except mysql.connector.Error as err:
        print(f"❌ Error de conexión a MySQL. Asegúrate de que XAMPP esté corriendo. Detalles:")
        print(f"   Código de Error: {err.errno}")
        print(f"   Mensaje: {err.msg}")
        sys.exit(1) # Salir con error
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al generar el gráfico: {e}")
        sys.exit(1) # Salir con error


if __name__ == "__main__":
    try:
        crear_dashboard_latencia()
    except Exception as e:
        print(f"❌ Error al iniciar el script: {e}")
        # Esto captura errores de importación (si falta una librería)
        print("Asegúrate de haber instalado todas las dependencias: pip install pandas plotly mysql-connector-python")