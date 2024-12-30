from models.user import User, UserDB
from sqlalchemy.orm import Session
from fastapi import HTTPException

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: User):
        db_user = UserDB(**user.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user_by_id(self, user_id: int):
        return self.db.query(UserDB).filter(UserDB.id == user_id).first()

    def get_all_users(self):
        return self.db.query(UserDB).all()

    def update_user(self, user_id: int, updated_user: User):
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
    
        for key, value in updated_user.dict(exclude_unset=True).items():
            setattr(db_user,key,value)
    
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    

    def delete_user(self, user_id: int):
        user = self.get_user_by_id(user_id)
        if not user:
          return None
        self.db.delete(user)
        self.db.commit()
        return {"message":"Usuario borrado correctamente"}