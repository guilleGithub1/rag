from fastapi import APIRouter, HTTPException, Depends
from models.resumen import Resumen, MailResumen
from services.resumen import ResumenService  # Importamos la clase
from sqlalchemy.orm import Session
from config.s3 import S3Manager
from config.database import DatabaseManager
from boto3 import client
from typing import List, Dict



router = APIRouter(prefix="/resumenes", tags=["resumen"])




@router.get("/get_archivos", response_model=List, status_code=201)
async def get_archivos_s3(s3: client = Depends(S3Manager.get_s3)):
        service = ResumenService(None, s3)
        archivos = service.get_s3_files(bucket_name="aws-resumenes")
        return archivos


@router.get("/actualizar_resumen", response_model=Resumen, status_code=201)
async def actualizar_resumen(key:str=None,s3: client = Depends(S3Manager.get_s3), db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(db=db,s3_client=s3)
        archivos = service.actualizar_resumen_db(key= 'ERESUMEN  VISA.PDF2024-02-26.pdf', bucket_name="aws-resumenes")
        return archivos


@router.post("/descargar_resumenes", response_model=List[str], status_code=201)
async def descargar_resumenes(datos_mail: MailResumen,s3: client = Depends(S3Manager.get_s3), db: Session = Depends(DatabaseManager.get_db_dependency)):
        service = ResumenService(db=db, s3_client=s3)
        archivos = service.obtener_resumenes(subject=datos_mail.subject, sender=datos_mail.sender)
        return archivos