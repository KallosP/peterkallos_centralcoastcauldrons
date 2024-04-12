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

    catalog = []

    # Open connection to DB 
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fetchall: fetches all (or all remaining) rows of a query result set and returns a list of tuples
        rows = result.fetchall()
        # Store the row corresponding to the green potion 
        # TODO: change from just green to generic
        potionRow = rows[0]
        numGreenPotions = potionRow[1] 
        numRedPotions = potionRow[4] 
        numBluePotions = potionRow[6] 

        # Put up any potion for sale that's in stock
        if numRedPotions > 0:
            catalog.append(
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": 1, #greenPotionRow[1],
                    "price": 1,
                    "potion_type": [100, 0, 0, 0],
                }
            )
        if numGreenPotions > 0:
            catalog.append(
                {

                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    # Dynamically set the quantity based on current value in table (on Supabase)
                    # NOTE: temporarily hardcoded to 1 to meet requirements for version 1, change back later to greenPotionRow[1]
                    # TODO: make dynamic once cart is implemented
                    "quantity": 1, #greenPotionRow[1],
                    # Amt I'm selling a green potion for
                    # TODO: change back to 50, just 1 temporarily for testing
                    "price": 1,
                    # Color green. AKA selling green potions
                    "potion_type": [0, 100, 0, 0],
                }
            )
        if numBluePotions > 0:
            catalog.append(
                {
                    "sku": "BLUE_POTION_0",
                    "name": "blue potion",
                    "quantity": 1, #greenPotionRow[1],
                    "price": 1,
                    "potion_type": [0, 0, 100, 0],
                }
            )

    print("Catalog: " + str(catalog))
    # Can return empty json [], this means don't advertise anything since you have nothing
    return catalog
        
