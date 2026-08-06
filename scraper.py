"""
scraper.py
==========
Motor de búsqueda y descarga agnóstico de literatura científica y archivos suplementarios.
Conecta con las APIs públicas de Zenodo y PubMed Central (PMC) para buscar y descargar 
documentos (PDFs y archivos de datos como .xlsx, .csv, .xls, .docx) en base a una consulta (query).
"""

import os
import time
import logging
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.error import HTTPError, URLError
import requests
from Bio import Entrez

# Configuración del Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

# Configurar el correo para Entrez (NCBI lo requiere).
# Se evita dejar datos personales hardcodeados en el código fuente.
correo_ncbi = os.environ.get("NCBI_EMAIL", "").strip()
if not correo_ncbi:
    correo_ncbi = "no-reply@example.com"
    logger.warning(
        "NCBI_EMAIL no está definido. Se usará un correo genérico; "
        "configura NCBI_EMAIL para producción."
    )
Entrez.email = correo_ncbi
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY

TARGET_EXTENSIONS = (".xlsx", ".xls", ".csv", ".docx", ".pdf")
# Aumentado el límite para respetar Rate Limiting de NCBI
SLEEP_INTERVAL = 1.0  

HTTP_HEADERS = {
    "User-Agent": (
        f"AgnosticScienceScraper/4.0 (mailto:{correo_ncbi}; "
        "Local Streamlit Research Pipeline)"
    )
}


