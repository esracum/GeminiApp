from fastapi import APIRouter, Depends, Path, HTTPException,status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from models import Base,Todo
from database import engine, SessionLocal

router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=2000)
    priority: int = Field(gt=0, lt=6)
    complete: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/read_all")
async def read_all(db: db_dependency):
    return db.query(Todo).all()

@router.get("/get_by_id/{todo_id}", status_code = status.HTTP_200_OK)
async def read_by_id(db: db_dependency, todo_id: int= Path(gt=0) ):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Todo not found")




@router.post("/create_todo", status_code=status.HTTP_201_CREATED)
async def create_todo(todo_request: TodoRequest,db: db_dependency ):
    todo = Todo(**todo_request.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@router.put("/update_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency,todo_request: TodoRequest, todo_id: int = Path(gt=0) ):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    todo = db.query(Todo).filter(Todo.id == todo_id).first()

    if todo is None:
        print("Todo not found!")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete

    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@router.delete("/delete_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency,todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    #db.query(Todo).filter(Todo.id==todo_id).delete() doğru şeyi sildiğinden emin olmak için
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}