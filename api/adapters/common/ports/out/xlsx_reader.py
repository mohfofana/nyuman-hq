import zipfile
from io import BytesIO
from typing import Any, List

from openpyxl import load_workbook

from use_cases.common.ports.out.tableur_reader import Classeur, TableurIllisibleException, TableurReader

# Garde-fous : un tableau d'équipe tient largement dans ces limites ; au-delà, on refuse plutôt que de saturer le serveur.
MAX_LIGNES = 2000
MAX_COLONNES = 40
MAX_DECOMPRESSE = 50 * 1024 * 1024


def _valeur(cell) -> Any:
    value = cell.value
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Les pourcentages restent lisibles (« 2 % » plutôt que 0,02).
        if "%" in (getattr(cell, "number_format", "") or ""):
            return f"{value * 100:g} %".replace(".", ",")
    return value


class XlsxReader(TableurReader):
    """Lit un classeur Excel (.xlsx), par exemple un tableau Google téléchargé. Valeurs seulement, pas les formules."""

    def read(self, content: bytes) -> Classeur:
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if sum(info.file_size for info in archive.infolist()) > MAX_DECOMPRESSE:
                    raise TableurIllisibleException("Ce fichier est trop gros pour être repris.")
            workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        except TableurIllisibleException:
            raise
        except Exception as exc:
            raise TableurIllisibleException() from exc

        classeur: Classeur = {}
        try:
            for sheet in workbook.worksheets:
                rows: List[List[Any]] = []
                for row in sheet.iter_rows(max_row=MAX_LIGNES, max_col=MAX_COLONNES):
                    rows.append([_valeur(cell) for cell in row])
                classeur[sheet.title] = rows
        finally:
            workbook.close()
        return classeur
