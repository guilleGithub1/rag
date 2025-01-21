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
from models.resumen import GastoDB, ResumenDB, CuotaDB, BancoDB, Banco
from config.mail import MailManager
import os


class ResumenService:
    def __init__(self, db: Session = None, s3_client: boto3.client= None):
        self.db = db
        self.s3_client = s3_client

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
    
    def get_marcas(self, nombre_banco: str)-> List[str]:
        """
        Obtiene las marcas de un banco que cuyo valor sea True en la base de datos. 
        Ejemplo, si el valor de visa es true, se obtiene la marca VISA
        """
        banco = self.get_banco_by_name(nombre_banco)
        marcas = []
        if banco.visa:
            marcas.append("VISA")
        if banco.mastercard:
            marcas.append("MASTERCARD")
        if banco.amex:
            marcas.append("AMEX")
        return marcas

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
                            parser = Parser(temp_file.name)
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
                            fecha_transaccion = datetime.strptime(row['transaction_date'], '%d.%m.%y').date() # Convert the string date to date object

                            gasto = GastoDB(
                                fecha=fecha_transaccion,
                                comercio=row['description'],  # Assuming 'description' contains comercio
                                monto=self.convert_amount_to_float(row['amount']),
                                marca=resumen.marca,
                                resumen=resumen  # Link to ResumenDB
                            )
                            self.db.add(gasto)

                        
                        for _, row in df_cuotas.iterrows():
                            fecha_transaccion = datetime.strptime(row['transaction_date'], '%d.%m.%y').date() # Convert the string date to date object
                            cuotas_parts = row['coutas'].split("/")
                            numero_cuota_pagada = int(cuotas_parts[0].replace("C.", "").strip())
                            cantidad_cuotas = int(cuotas_parts[1].strip())

                            gasto = GastoDB(
                                fecha=fecha_transaccion,
                                comercio=row['description'],  # Assuming 'description' contains comercio
                                monto=float(row['amount'].replace(".", "").replace(",", ".")), # Convert to float
                                marca=resumen.marca,
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
                    os.remove(local_path)
            
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
                visa= banco.visa,
                mastercard= banco.mastercard,
                amex= banco.amex
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
            "visa": banco.visa,
            "mastercard": banco.mastercard,
            "amex": banco.amex
        }
        
            return Banco.model_validate(banco_dict)
                        
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al agregar banco: {str(e)}"
            )