import pdftotext
import re
import pandas as pd
from typing import List, Dict
from datetime import date as Date
import calendar


class Parser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.transactions: List[Dict] = []
        self.coutas: List[Dict] = []
        self.cierre: Date = None
        self.vencimiento: Date = None

        self.patrones
        self.transaction_pattern = "^(?P<transaction_date>\s*\d{2}.\d{2}.\d{2})(?P<id_trans>\s+\d{6}\*)(?P<description>\s+[\w\s*. -]+(?:\([\w,\s]+\))?)(?P<amount>\s+\d{1,5}(?:.\d{2})?\d{1,5}(?:,\d{2})?)"
        self.cuotas_pattern = "^(?P<transaction_date>\s*\d{2}.\d{2}.\d{2})(?P<id_trans>\s+\d{6}\*)(?P<description>\s+[\w\s*. -]+(?:\([\w,\s]+\))?)(?P<coutas>\s+C.\d{2}/\d{2})(?P<amount>\s+\d{1,5}(?:.\d{2})?\d{1,5}(?:,\d{2})?)"
        self.cierre_pattern = "(CIERRE\s+ACTUAL\s+)(?P<dia>\d{2})\s+(?P<mes>[A-Za-z]{3})\s+(?P<anio>\d{2})"
        self.vencimiento_pattern = "(VENCIMIENTO\s+ACTUAL\s+)(?P<dia>\d{2})\s+(?P<mes>[A-Za-z]{3})\s+(?P<anio>\d{2})"

    def parse_pdf(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        with open(self.pdf_path, "rb") as file:
            pdf = pdftotext.PDF(file, physical=True)
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                lines = page.split("\n")
                for line in lines:
                    self._process_line(line.lstrip())
        
        return self._create_dataframes()

    def _process_line(self, line: str) -> None:
        match_transacciones = re.search(pattern=self.transaction_pattern, string=line)
        match_cuotas = re.search(pattern=self.cuotas_pattern, string=line)
        match_cierre = re.search(pattern=self.cierre_pattern, string=line)
        match_vencimiento = re.search(pattern=self.vencimiento_pattern, string=line)
        
        # Spanish month abbreviations dictionary
        meses_es = {
                "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
                "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12
            }

        if match_cierre:
            dia = int(match_cierre.group("dia"))
            mes_str = match_cierre.group("mes").upper()  # Still uppercase for consistency
            anio = 2000 + int(match_cierre.group("anio"))

            try:
                mes = meses_es[mes_str]
            except KeyError:
                print(f"Error: Invalid month abbreviation: {mes_str}")
                # Handle the error as needed, e.g., raise an exception, set a default, skip the line
                return  # Or raise a more specific exception

            self.cierre = Date(anio, mes, dia)

        if match_vencimiento:
            dia = int(match_vencimiento.group("dia"))
            mes_str = match_vencimiento.group("mes").upper()    # Still uppercase for consistency
            anio = 2000 + int(match_vencimiento.group("anio"))
            try:
                mes = meses_es[mes_str]
            except KeyError:
                print(f"Error: Invalid month abbreviation: {mes_str}")
                return
            
            self.vencimiento = Date(anio, mes, dia)

        if match_transacciones:
            self.transactions.append(match_transacciones.groupdict())
        elif match_cuotas:
            self.coutas.append(match_cuotas.groupdict())


    def _create_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        df_transaciones = pd.DataFrame(self.transactions)
        df_cuotas = pd.DataFrame(self.coutas)
        return df_transaciones, df_cuotas

# Ejemplo de uso:
"""
parser = Parser("./ERESUMEN  VISA.PDF2024-02-26.pdf")
df_trans, df_cuotas = parser.parse_pdf()
print(df_trans)
print(df_cuotas)
"""