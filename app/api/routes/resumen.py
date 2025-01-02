from fastapi import APIRouter, HTTPException, Depends
from models.user import User
from services.resumen import ResumenService  # Importamos la clase
from sqlalchemy.orm import Session
from config.database import get_db

router = APIRouter(prefix="/resumenes", tags=["resumen"])

@router.get("/", response_model=User, status_code=201)
async def get_archivos(user: User, db: Session = Depends(get_db)):
    json=ResumenService.get_archivos_onedrive('dfsdfds')
    return json