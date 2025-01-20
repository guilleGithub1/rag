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
from models.resumen import GastoDB, ResumenDB, CuotaDB
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
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
                # Descargar archivo de S3
                self.s3_client.download_file(
                    Bucket=bucket_name,
                    Key=key,
                    Filename=temp_file.name
                )
                
                # Parsear PDF
                parser = Parser(temp_file.name)
                df_trans, df_cuotas = parser.parse_pdf()
                

            emision = parser.cierre  # Assuming cierre is the emision date
            vencimiento = parser.vencimiento  # Assuming vencimiento is the vencimiento date

            resumen = ResumenDB(
                fecha=date.today(),
                banco="BBVA",
                marca="VISA", 
                vencimiento=vencimiento,
                emision=emision
            )
            self.db.add(resumen)

            for _, row in df_trans.iterrows():
                fecha_transaccion = datetime.strptime(row['transaction_date'], '%d.%m.%y').date() # Convert the string date to date object

                gasto = GastoDB(
                    fecha=fecha_transaccion,
                    comercio=row['description'],  # Assuming 'description' contains comercio
                    monto=float(row['amount'].replace(".", "").replace(",", ".")), # Convert to float
                    banco=resumen.banco,
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
                    banco=resumen.banco,
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
            # Crear instancia de MailManager
            mail_manager = MailManager(target_subject=subject, target_sender=sender)
            
            # Procesar emails y guardar localmente
            mail_manager.process_emails()
            
            # Subir archivos a S3
            resumenes_dir = os.path.join(".", 'resumenes')
            s3_manager = S3Manager(bucket_name="aws-resumenes", s3_client=self.s3_client)
            
            archivos_subidos = []
            
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