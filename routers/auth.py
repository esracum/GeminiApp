from fastapi import APIRouter, Depends, HTTPException, Request
from pyasn1_modules.rfc7508 import Algorithm
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from fastapi.templating import Jinja2Templates
from models import Base,Todo



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

SECRET_KEY = "t123bzzxhalyfzmq4pyqbg6i66t2cs7v"
ALGORITHM = "HS256"
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")
class  CreateUserRequest(BaseModel):
    username: str
    email : str
    first_name : str
    last_name : str
    password : str
    role : str

def authenticate_user(db: db_dependency,username:str, password:str):
    user = db.query(User).filter(User.username==username).first()

    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

class Token(BaseModel):
    access_token: str
    token_type:str

def create_access_token(username:str, user_id:int, role:str, expires_delta: timedelta):
    payload = {'sub':username, 'id': user_id, 'role':role}
    expires = datetime.now(timezone.utc)+expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = User(
        username = create_user_request.username,
        email = create_user_request.email,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        role = create_user_request.role,
        is_active = True,
        hashed_password = bcrypt_context.hash(create_user_request.password)
    )
    db.add(user)
    db.commit()

async def get_current_user(token:Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username = payload.get('sub')
        user_id = payload.get('id')
        user_role =payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="username or ID is invalid")
        return {'username': username, 'id':user_id, 'role':user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token is invalid")



@router.post("/token", response_model = Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],
                                 db: db_dependency):
    user = authenticate_user(db,form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")
    token = create_access_token(user.username,user.id,user.role, timedelta(minutes=60))
    return {"access token:":token, "token_type":"bearer"}