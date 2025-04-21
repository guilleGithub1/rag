from fastapi import APIRouter, HTTPException, Depends
from models.resumen import Resumen, MailResumen, Banco, Patron
from services.resumen import ResumenService  # Importamos la clase
from sqlalchemy.orm import Session
from config.s3 import S3Manager
from config.database import DatabaseManager
from config.mail import MailManager
from boto3 import client
from typing import List, Dict
import os


router = APIRouter(prefix="/resumenes", tags=["resumen"])




@router.get("/get_archivos", response_model=List, status_code=201)
async def get_archivos_s3(s3: client = Depends(S3Manager.get_s3)):
        service = ResumenService(None, s3)
        archivos = service.get_s3_files(bucket_name="aws-resumenes")
        return archivos


@router.get("/actualizar_resumen", response_model=Resumen, status_code=201)
async def actualizar_resumen(key:str=None,s3: client = Depends(S3Manager.get_s3), db: Session = Depends(DatabaseManager.get_db_dependency), banco: str = None):
        service = ResumenService(db=db,s3_client=s3)
        archivos = service.actualizar_resumen_db(key= 'ERESUMEN  VISA.PDF2024-02-26.pdf', bucket_name="aws-resumenes")
        return archivos


@router.post("/descargar_resumenes", response_model=List[str], status_code=201)
async def descargar_resumenes(datos_mail: MailResumen,s3: client = Depends(S3Manager.get_s3), db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(db=db, s3_client=s3)
        archivos = service.obtener_resumenes(subject=datos_mail.subject, sender=datos_mail.sender)
        return archivos


@router.post("/agregar_banco", response_model=Banco, status_code=201)
async def agregar_banco(banco: Banco=None,  db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(db=db)
        archivos = service.agregar_banco(banco=banco)
        return archivos


@router.post("/agregar_patron", response_model=Patron, status_code=201)
async def agregar_patron(patron: Patron=None,  db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(db=db)
        resultado = service.agregar_patron(patron=patron)
        return resultado



@router.get("/lineas_pdf", response_model=None, status_code=201)
async def lineas_pdf(nombre_archivo:str=None):
        service = ResumenService(db=None,s3_client=None)
        archivos = service.get_lineas_resumen(nombre_archivo='./resumenes/20250201.PDF')
        return archivos

@router.get("/get_mails", response_model=list[Dict], status_code=201)
async def get_mails(mail:MailManager = Depends(MailManager.get_mail_dependency),db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(mail=mail, db=db)
        archivos = service.get_mails()
        return archivos

@router.post("/agregar_resumen", response_model=List[str], status_code=201)
async def agregar_resumen(db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(db=db)


        # Aquí puedes agregar la lógica para obtener el resumen y guardarlo en la base de datos
        # Por ejemplo, si tienes un archivo PDF en una ruta específica:
        path = './resumenes'

        # Crear una instancia del servicio
        service = ResumenService(db=db)
        archivos_procesados = []
        # Listar todos los archivos en el directorio
        for archivo in os.listdir(path):
                archivo_path = os.path.join(path, archivo)
                if os.path.isfile(archivo_path):
                        try:
                                service.nuevo_resumen(path_pdf=archivo_path)
                                archivos_procesados.append(archivo)
                        except Exception as e:
                                # Puedes loggear o manejar errores por archivo aquí si lo deseas
                                pass
        return archivos_procesados