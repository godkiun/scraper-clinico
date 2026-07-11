# Buscador de Literatura Clínica y Archivos Suplementarios MVP

Este proyecto es una herramienta local interactiva basada en **Streamlit** diseñada para automatizar la recopilación, traducción y descarga de literatura científica médica y sus correspondientes archivos de datos suplementarios desde repositorios públicos abiertos.

## 🚀 Características principales
- **Búsqueda Inteligente Multilingüe:** Permite ingresar consultas de búsqueda en español. El sistema utiliza la librería `deep-translator` para traducir automáticamente la query al inglés antes de realizar la consulta en los servidores médicos, optimizando la precisión de la búsqueda.
- **Rastreador de PubMed Central (PMC):** Conecta con el sistema de base de datos de PubMed para encontrar papers y extraer de manera automatizada tanto el documento principal (PDF) como todas sus tablas suplementarias asociadas (en formatos `.csv`, `.xlsx`, `.xls`, `.docx`).
- **Rastreador de Zenodo:** Consulta el repositorio multidisciplinar Zenodo para descargar bases de datos biomédicas en bruto y reportes complementarios correspondientes a la consulta.
- **Empaquetado y Limpieza de Servidor:** Agrupa todos los documentos obtenidos en un archivo comprimido `.zip` listo para descargar. Todos los datos temporales del proceso se eliminan automáticamente del servidor local al finalizar, evitando el consumo innecesario de almacenamiento.

---

## 📁 Estructura del Repositorio
El repositorio cuenta con la siguiente estructura base de producción limpia:
```
MODELO SIBO E IMO/
├── app.py              # Interfaz gráfica Streamlit y orquestación UI
├── scraper.py          # Lógica de búsqueda y descarga desde APIs científicas
├── requirements.txt    # Dependencias mínimas del entorno
├── README.md           # Documentación del proyecto (este archivo)
└── output/             # Carpeta de destino local para los archivos comprimidos (.ZIP)
```

---

## 🛠️ Requisitos e Instalación

1. **Clonar o descargar** este repositorio en tu máquina local.
2. Asegurarte de tener instalado **Python 3.8+**.
3. Instalar las dependencias necesarias ejecutando el siguiente comando en tu terminal:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Instrucciones de Uso

Para lanzar la interfaz local de la aplicación, ejecuta en tu terminal:
```bash
streamlit run app.py
   ```

Una vez que se inicie el servidor de Streamlit:
1. Abre tu navegador en la dirección provista (usualmente `http://localhost:8501`).
2. Ingresa un tema médico o clínico de tu interés en español (ej. *'sobrecrecimiento bacteriano SIBO'*, *'microbiota diabetes'*).
3. Configura el número máximo de resultados a descargar en la barra lateral.
4. Presiona el botón **Iniciar Búsqueda y Descarga**.
5. Tras completarse el flujo, haz clic en **Descargar literatura y archivos suplementarios (.ZIP)** para guardar los archivos consolidados en tu equipo local.
