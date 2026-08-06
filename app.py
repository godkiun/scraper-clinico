"""
app.py
======
Interfaz gráfica de la Web App de Scraping de Literatura Clínica.
Permite realizar búsquedas en español, traducirlas al inglés para optimizar consultas en APIs médicas,
descargar los PDFs y archivos suplementarios de Zenodo/PubMed Central en un entorno temporal,
y empaquetarlos en un archivo .ZIP comprimido para su descarga.
"""

import tempfile
import zipfile
from pathlib import Path
import streamlit as st
import requests

# Configurar layout de la página
st.set_page_config(
    page_title="Medical Scraper MVP",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar motor de descarga local
from scraper import ejecutar_scraper


def traducir_consulta_es_en(texto_consulta: str) -> str:
    """
    Traduce texto de español a inglés usando un endpoint HTTP público.
    Si la traducción falla, se debe manejar la excepción en el flujo principal.
    """
    url_traduccion = "https://api.mymemory.translated.net/get"
    parametros = {"q": texto_consulta, "langpair": "es|en"}
    respuesta = requests.get(url_traduccion, params=parametros, timeout=20)
    respuesta.raise_for_status()
    datos_respuesta = respuesta.json()
    texto_traducido = (
        datos_respuesta.get("responseData", {}).get("translatedText", "").strip()
    )
    if not texto_traducido:
        raise ValueError("La API de traducción respondió sin texto traducido.")
    return texto_traducido


# =============================================================================
# INYECCIÓN DE ESTILOS CSS PERSONALIZADOS (Aesthetics & Design)
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* Aplicar tipografía general */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
}

/* Header Premium */
.header-container {
    background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
    padding: 2.5rem;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    margin-bottom: 2.5rem;
    text-align: center;
}

