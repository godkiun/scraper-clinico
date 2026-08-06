"""Pruebas unitarias básicas de utilidades de seguridad del scraper."""

import tarfile
import unittest
from pathlib import Path

from scraper import _miembro_tar_es_seguro, _normalizar_nombre_archivo


class PruebasSeguridadScraper(unittest.TestCase):
    """Valida controles de sanitización y extracción segura."""

    def test_normaliza_nombre_archivo(self):
        nombre_original = "tabla clínica 2026?.csv"
        nombre_normalizado = _normalizar_nombre_archivo(nombre_original)
        self.assertEqual(nombre_normalizado, "tabla_clínica_2026_.csv")

    def test_miembro_tar_seguro_en_ruta_valida(self):
        directorio_base = Path("C:/tmp/base")
        miembro = tarfile.TarInfo(name="carpeta/datos.csv")
        self.assertTrue(_miembro_tar_es_seguro(directorio_base, miembro))

    def test_miembro_tar_inseguro_por_path_traversal(self):
        directorio_base = Path("C:/tmp/base")
        miembro = tarfile.TarInfo(name="../escape/payload.sh")
        self.assertFalse(_miembro_tar_es_seguro(directorio_base, miembro))

    def test_miembro_tar_inseguro_por_symlink(self):
        directorio_base = Path("C:/tmp/base")
        miembro = tarfile.TarInfo(name="enlace")
        miembro.type = tarfile.SYMTYPE
        self.assertFalse(_miembro_tar_es_seguro(directorio_base, miembro))


if __name__ == "__main__":
    unittest.main()
