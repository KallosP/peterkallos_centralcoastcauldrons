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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fetchall: fetches all (or all remaining) rows of a query result set and returns a list of tuples
        rows = result.fetchall()
        # Store the row corresponding to the green potion 
        greenPotionRow = rows[0]

        return [
                #{
                #    "sku": "RED_POTION_0",
                #    "name": "red potion",
                #    "quantity": 1,
                #    "price": 50,
                #    "potion_type": [100, 0, 0, 0],
                #}
                {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    # Dynamically set the quantity based on current value in table (on Supabase)
                    "quantity": greenPotionRow[1],
                    # Amt I'm selling a green potion for
                    "price": 50,
                    # Color green
                    "potion_type": [0, 100, 0, 0],
                }
        ]
        
