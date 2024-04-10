from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

# Catalog tells the bots what they can/cannot buy

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
        numGreenPotions = greenPotionRow[1] 

        if numGreenPotions > 0:

            return [
                    {

                        # FIXME: correct sku?
                        "sku": "GREEN_POTION_0",
                        "name": "green potion",
                        # Dynamically set the quantity based on current value in table (on Supabase)
                        # Note: temporarily hardcoded to 1 to meet requirements for version 1, change back later to greenPotionRow[1]
                        "quantity": 1, #greenPotionRow[1],
                        # Amt I'm selling a green potion for
                        # TODO: change back to 50, just 1 temporarily for testing
                        "price": 1,
                        # Color green. AKA selling green potions
                        "potion_type": [0, 100, 0, 0],
                    }
            ]
    # Don't advertise anything if you have nothing
    return []
        
