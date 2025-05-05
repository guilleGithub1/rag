import boto3 
from models.user import User, UserDB
from config.onedrive import *
from config.database import *
from config.s3 import S3Manager
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict
from botocore.exceptions import ClientError 
from utils.parseVisa import Parser
import tempfile
from datetime import datetime, timedelta, date
from models.resumen import GastoDB, ResumenDB, CuotaDB, BancoDB, Banco, PatronDB, Patron, MailDB, ResumenPdfDB
from config.mail import MailManager
import os
import pdftotext
import re 


class ResumenService:
    def __init__(self, db: Session = None, s3_client: boto3.client= None, mail: MailManager = None):
        self.db = db
        self.s3_client = s3_client
        self.mail = mail 

    def crear_resumen(self, user: User):
        db_user = ResumenDB(**user.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_resumen(self, user_id: int):
        resumen = self.db.query(ResumenDB).filter(ResumenDB.id == user_id).first()
        if resumen is None:
            raise HTTPException(status_code=404, detail="Resumen no encontrado")
        return resumen
    
    def get_resumenes(self):
        return self.db.query(ResumenDB).all()   
    
    def update_resumen(self, user_id: int, user: User):       
        db_user = self.db.query(ResumenDB).filter(ResumenDB.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="Resumen no encontrado")
        for var, value in user.dict().items():
            setattr(db_user, var, value)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_banco_by_name(self, nombre_banco: str):
        """
        Obtiene un banco por su nombre
        """
        return self.db.query(BancoDB).filter(BancoDB.nombre == nombre_banco).first()
    
    def get_lista_bancos(self):
        """
        Obtiene la lista de bancos
        """
        return self.db.query(BancoDB).all()
    
    def get_fecha(self, date_str: str) -> date:
        """Convierte string de fecha a objeto date"""
        formats = ['%d.%m.%y', '%d-%b-%y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"No se pudo convertir la fecha: {date_str}")
    
    def get_marcas(self, nombre_banco: str)-> List[str]:
        """
        Obtiene las marcas de un banco que cuyo valor sea True en la base de datos. 
        Ejemplo, si el valor de visa es true, se obtiene la marca VISA
        """
        banco = self.get_banco_by_name(nombre_banco)
        marcas = []
        if banco.patrones_visa:
            marcas.append("VISA")
        if banco.patrones_mastercard:
            marcas.append("Master")
        if banco.patrones_amex:
            marcas.append("AMEX")
        return marcas
    
    def get_patron_by_id(self, patron_id: int):
        """
        Obtiene un patron por su id
        """
        return self.db.query(PatronDB).filter(PatronDB.id == patron_id).first()
    
    def get_patrones(self, banco: BancoDB, marca: str = None) -> Dict[str, str]:
        """
        Obtiene diccionario con los patrones específicos de una marca
        Args:
            banco (BancoDB): Banco a consultar
            marca (str): Marca de la tarjeta
        Returns:
            Dict[str, str]: Diccionario con patrones {transaccion, transaccion_cuota, fecha_cierre, fecha_vencimiento}
        """
        try:
            if not marca:
                return {}
                
            marca = marca.upper()
            patron = None
            
            if marca == "VISA":
                patron = banco.patron_visa
            elif marca == "MASTER" or marca == "MASTERCARD":
                patron = banco.patron_mastercard
            elif marca == "AMEX":
                patron = banco.patron_amex
                
            if patron:
                return {
                    "transaccion": patron.transacion,
                    "transaccion_cuota": patron.transaccion_cuota,
                    "fecha_cierre": patron.fecha_cierre,
                    "fecha_vencimiento": patron.fecha_vencimiento,
                    "ancho_maximo": patron.ancho_maximo, 
                    "ancho_pesos": patron.ancho_pesos,
                    "ancho_dolares": patron.ancho_dolares,
                }
                
            return {}
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo patrones: {str(e)}"
            )

    

    def convert_amount_to_float(self, amount_str: str) -> float:
        """
        Convierte string de monto a float, manejando signo negativo al final
        """
        # Remover espacios
        amount_str = amount_str.strip()
        
        # Verificar signo negativo al final
        is_negative = amount_str.endswith('-')
        if is_negative:
            amount_str = amount_str[:-1]  # Remover el '-'
        
        # Convertir a float
        amount = float(amount_str.replace(".", "").replace(",", "."))
        
        # Aplicar signo si corresponde
        return -amount if is_negative else amount

    def get_s3_files(self, bucket_name: str) -> List[Dict]:
        """
        Obtiene la lista de archivos almacenados en S3.
        
        Returns:
            List[Dict]: Lista de archivos con sus metadatos
        """
        try:
            # Inicializar el manager
            s3_manager = S3Manager(bucket_name=bucket_name, s3_client=self.s3_client)
            
            # Obtener lista de archivos
            archivos = s3_manager.list_files(bucket_name=bucket_name)
            
            if not archivos:
                return []
                
            # Formatear respuesta
            resultado = []
            for archivo in archivos:
                resultado.append({
                    'nombre: ' + archivo
                })
                
            return resultado
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener archivos de S3: {str(e)}"
            )

    def actualizar_resumen_db(self, key: str, bucket_name: str):
        """
        Procesa archivo PDF de S3 y actualiza la base de datos.
        
        Args:
            key (str): Nombre del archivo en S3
            bucket_name (str): Nombre del bucket
        """
        try:

            bancos= self.get_lista_bancos()
            for banco in bancos:
                marcas = self.get_marcas(banco.nombre)
                for marca in marcas:
                    s3_manager = S3Manager(bucket_name=bucket_name, s3_client=self.s3_client)
                    # Obtener lista de archivos
                    lista_resumenes = s3_manager.get_files_by_keywords(keyword1=banco.nombre, keyword2=marca, bucket_name=bucket_name)
                    
                    for archivo in lista_resumenes:
                       
                        # Crear archivo temporal
                        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
                            # Descargar archivo de S3
                            self.s3_client.download_file(
                                Bucket=bucket_name,
                                Key=archivo,
                                Filename=temp_file.name
                            )
                            
                            # Parsear PDF
                            patrones = self.get_patrones(banco, marca)
                            parser = Parser(temp_file.name, patrones=patrones)
                            df_trans, df_cuotas = parser.parse_pdf()
                        

                        emision = parser.cierre  # Assuming cierre is the emision date
                        vencimiento = parser.vencimiento  # Assuming vencimiento is the vencimiento date

                        resumen = ResumenDB(
                            banco_id=banco.id,
                            marca=marca, 
                            vencimiento=vencimiento,
                            emision=emision
                        )
                        self.db.add(resumen)

                        for _, row in df_trans.iterrows():
                            fecha_transaccion = row['transaction_date']

                            gasto = GastoDB(
                                fecha=fecha_transaccion,
                                comercio=row['description'],  # Assuming 'description' contains comercio
                                monto=self.convert_amount_to_float(row['amount']),
                                moneda=row['moneda'],
                                marca=resumen.marca,
                                resumen=resumen  # Link to ResumenDB
                            )
                            self.db.add(gasto)

                        
                        for _, row in df_cuotas.iterrows():
                            fecha_transaccion = row['transaction_date']
                            cuotas_parts = row['cuotas'].split("/")
                            numero_cuota_pagada = int(cuotas_parts[0].replace("C.", "").strip())
                            cantidad_cuotas = int(cuotas_parts[1].strip())

                            gasto = GastoDB(
                                fecha=fecha_transaccion,
                                comercio=row['description'],  # Assuming 'description' contains comercio
                                monto=float(row['amount'].replace(".", "").replace(",", ".")), # Convert to float
                                marca=resumen.marca,
                                moneda=row['moneda'],
                                resumen=resumen  # Link to ResumenDB
                            )
                            cuota = CuotaDB(
                                cantidad_cuotas=cantidad_cuotas,
                                numero_cuota_pagada=numero_cuota_pagada,
                                gasto=gasto
                            )
                            self.db.add(cuota)

                        self.db.commit()  # Commit changes to the database
                        self.db.refresh(resumen) # Refresh the resumen_db object

            return resumen  # Return the Pydantic Resumen model

        except Exception as e:
            self.db.rollback() # Rollback in case of an error
            raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")



    def obtener_resumenes(self, subject: str, sender: str):
        """
        Obtiene resumenes desde emails y los sube a S3
        
        Args:
            subject (str): Asunto del correo
            sender (str): Remitente del correo
        """
        try:
            archivos_subidos = []
            bancos_db = self.get_lista_bancos()

            for banco in bancos_db:

                # Crear instancia de MailManager
                mail_manager = MailManager(target_subject=banco.subject, target_sender=banco.sender, banco=banco.nombre)
                
                # Procesar emails y guardar localmente
                mail_manager.process_emails()
                
                # Subir archivos a S3
                resumenes_dir = os.path.join(".", 'resumenes')
                s3_manager = S3Manager(bucket_name="aws-resumenes", s3_client=self.s3_client)
                
            
                
                # Subir cada archivo a S3
                with s3_manager.get_s3_session() as s3:
                    for archivo in os.listdir(resumenes_dir):
                        local_path = os.path.join(resumenes_dir, archivo)
                        s3_manager.upload_file(local_path, archivo)
                        archivos_subidos.append(archivo)
                            
                    # Limpiar archivos locales
                    #os.remove(local_path)
            
            return archivos_subidos
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al procesar resumenes: {str(e)}"
            )
        

    def agregar_banco(self, banco: Banco):
        """
        Agrega un nuevo banco a la base de datos
        
        Args:
            nombre_banco (str): Nombre del banco
            re_busqueda (str): Expresión regular para buscar emails
        """
        try:


            banco = BancoDB(
                nombre=banco.nombre,
                patron_busqueda=banco.patron_busqueda,
                subject=banco.subject,
                sender=banco.sender,
                patron_visa=self.get_patron_by_id(banco.patrones_visa),
                patron_amex=self.get_patron_by_id(banco.patrones_amex),
                patron_mastercard=self.get_patron_by_id(banco.patrones_mastercard)
            )
            
            self.db.add(banco)
            self.db.commit()
            self.db.refresh(banco)

            # Convertir a diccionario antes de validar
            banco_dict = {
            "id": banco.id,
            "nombre": banco.nombre,
            "patron_busqueda": banco.patron_busqueda,
            "subject": banco.subject,
            "sender": banco.sender,
        }
        
            return Banco.model_validate(banco_dict)
                        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al agregar banco: {str(e)}"
            )
        
    
    def agregar_patron(self,  patron: Patron):
        """
        Agrega un nuevo patron a la base de datos   
        """
        try:
            patron = PatronDB(
                transacion=patron.transaccion,
                transaccion_cuota=patron.transaccion_cuota,
                fecha_cierre=patron.fecha_cierre,
                fecha_vencimiento=patron.fecha_vencimiento,
                descripcion=patron.descripcion,
                ancho_maximo=patron.ancho_maximo
            )
            
            self.db.add(patron)
            self.db.commit()
            self.db.refresh(patron)
            return patron   
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al agregar patron: {str(e)}"
            )
        
    def get_lineas_resumen(self, nombre_archivo: str):

        with open(nombre_archivo, "rb") as file:
            pdf = pdftotext.PDF(file, physical=True)
            lines = []
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                lines += page.split("\n")

            return lines
        

    def get_texto_pdf(self, nombre_archivo: str):

        with open(nombre_archivo, "rb") as file:
            pdf = pdftotext.PDF(file, physical=True)
            page = []
            for page_num in range(len(pdf)):
                page += pdf[page_num]

            return page
        
    def get_resumen_bbva(self, subject: str, sender: str) -> str:
        """
        Obtiene link del email especificado
        
        Args:
            subject (str): Asunto del correo
            sender (str): Remitente del correo
        Returns:
            str: URL encontrada
        """
        try:

            

            
            # Extraer link
            link = self.mail.extract_links_from_emails(subject, sender)
            
            if not link:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontró link en el email"
                )
                
            return link
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo link: {str(e)}"
            )    
        
    def download_files_from_links(self, emails_data: List[Dict]) -> List[str]:
        """
        Descarga archivos desde links BBVA
        Args:
            emails_data (List[Dict]): Lista de diccionarios con {fecha, link}
        Returns:
            List[str]: Lista de archivos descargados
        """
        downloaded_files = []
        
        try:
            for email_data in emails_data:
                fecha = email_data['fecha']
                link = email_data['link']
                
                # Crear nombre archivo
                filename = f"BBVA_resumen_{fecha.strftime('%Y-%m-%d')}.pdf"
                filepath = os.path.join(".", 'resumenes', filename)
                
                # Descargar archivo
                response = requests.get(link)
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    downloaded_files.append(filename)
                    
            return downloaded_files
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error descargando archivos: {str(e)}"
            )
    
    def get_link_adjunto(contenido: str, patron_link_adjunto: str) -> str:
        """
        Obtiene link de archivo adjunto en el contenido del email
        Args:
            contenido (str): Contenido del email
        Returns:
            str: Link encontrado
        """
        try:
            # Buscar link en el contenido
            link = re.search(patron_link_adjunto, contenido)
            if link:
                return link.group(0)
            return ""
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo link adjunto: {str(e)}"
            )

    def get_contenido_pdf(self, link_descarga:str) -> str: 

        with open(link_descarga, "rb") as file:
            pdf = pdftotext.PDF(file, physical=True)
            contenido = ""
            for page_num in range(len(pdf)):
                contenido += pdf[page_num]
            return contenido
        

    
    def get_mails(self) -> List[Dict]:
        """
        Obtiene mails de todos los bancos configurados
        Returns:
            List[Dict]: Lista de mails encontrados
        """
        try:
            all_mails = []
            bancos = self.get_lista_bancos()
            
            for banco in bancos:

                # Obtener mails del banco

                mails_banco = self.mail.get_lista_mails(
                        banco.patron_busqueda,
                        banco.sender, 
                        banco.archivo_adjunto, 
                        banco.patron_link_descarga
                    )
                for mail in mails_banco:
                    mail['banco'] = banco.nombre



                    maildb=MailDB(
                        mail_gmail_id=mail['mail_id'],
                        fecha=mail['fecha'],
                        contenido_mail=mail['contenido']
                    )

                    if banco.archivo_adjunto:
                        contenido_pdf = mail['contenido_adjunto']
       
                    adjunto_db=ResumenPdfDB(
                            nombre=banco.nombre + "_" + str(mail['fecha']) ,
                            mail=maildb,
                            link_descarga="",
                            contenido_pdf=contenido_pdf
                        )

                    self.db.add(adjunto_db)               
                    self.db.add(maildb)


                    
                    parser = Parser(contenido_pdf=contenido_pdf)
                    marca = parser.get_marca_tarjeta()
                    patrones = self.get_patrones(banco, marca=marca)
                    parser.set_patrones(patrones)


                    cierre, vencimiento = parser.extract_fechas()
                    df_trans, df_cuotas = parser.get_gastos_cuotas()

                    resumen = ResumenDB(
                        banco_id=banco.id,
                        marca=marca,
                        vencimiento=vencimiento,
                        cierre=cierre, 
                        mail=maildb,
                        emision=mail['fecha'],
                    )


                    for _, row in df_trans.iterrows():
                            fecha_transaccion = row['transaction_date']

                            gasto = GastoDB(
                                fecha=fecha_transaccion,
                                comercio=row['description'],  # Assuming 'description' contains comercio
                                monto=self.convert_amount_to_float(row['amount']),
                                moneda=row['moneda'],
                                marca=resumen.marca,
                                resumen=resumen  # Link to ResumenDB
                            )
                            self.db.add(gasto)

                        
                    for _, row in df_cuotas.iterrows():
                            fecha_transaccion = row['transaction_date']
                            cuotas_parts = row['cuotas'].split("/")
                            numero_cuota_pagada = int(cuotas_parts[0].replace("C.", "").strip())
                            cantidad_cuotas = int(cuotas_parts[1].strip())

                            gasto = GastoDB(
                                fecha=fecha_transaccion,
                                comercio=row['description'],  # Assuming 'description' contains comercio
                                monto=float(row['amount'].replace(".", "").replace(",", ".")), # Convert to float
                                marca=resumen.marca,
                                moneda=row['moneda'],
                                resumen=resumen  # Link to ResumenDB
                            )
                            cuota = CuotaDB(
                                cantidad_cuotas=cantidad_cuotas,
                                numero_cuota_pagada=numero_cuota_pagada,
                                gasto=gasto
                            )
                            self.db.add(cuota)


                    self.db.add(resumen)

                    self.db.commit()
                    self.db.refresh(maildb)

                
                all_mails.extend(mails_banco)
                
            return all_mails
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo mails: {str(e)}"
            )
        

    def nuevo_resumen(self, path_pdf: str):
        """
        Crea un nuevo resumen   
        """ 

        try:

            bancos=self.get_bancos()

            # Leer el contenido del PDF
            contenido_pdf = self.get_contenido_pdf(path_pdf)

            # Crear un objeto parser
            parser = Parser(contenido_pdf=contenido_pdf)
            marca= parser.get_marca_tarjeta()

            banco = parser.get_banco(bancos)

            patrones = self.get_patrones(banco, marca)
            parser.set_patrones(patrones)


            cierre, vencimiento = parser.extract_fechas()
            df_trans, df_cuotas = parser.get_gastos_cuotas()

            resumen = ResumenDB(
                        banco_id=banco.id,
                        marca=marca,
                        vencimiento=vencimiento,
                        cierre=cierre, 
                    )

            # Agregar resumen a la sesión de base de datos
            self.db.add(resumen)

            for _, row in df_trans.iterrows():
                fecha_transaccion = row['transaction_date']

                gasto = GastoDB(
                    fecha=fecha_transaccion,
                    comercio=row['description'],
                    monto=self.convert_amount_to_float(row['amount']),
                    moneda=row['moneda'],
                    marca=resumen.marca,
                    resumen=resumen
                )
                self.db.add(gasto)

                    
            for _, row in df_cuotas.iterrows():
                fecha_transaccion = row['transaction_date']
                cuotas_parts = row['cuotas'].split("/")
                numero_cuota_pagada = int(cuotas_parts[0].replace("C.", "").strip())
                cantidad_cuotas = int(cuotas_parts[1].strip())

                gasto = GastoDB(
                    fecha=fecha_transaccion,
                    comercio=row['description'],
                    monto=float(row['amount'].replace(".", "").replace(",", ".")),
                    marca=resumen.marca,
                    moneda=row['moneda'],
                    resumen=resumen
                )
                cuota = CuotaDB(
                    cantidad_cuotas=cantidad_cuotas,
                    numero_cuota_pagada=numero_cuota_pagada,
                    gasto=gasto
                )
                self.db.add(cuota)

            self.db.commit()

        except Exception as e:
            self.db.rollback()  # Añadido rollback en caso de error
            raise HTTPException(
                status_code=500,
                detail=f"Error al crear resumen: {str(e)}"
            )
        return resumen


        

    def get_banco(self, nombre_banco: str):
        """
        Obtiene un banco por su nombre
        """
        return self.db.query(BancoDB).filter(BancoDB.nombre == nombre_banco).first()
    
    def get_bancos(self):
        """
        Obtiene un banco por su nombre
        """
        return self.db.query(BancoDB).all()
    
