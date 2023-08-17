from typing import Annotated
from fastapi import Header, HTTPException
import psycopg2
import os
from settings import BASE_DIR


async def authenticate_token(authtoken: Annotated[str, Header()]):
    if authtoken != "123456789":
        return {'status': False, 'data': "User not authenticated"}
    

def createDBConnection():
    try :
        connection = psycopg2.connect(
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            host='localhost',
            port=int(os.getenv('DB_PORT')),
            database=os.getenv('DB_DATABASE'),
        )
        return connection
    except Exception as e:
        raise HTTPException(status_code=400, detail="Connection lost")
