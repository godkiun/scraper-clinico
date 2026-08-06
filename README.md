# Scraper Clínico - Extracción y Procesamiento de Datos Médicos 🩺📊

Herramienta automatizada en Python/Streamlit para la extracción, estructuración y análisis de datos clínicos y literatura médica.

## 🚀 Características principales
- **Búsqueda multilingüe:** permite consultas en español y las traduce al inglés para optimizar resultados.
- **Rastreador de PubMed Central (PMC):** descarga PDF principal y archivos suplementarios (`.csv`, `.xlsx`, `.xls`, `.docx`).
- **Rastreador de Zenodo:** descarga datasets biomédicos y reportes complementarios.
- **Empaquetado final en ZIP:** genera un archivo listo para descarga.

---

## 🛠️ Instalación

1. Clonar o descargar el repositorio.
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. (Opcional recomendado) Instalar utilidades de seguridad:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Definir variables de entorno para NCBI:
   ```bash
   set NCBI_EMAIL=tu_correo@dominio.com
   set NCBI_API_KEY=tu_api_key_opcional
   ```

---

## 💻 Uso

```bash
streamlit run app.py
```

Luego abre `http://localhost:8501`, ingresa tu consulta y descarga el ZIP generado.

---

## 🔐 Seguridad y validación

- Pruebas unitarias:
  ```bash
  python -m unittest -v
  ```
- Auditoría de dependencias:
  ```bash
  pip-audit -r requirements.txt
  ```
