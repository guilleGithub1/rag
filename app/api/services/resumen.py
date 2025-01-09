import boto3 
from models.user import User, UserDB
from models.resumen import *
from config.onedrive import *
from config.database import *
from config.s3 import S3Manager
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict
from botocore.exceptions import ClientError 
from utils.parseVisa import Parser
import tempfile

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

    def actualizar_db(self, key: str, bucket_name: str):
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
                
                # Crear objeto Resumen
                resumen = ResumenDB(
                    fecha=df_trans['transaction_date'].iloc[0],
                    banco="BBVA",
                    marca="VISA"
                )
                
                # Guardar en DB
                self.db.add(resumen)
                self.db.commit()
                self.db.refresh(resumen)
                
                return resumen
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al procesar archivo: {str(e)}"
            )