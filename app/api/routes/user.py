from fastapi import APIRouter, HTTPException, Depends
from models.user import User
from services.user import UserService  # Importamos la clase
from sqlalchemy.orm import Session
from config.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User, status_code=201)
async def create_user(user: User, db: Session = Depends(get_db)):
    user_service = UserService(db)  # Instancia del servicio
    created_user = user_service.create_user(user)
    return created_user

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=list[User])
async def get_all_users(db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.get_all_users()


@router.put("/{user_id}", response_model=User)
async def update_user(user_id:int, updated_user:User, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.update_user(user_id,updated_user)
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}")
async def delete_user(user_id:int, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.delete_user(user_id)
    if not user:
      raise HTTPException(status_code=404, detail="User not found")
    return user