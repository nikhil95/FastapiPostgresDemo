from typing import Union

from fastapi import FastAPI

from typing import List
import databases
import sqlalchemy
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import os
import urllib

host_server = os.environ.get('host_server', 'localhost')
db_server_port = urllib.parse.quote_plus(str(os.environ.get('db_server_port', '5432')))
database_name = os.environ.get('database_name', 'fastapi')
db_username = urllib.parse.quote_plus(str(os.environ.get('db_username', 'postgres')))
db_password = urllib.parse.quote_plus(str(os.environ.get('db_password', 'secret')))
ssl_mode = urllib.parse.quote_plus(str(os.environ.get('ssl_mode','prefer')))
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}?sslmode={}'.format(db_username, db_password, host_server, db_server_port, database_name, ssl_mode)

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

projects = sqlalchemy.Table(
    "projects",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
)

engine = sqlalchemy.create_engine(
    #DATABASE_URL, connect_args={"check_same_thread": False}
    DATABASE_URL, pool_size=3, max_overflow=0
)
metadata.create_all(engine)

class ProjectIn(BaseModel):
    name: str
    completed: bool

class Project(BaseModel):
    id: int
    name: str
    completed: bool
        
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/projects/", response_model=Project, status_code = status.HTTP_201_CREATED)
async def create_project(project: ProjectIn):
    query = projects.insert().values(name=project.name, completed=project.completed)
    last_record_id = await database.execute(query)
    return {**project.dict(), "id": last_record_id}

@app.get("/projects/", response_model=List[Project], status_code = status.HTTP_200_OK)
async def read_projects(skip: int = 0, take: int = 20):
    query = projects.select().offset(skip).limit(take)
    return await database.fetch_all(query)