def _normalizar_nombre_archivo(nombre_original: str) -> str:
    """Normaliza nombres para guardar archivos de forma segura y portable."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in nombre_original)


def _miembro_tar_es_seguro(directorio_base: Path, miembro: tarfile.TarInfo) -> bool:
    """
    Valida que cada miembro del .tar no salga del directorio base y que
    no use symlinks/hardlinks potencialmente peligrosos.
    """
    if miembro.issym() or miembro.islnk():
        return False

    ruta_base_resuelta = directorio_base.resolve()
    ruta_destino = (directorio_base / miembro.name).resolve()
    try:
        ruta_destino.relative_to(ruta_base_resuelta)
        return True
    except ValueError:
        return False


def _extraer_tar_seguro(archivo_tar: tarfile.TarFile, directorio_destino: Path) -> None:
    """Extrae solo miembros seguros para mitigar path traversal."""
    for miembro in archivo_tar.getmembers():
        if not _miembro_tar_es_seguro(directorio_destino, miembro):
            logger.warning(f"Miembro inseguro omitido del tar: {miembro.name}")
            continue
        archivo_tar.extract(miembro, path=directorio_destino)


def descargar_archivo(url: str, destino: Path) -> bool:
    """Descarga un archivo desde una URL de manera segura."""
    try:
        response = requests.get(url, headers=HTTP_HEADERS, timeout=60, stream=True)
        if response.status_code == 200:
            with open(destino, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            logger.error(f"Error {response.status_code} al descargar de {url}")
            return False
    except (requests.RequestException, OSError) as e:
        logger.error(f"Excepción al descargar de {url}: {e}")
        return False


def buscar_y_descargar_zenodo(query: str, temp_dir: Path, max_results: int = 5) -> List[Path]:
    """
    Busca en la API de Zenodo y descarga archivos que coincidan con las extensiones de interés.
    """
    logger.info(f"Iniciando búsqueda en Zenodo para: '{query}'")
    descargados = []
    base_url = "https://zenodo.org/api/records"
    params = {"q": query, "size": max_results}
    
    try:
        response = requests.get(base_url, params=params, headers=HTTP_HEADERS, timeout=30)
        time.sleep(SLEEP_INTERVAL)
        if response.status_code != 200:
            logger.error(f"[Zenodo] Error {response.status_code}: {response.text[:200]}")
            return descargados
            
        hits = response.json().get("hits", {}).get("hits", [])
        logger.info(f"[Zenodo] Se encontraron {len(hits)} registros de interés.")
        
        for record in hits:
            record_id = record.get("id")
            title = record.get("metadata", {}).get("title", "Sin Título")
            files = record.get("files", [])
            
            # Filtrar archivos con extensiones válidas
            candidatos = [f for f in files if f.get("key", "").lower().endswith(TARGET_EXTENSIONS)]
            if not candidatos:
                continue
                
            logger.info(f"[Zenodo] Procesando registro útil: '{title}' (ID: {record_id})")
            for f in candidatos:
                name = f.get("key", "")
                url = f.get("links", {}).get("self") or f.get("links", {}).get("download")
                if not url:
                    continue
                
                # Nombre limpio para evitar colisiones
                nombre_seguro = _normalizar_nombre_archivo(name)
                filename = f"zenodo_{record_id}_{nombre_seguro}"
                target_path = temp_dir / filename
                
                logger.info(f"[Zenodo] Descargando '{name}'...")
                if descargar_archivo(url, target_path):
                    descargados.append(target_path)
                    logger.info(f"[Zenodo] Archivo descargado con éxito: {filename}")
                    time.sleep(SLEEP_INTERVAL)
                    
    except (requests.RequestException, ValueError) as e:
        logger.error(f"[Zenodo] Error general en búsqueda/descarga: {e}")
        
    return descargados


def obtener_detalles_pmc(pmcid: str) -> Tuple[str, List[str]]:
    """
    Obtiene el título del artículo de PMC y una lista de nombres de archivos suplementarios
    referenciados en el XML del artículo.
    """
    titulo = "Título Desconocido"
    archivos_suplementarios = []
    pmcid_num = pmcid.replace("PMC", "")
    try:
        handle = Entrez.efetch(db="pmc", id=pmcid_num, rettype="xml")
        xml_data = handle.read()
        handle.close()
        time.sleep(SLEEP_INTERVAL)
        
        root = ET.fromstring(xml_data)
        title_el = root.find(".//article-title")
        if title_el is not None:
            titulo = "".join(title_el.itertext()).strip()
            
        # Buscar suplementarios referenciados
        for supp in root.findall(".//supplementary-material"):
            href = supp.get("{http://www.w3.org/1999/xlink}href")
            if not href:
                for child in supp.iter():
                    href = child.get("{http://www.w3.org/1999/xlink}href")
                    if href:
                        break
            if href and href.strip().lower().endswith(TARGET_EXTENSIONS):
                archivos_suplementarios.append(href.strip())
    except (RuntimeError, ET.ParseError, ValueError, OSError, HTTPError, URLError) as e:
        logger.error(f"[{pmcid}] Error leyendo XML de efetch: {e}")
    return titulo, archivos_suplementarios


def consultar_pmc_oa_tgz_url(pmcid: str) -> Optional[str]:
    """
    Usa el servicio PMC Open Access Web Service para obtener la URL del paquete tgz.
    """
    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
    try:
        response = requests.get(url, params={"id": pmcid}, headers=HTTP_HEADERS, timeout=30)
        time.sleep(SLEEP_INTERVAL)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            if root.find("error") is not None:
                logger.warning(f"[{pmcid}] No disponible en el servicio de Open Access de PMC")
                return None
            link_el = root.find(".//record/link[@format='tgz']")
            if link_el is not None:
                href = link_el.get("href", "")
                if href.startswith("ftp://"):
                    href = "https://" + href[len("ftp://"):]
                return href
    except (requests.RequestException, ET.ParseError, ValueError) as e:
        logger.error(f"[{pmcid}] Error en PMC OA Web Service: {e}")
    return None


def descargar_y_extraer_pmc(pmcid: str, url_tgz: str, target_dir: Path, target_names: List[str], title: str) -> List[Path]:
    """
    Descarga el archivo .tar.gz de PMC OA, extrae el PDF principal y los archivos suplementarios,
    y los guarda en target_dir.
    """
    descargados = []
    try:
        logger.info(f"[{pmcid}] Descargando paquete Open Access desde {url_tgz}...")
        response = requests.get(url_tgz, headers=HTTP_HEADERS, timeout=120)
        time.sleep(SLEEP_INTERVAL)
        
        # Manejo de ruta obsoleta/deprecada en el FTP de PMC
        if response.status_code == 404 and "pub/pmc/" in url_tgz and "deprecated/" not in url_tgz:
            url_dep = url_tgz.replace("pub/pmc/", "pub/pmc/deprecated/")
            logger.info(f"[{pmcid}] Reintentando con URL deprecada: {url_dep}")
            response = requests.get(url_dep, headers=HTTP_HEADERS, timeout=120)
            time.sleep(SLEEP_INTERVAL)
            
        if response.status_code != 200:
            logger.error(f"[{pmcid}] Error {response.status_code} al descargar tgz")
            return descargados
            
        with tempfile.TemporaryDirectory() as tmp_dir:
            tgz_path = Path(tmp_dir) / f"{pmcid}.tar.gz"
            tgz_path.write_bytes(response.content)
            
            with tarfile.open(tgz_path, "r:gz") as archivo_tar:
                _extraer_tar_seguro(archivo_tar, Path(tmp_dir))
                
            extracted_files = [f for f in Path(tmp_dir).rglob("*") if f.is_file()]
            
            # 1. Buscar y extraer el PDF principal (suele ser el único .pdf en el paquete)
            for f in extracted_files:
                if f.suffix.lower() == ".pdf":
                    dest_pdf_name = f"pmc_{pmcid}_main.pdf"
                    destino_pdf = target_dir / dest_pdf_name
                    destino_pdf.write_bytes(f.read_bytes())
                    descargados.append(destino_pdf)
                    logger.info(f"[{pmcid}] PDF Principal extraído: {dest_pdf_name}")
            
            # 2. Buscar y extraer los archivos suplementarios/datos de interés
            # Si target_names está vacío, intentamos extraer cualquier archivo con las extensiones deseadas
            for f in extracted_files:
                ext = f.suffix.lower()
                if ext in TARGET_EXTENSIONS and ext != ".pdf":
                    # Verificar si coincide con los nombres declarados o simplemente lo guardamos por su extensión
                    is_candidate = False
                    if not target_names:
                        is_candidate = True
                    else:
                        is_candidate = any(t_name.lower() in f.name.lower() or f.name.lower() in t_name.lower() for t_name in target_names)
                    
                    if is_candidate:
                        nombre_seguro = _normalizar_nombre_archivo(f.name)
                        dest_file_name = f"pmc_{pmcid}_{nombre_seguro}"
                        destino_file = target_dir / dest_file_name
                        destino_file.write_bytes(f.read_bytes())
                        descargados.append(destino_file)
                        logger.info(f"[{pmcid}] Archivo de datos extraído: {dest_file_name}")
                        
    except (requests.RequestException, tarfile.TarError, OSError, ValueError) as e:
        logger.error(f"[{pmcid}] Error extrayendo archivos del tgz: {e}")
        
    return descargados


def buscar_y_descargar_pmc(query: str, temp_dir: Path, max_results: int = 5) -> List[Path]:
    """
    Busca artículos en PubMed Central, descarga sus paquetes Open Access y extrae 
    el PDF y los archivos suplementarios útiles (.xlsx, .csv, .xls, .docx).
    """
    logger.info(f"Iniciando búsqueda en PMC para: '{query}'")
    descargados = []
    
    # Refinar la consulta para enfocarse en artículos que contengan suplementos/datasets
    query_refinada = f"{query} AND (supplementary OR dataset OR table OR data)"
    
    try:
        handle = Entrez.esearch(db="pmc", term=query_refinada, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        time.sleep(SLEEP_INTERVAL)
        
        id_list = record.get("IdList", [])
        pmcids = [f"PMC{pid}" for pid in id_list]
        logger.info(f"[PMC] Se encontraron {len(pmcids)} artículos candidatos.")
        
        for pmcid in pmcids:
            title, files_suplementarios = obtener_detalles_pmc(pmcid)
            logger.info(f"[PMC] Artículo: '{title}' ({pmcid})")
            
            url_tgz = consultar_pmc_oa_tgz_url(pmcid)
            if not url_tgz:
                logger.warning(f"[PMC] Paquete Open Access no disponible para {pmcid}. Saltando...")
                continue
                
            files_desc = descargar_y_extraer_pmc(pmcid, url_tgz, temp_dir, files_suplementarios, title)
            descargados.extend(files_desc)
            
    except (RuntimeError, ValueError, OSError, HTTPError, URLError) as e:
        logger.error(f"[PMC] Error general en búsqueda de PubMed Central: {e}")
        
    return descargados


def ejecutar_scraper(query: str, temp_dir: Path, max_results: int = 5) -> List[Path]:
    """
    Orquesta la descarga desde Zenodo y PMC. Guarda todo en temp_dir.
    Retorna la lista de rutas a los archivos descargados.
    """
    temp_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ejecutando scraper unificado para query: '{query}' en directorio temporal: {temp_dir}")
    
    archivos_zenodo = buscar_y_descargar_zenodo(query, temp_dir, max_results)
    archivos_pmc = buscar_y_descargar_pmc(query, temp_dir, max_results)
    
    total_descargados = archivos_zenodo + archivos_pmc
    logger.info(f"Scraper finalizado. Total archivos descargados: {len(total_descargados)}")
    return total_descargados
