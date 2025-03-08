from http.client import HTTPException
from typing import Annotated
from fastapi import status
from fastapi import FastAPI, Depends, Path
from sqlalchemy.orm import Session
from models import Base,Todo
from database import engine, SessionLocal

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/read_all")
async def read_all(db: db_dependency):
    return db.query(Todo).all()

@app.get("/get_by_id/{todo_id}", status_code = status.HTTP_200_OK)
async def read_by_id(db: db_dependency, todo_id: int= Path(gt=0) ):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Todo not found")

