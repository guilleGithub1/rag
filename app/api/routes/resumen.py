from fastapi import APIRouter, HTTPException, Depends
from models.resumen import Resumen
from services.resumen import ResumenService  # Importamos la clase
from sqlalchemy.orm import Session
from config.s3 import S3Manager
from boto3 import client
from typing import List, Dict

router = APIRouter(prefix="/resumenes", tags=["resumen"])

@router.get("/get_archivos", response_model=List, status_code=201)
async def get_archivos_s3(s3: client = Depends(S3Manager.get_s3)):
        service = ResumenService(None, s3)
        archivos = service.get_s3_files(bucket_name="aws-resumenes")
        return archivos


@router.get("/actualizar", response_model=Resumen, status_code=201)
async def actualizar_db(s3: client = Depends(S3Manager.get_s3)):
        service = ResumenService(s3_client=s3)
        archivos = service.actualizar_db(key= 'ERESUMEN  VISA.PDF2024-02-26.pdf', bucket_name="aws-resumenes")
        return archivos