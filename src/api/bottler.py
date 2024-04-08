from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    # FIXME: Where to handle ml to potion conversion logic?

    # Mix all available green ml if any exists
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fetchall: fetches all (or all remaining) rows of a query result set and returns a list of tuples
        rows = result.fetchall()
        # Store the row corresponding to the green potion 
        greenPotionRow = rows[0]
        # Amount of green liquid
        greenML = greenPotionRow[2]
        # Bottle green potions until we're out of greenML
        while greenML >= 100:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {1}, num_green_ml = num_green_ml - {100} WHERE id = {1}"))
            greenML -= 100


        
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    
    # Bottle all barrels into green potions
    return[
        {
            "potion_type": [0, 100, 0, 0],
            # FIXME: calculate quantity based on num greenML ?
            "quantity": 5,
        }
    ]

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    #return [
    #    {
    #        "potion_type": [100, 0, 0, 0],
    #        "quantity": 5,
    #    }
    #]

if __name__ == "__main__":
    print(get_bottle_plan())