.header-title {
    background: linear-gradient(90deg, #38bdf8, #818cf8, #fb7185);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 3rem;
    margin: 0;
}

.header-subtitle {
    color: #94a3b8;
    font-size: 1.25rem;
    margin-top: 0.6rem;
    font-weight: 300;
}

/* Botón principal */
.stButton>button {
    background: linear-gradient(90deg, #fb7185, #818cf8);
    color: white !important;
    border: none !important;
    padding: 0.8rem 2.5rem !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(251, 113, 133, 0.3) !important;
    width: 100%;
}

.stButton>button:hover {
    background: linear-gradient(90deg, #f43f5e, #6366f1) !important;
    transform: scale(1.02) !important;
    box-shadow: 0 6px 20px rgba(251, 113, 133, 0.5) !important;
}

/* Info Box / Success Box */
.info-gradient-box {
    background: linear-gradient(135deg, rgba(251, 113, 133, 0.1) 0%, rgba(129, 140, 248, 0.1) 100%);
    border-left: 4px solid #fb7185;
    padding: 1.2rem;
    border-radius: 8px;
    color: #e2e8f0;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER DE LA APLICACIÓN
# =============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-title">📚 Clinical Literature & Supplementary Scraper</div>
    <div class="header-subtitle">Autotraducción inteligente, extracción multiorigen y empaquetado directo de documentos científicos</div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# PANEL DE CONFIGURACIÓN (Sidebar)
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuración de Descargas")
    max_descargas = st.slider(
        "Resultados máximos por API", 
        min_value=1, 
        max_value=30, 
        value=5, 
        help="Límite máximo de artículos y suplementos a descargar de Zenodo y PubMed Central respectivamente."
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Acerca del MVP")
    st.markdown("""
    Esta herramienta simplificada está diseñada para agilizar la obtención de literatura médica.
    
    * **Búsqueda en Español:** Escribe tu consulta en tu idioma nativo y el sistema la traducirá al inglés.
    * **PubMed Central & Zenodo:** Acceso en tiempo real a papers Open-Access y bases de datos suplementarias.
    * **Limpieza de Servidor:** Los archivos temporales se borran automáticamente tras generar tu descarga.
    """)

# =============================================================================
# PANEL CENTRAL DE BÚSQUEDA
# =============================================================================
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### 🔍 Consulta de Búsqueda")
    query = st.text_input(
        "Ingresa el tema o término de investigación médica (en Español o Inglés)", 
        value="prueba de aliento SIBO", 
        placeholder="Ej. 'cáncer de colon microbiota', 'diabetes tipo 2 suplementos', 'SIBO breath test'",
        help="La consulta se traducirá automáticamente al inglés para maximizar los resultados en las bases de datos internacionales."
    )

with col_right:
    st.markdown("""
    <div class="info-gradient-box">
        <h4>💡 Flujo del MVP</h4>
        <ol>
            <li>Ingresa tu búsqueda y define la cantidad de artículos a procesar en la barra lateral.</li>
            <li>Haz clic en <b>Iniciar Búsqueda y Descarga</b>.</li>
            <li>El sistema traducirá la consulta, rastreará las APIs y descargará los archivos.</li>
            <li>Descarga el paquete <b>.ZIP</b> final y el servidor eliminará los temporales automáticamente.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# EJECUCIÓN DEL SCRAPER Y COMPRESIÓN
# =============================================================================
st.markdown("---")
if st.button("🚀 Iniciar Búsqueda y Descarga"):
    if not query.strip():
        st.error("Por favor, ingresa un término de búsqueda válido.")
    else:
        # 1. TRADUCCIÓN AUTOMÁTICA
        with st.spinner("Traduciendo búsqueda al inglés..."):
            try:
                translated_query = traducir_consulta_es_en(query)
                st.info(f"✨ **Traducción optimizada para base de datos:** '{translated_query}'")
            except (requests.RequestException, ValueError, TypeError) as error_traduccion:
                st.warning(
                    f"No se pudo conectar al traductor ({error_traduccion}). "
                    f"Se utilizará la consulta original: '{query}'"
                )
                translated_query = query
        
        # 2. PROCESO DE DESCARGA
        output_folder = Path("output")
        output_folder.mkdir(exist_ok=True)
        
        safe_query = "".join(c if c.isalnum() else "_" for c in translated_query)
        zip_filename = f"literatura_{safe_query}.zip"
        zip_filepath = output_folder / zip_filename
        
        # Usar tempfile para el almacenamiento de archivos descargados temporalmente
        with tempfile.TemporaryDirectory() as raw_temp_dir:
            temp_dir = Path(raw_temp_dir)
            
            with st.status("Ejecutando motores de búsqueda...", expanded=True) as status_box:
                st.write("🔍 Conectando con Zenodo y PubMed Central...")
                archivos_descargados = ejecutar_scraper(translated_query, temp_dir, max_results=max_descargas)
                
                if not archivos_descargados:
                    st.warning("⚠️ No se encontraron documentos para descargar con los criterios de búsqueda.")
                else:
                    st.success(f"📥 Descargados {len(archivos_descargados)} archivos exitosamente.")
                    
                    # 3. EMPAQUETAR EN ZIP
                    st.write("📦 Comprimiendo archivos en formato .ZIP...")
                    try:
                        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file_in_temp in temp_dir.rglob("*"):
                                if file_in_temp.is_file():
                                    zipf.write(file_in_temp, arcname=file_in_temp.name)
                        st.success("✅ Compresión finalizada con éxito.")
                    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error_compresion:
                        st.error(f"Error comprimiendo archivos: {error_compresion}")
                        zip_filepath = None
                
                status_box.update(label="¡Búsqueda y Descarga Completadas!", state="complete", expanded=False)

        # La carpeta temporal temp_dir se elimina automáticamente al salir del bloque "with tempfile.TemporaryDirectory()"
        
        # 4. RENDERIZAR RESULTADO Y BOTÓN DE DESCARGA
        if zip_filepath and zip_filepath.exists():
            st.markdown("### 🎉 ¡Resultados Listos!")
            st.success("Los archivos se han guardado en el servidor y la carpeta temporal se ha limpiado de forma segura.")
            
            # Leer bytes del ZIP para el download_button
            with open(zip_filepath, "rb") as fz:
                zip_bytes = fz.read()
            
            st.download_button(
                label="📥 Descargar literatura y archivos suplementarios (.ZIP)",
                data=zip_bytes,
                file_name=zip_filename,
                mime="application/zip",
                help="Haz clic para descargar el paquete de documentos en tu dispositivo local.",
                width='stretch'  # Adaptado al Streamlit de 2026
            )
