from fastapi import APIRouter, HTTPException, Depends
from models.resumen import Resumen
from services.resumen import ResumenService  # Importamos la clase
from sqlalchemy.orm import Session
from config.s3 import S3Manager
from boto3 import client

router = APIRouter(prefix="/resumenes", tags=["resumen"])

@router.get("/", response_model=Resumen, status_code=201)
async def get_archivos_s3(Resumen: None, s3: client = Depends(S3Manager.get_s3_session)):
        service = ResumenService(s3)
        archivos = service.get_s3_files()
        return archivos