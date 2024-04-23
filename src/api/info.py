from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src import database as db
import sqlalchemy

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):

    # Update current time in database for reference
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            UPDATE present_time SET 
            time = :time
            WHERE id = 1
            """
            ), [{"time": str(timestamp)}])
            
    """
    Share current time.
    """
    return "OK"

