from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Open connection to DB 
    #with db.engine.begin() as connection:
    #    result = connection.execute(sqlalchemy.text(sql_to_execute))

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
            #{
            #    "sku": "GREEN_POTION_0",
            #    "name": "green potion",
            #    "quantity": 1,
            #    "price": 50,
            #    # Color green
            #    "potion_type": [0, 100, 0, 0],
            #}
        ]
