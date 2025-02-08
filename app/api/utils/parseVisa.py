import pdftotext
import re
import pandas as pd
from typing import List, Dict
from datetime import date as Date, datetime
import calendar


class Parser:
    def __init__(self,  contenido_pdf: str, patrones: Dict[str, str] = None):
        self.pdf_path = str = None
        self.transactions: List[Dict] = []
        self.coutas: List[Dict] = []
        self.cierre: Date = None
        self.vencimiento: Date = None
        self.contenido = contenido_pdf

        self.transaction_pattern =  None
        self.cuotas_pattern = None
        self.cierre_pattern = None
        self.vencimiento_pattern =   None
        self.ancho_maximo = None

        '''
        visa:
        ^(?P<fecha>.{11})(?P<id>\d{6})\*(?P<Descripcion>.{68})(?P<monto_pesos>.{9}-?)?(?P<monto_dolares>.{2})?
        ^(?P<fecha>.{11})(?P<id>\d{6})\*(?P<Descripcion>.{33})(?P<cuota>.{9})(?P<monto_pesos>.{35})?(?P<monto_dolares>.{2})?
        
        ^(?P<fecha>.{10})(?P<Descripcion>.{38})(?P<id>.{6})(?P<monto_pesos>.{28})?(?P<monto_dolares>.{25})?
        ^(?P<fecha>.{10})(?P<Descripcion>.{35})(?P<cuota>.{6})?(?P<id>.{6})(?P<monto_pesos>.{26})?(?P<monto_dolares>.{25})?

        (?P<transaction_date>\d{2}-[A-Za-z]{3}-\d{2})\s+(?P<description>.+?)\s+(?P<id_trans>\d+)\s+(?P<amount>\d{1,}(?:\.\d{3})*(?:,\d{2})?)
        (?P<transaction_date>\d{2}-[A-Za-z]{3}-\d{2})\s+(?P<description>.+?)\s+(?P<cuotas>\d{2}/\d{2})\s+(?P<id_trans>\d+)\s+(?P<amount>\d{1,}(?:\.\d{3})*(?:,\d{2})?)
        self.transaction_pattern = "^(?P<transaction_date>\s*\d{2}.\d{2}.\d{2})(?P<id_trans>\s+\d{6}\*)(?P<description>\s+[\w\s*. -]+(?:\([\w,\s]+\))?)(?P<amount>\s+\d{1,5}(?:.\d{2})?\d{1,5}(?:,\d{2})?-?)"
        self.cuotas_pattern = "^(?P<transaction_date>\s*\d{2}.\d{2}.\d{2})(?P<id_trans>\s+\d{6}\*)(?P<description>\s+[\w\s*. -]+(?:\([\w,\s]+\))?)(?P<coutas>\s+C.\d{2}/\d{2})(?P<amount>\s+\d{1,5}(?:.\d{2})?\d{1,5}(?:,\d{2})?-?)"
        self.cierre_pattern = "(CIERRE\s+ACTUAL\s+)(?P<dia>\d{2})\s+(?P<mes>[A-Za-z]{3})\s+(?P<anio>\d{2})"
        self.vencimiento_pattern = "(VENCIMIENTO\s+ACTUAL\s+)(?P<dia>\d{2})\s+(?P<mes>[A-Za-z]{3})\s+(?P<anio>\d{2})"
        '''

    def parse_pdf(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        with open(self.pdf_path, "rb") as file:
            pdf = pdftotext.PDF(file, physical=True)
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                lines = page.split("\n")
                for line in lines:
                    self._process_line(line.lstrip())
        
        return self._create_dataframes()

    def get_contenido_pdf(self) -> str: 
        with open(self.pdf_path, "rb") as file:
            pdf = pdftotext.PDF(file, physical=True)
            contenido = ""
            for page_num in range(len(pdf)):
                contenido += pdf[page_num]
            return contenido

    def _process_line(self, line: str) -> None:
        
        # Spanish month abbreviations dictionary
        meses_es = {
                "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
                "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12
            }
        # Procesar fecha de cierre y vencimiento
        try:
            match_cierre = re.search(pattern=self.cierre_pattern, string=line)
            if match_cierre:
                self.cierre = self.parse_date(match_cierre.group("fecha"))

            match_vencimiento = re.search(pattern=self.vencimiento_pattern, string=line)
            if match_vencimiento:
                self.vencimiento = self.parse_date(match_vencimiento.group("fecha"))

        # Procesar transacciones y cuotas
            match_transacciones = re.search(pattern=self.transaction_pattern, string=line)
            match_cuotas = re.search(pattern=self.cuotas_pattern, string=line)

            if match_transacciones:
                transaction_dict = match_transacciones.groupdict()
        
                transaction = {
                    'transaction_date': self.parse_date(transaction_dict['transaction_date'].strip()),
                    'description': transaction_dict['description'].strip(),
                    'id_trans': transaction_dict['id_trans'].strip(),
                    'amount':  transaction_dict['amount'].strip(),
                    'moneda': self.get_moneda(line)
                }
                self.transactions.append(transaction)
            
            elif match_cuotas:

                cuotas_dict = match_cuotas.groupdict()

                cuota = {
                    'transaction_date': self.parse_date(cuotas_dict['transaction_date'].strip()),
                    'description': cuotas_dict['description'].strip(),
                    'id_trans': cuotas_dict['id_trans'].strip(),
                    'amount': cuotas_dict['amount'].strip(),
                    'cuotas': cuotas_dict['cuotas'].strip(),
                    'moneda': self.get_moneda(line)
                }
                print(cuota)
                self.coutas.append(cuota)

        except KeyError as e:
            raise ValueError(f"Campo requerido no encontrado: {str(e)}")
            
        except ValueError as e:
            raise ValueError(f"Error al convertir valor: {str(e)}")
            
        except AttributeError as e:
            raise ValueError(f"Error en formato de datos: {str(e)}")
            
        except Exception as e:
            raise RuntimeError(f"Error procesando línea: {str(e)}")

    def _create_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        df_transaciones = pd.DataFrame(self.transactions) 
        df_cuotas = pd.DataFrame(self.coutas)
        return df_transaciones, df_cuotas
    

    def get_moneda(self, line: str) -> str:
        return "USD" if len(line.strip()) >= self.ancho_maximo else "PESOS"
    
    def parse_date(self, date_str: str) -> Date:
        """
        Convierte string a Date
        Args:
            date_str: Fecha en formato '10.05.19' o '10-May-19'
        Returns:
            Date: Objeto fecha convertido
        """
        meses = {
            'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Ago': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'
        }

        try:
            # Intentar formato dd.mm.yy
            if '.' in date_str:
                return datetime.strptime(date_str.strip(), '%d.%m.%y').date()
                
            # Intentar formato dd-mmm-yy
            if '-' in date_str:
                dia, mes, anio = date_str.strip().split('-')
                mes_numero = meses.get(mes, '01')
                fecha_str = f"{dia}.{mes_numero}.{anio}"
                return datetime.strptime(fecha_str, '%d.%m.%y').date()
                    
            # Intentar formato dd-mmm-yy
            if ' ' in date_str:
                dia, mes, anio = date_str.strip().split(' ')
                mes_numero = meses.get(mes, '01')
                fecha_str = f"{dia}.{mes_numero}.{anio}"
                return datetime.strptime(fecha_str, '%d.%m.%y').date()
                
            raise ValueError(f"Formato de fecha no soportado: {date_str}")
            
        except Exception as e:
            raise ValueError(f"Error convirtiendo fecha {date_str}: {str(e)}")

    def extract_fechas(self) -> tuple[str, str]:
        """
        Extrae fechas de cierre y vencimiento
        Args:
            contenido_pdf: Contenido del PDF
        Returns:
            tuple[str, str]: (fecha_cierre, fecha_vencimiento)
        """
        try:
            fecha_cierre = ''
            fecha_vencimiento = ''
            
            for linea in self.contenido.split('\n'):
                # Buscar fecha cierre
                match_cierre = re.search(self.cierre_pattern, linea)
                if match_cierre:
                    fecha_cierre = self.parse_date(match_cierre.group('cierre'))
                    
                # Buscar fecha vencimiento    
                match_vencimiento = re.search(self.vencimiento_pattern, linea)
                if match_vencimiento:
                    fecha_vencimiento = self.parse_date(match_vencimiento.group('vencimiento'))
                    
            return (fecha_cierre, fecha_vencimiento)
                
        except Exception as e:
            print(f"Error extrayendo fechas: {str(e)}")
            return ('', '')


    def get_marca_tarjeta(self) -> str:
        """
        Detecta tipo de tarjeta en texto
        Args:
            texto (str): Texto a analizar
        Returns:
            str: VISA, MASTERCARD, AMEX o string vacío
        """
        try:
            # Usar grupo de captura para obtener el texto exacto
            mastercard_match = re.search(r'(MASTERCARD)', self.contenido, re.IGNORECASE)
            visa_match = re.search(r'(VISA)', self.contenido, re.IGNORECASE)
            amex_match = re.search(r'(AMEX)', self.contenido, re.IGNORECASE)
            
            if mastercard_match:
                return "MASTERCARD"  # Retornar siempre en mayúsculas
            elif visa_match:
                return "VISA"
            elif amex_match:
                return "AMEX"
                
            return ""
            
        except Exception as e:
            print(f"Error detectando tipo tarjeta: {str(e)}")
            return ""

    def set_patrones(self, patrones: Dict[str, str]) -> 'Parser':
        """
        Asigna patrones después de crear instancia
        Args:
            patrones: Diccionario con patrones
        Returns:
            Parser: self para encadenamiento
        """
        self.transaction_pattern = patrones["transaccion"]
        self.cuotas_pattern = patrones["transaccion_cuota"]
        self.cierre_pattern = patrones["fecha_cierre"]
        self.vencimiento_pattern = patrones["fecha_vencimiento"]
        self.ancho_maximo = patrones["ancho_maximo"]
        return self


    def get_gastos_cuotas(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extrae gastos y cuotas de PDF
        Args:
            contenido_pdf: Contenido del PDF
        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: (gastos, cuotas)
        """
        try:
            gastos = []
            cuotas = []
            for linea in self.contenido.split('\n'):
                # Buscar transacciones
                match_transaccion = re.search(self.transaction_pattern, linea)
                if match_transaccion:
                    transaction_dict = match_transaccion.groupdict()
            
                    gastos = {
                        'transaction_date': self.parse_date(transaction_dict['transaction_date'].strip()),
                        'description': transaction_dict['description'].strip(),
                        'id_trans': transaction_dict['id_trans'].strip(),
                        'amount':  transaction_dict['amount'].strip(),
                        'moneda': self.get_moneda(linea)
                    }
                    self.transactions.append(gastos)

                # Buscar cuotas
                match_cuota = re.search(self.cuotas_pattern, linea)
                if match_cuota:
                    cuotas_dict = match_cuota.groupdict()

                    cuota = {
                        'transaction_date': self.parse_date(cuotas_dict['transaction_date'].strip()),
                        'description': cuotas_dict['description'].strip(),
                        'id_trans': cuotas_dict['id_trans'].strip(),
                        'amount': cuotas_dict['amount'].strip(),
                        'cuotas': cuotas_dict['cuotas'].strip(),
                        'moneda': self.get_moneda(linea)
                    }
                    print(cuota)
                    self.coutas.append(cuota)

            return (pd.DataFrame(self.transactions), pd.DataFrame(self.coutas))
        
        except Exception as e:
            print(f"Error extrayendo gastos y cuotas: {str(e)}")
            return (pd.DataFrame(), pd.DataFrame())
        


# Patrones de búsqueda para Visa    
# Ejemplo de uso:ffff
"""
parser = Parser("./ERESUMEN  VISA.PDF2024-02-26.pdf")
df_trans, df_cuotas = parser.parse_pdf()
print(df_trans)
print(df_cuotas)
"""