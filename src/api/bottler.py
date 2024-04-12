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

# Deliver is where you're recieving the bot's response to what you requested in plan.
# You have to update your table with the information that the bot is giving you b/c
# that is the accurate data (the bot is like the bank)
@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    # Add bottles and subtract ml to databse. This is
    # where you're actually editing the values in your table.
    # Use the information stored in potions_delivered and change
    # your database to reflect the same info that potions_delivered contains

    with db.engine.begin() as connection:
        # Parse/store recieved data
        for potion in potions_delivered:
            # If a red potion
            if potion.potion_type[0] == 100:
                # Update database
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions + {potion.quantity}, num_red_ml = num_red_ml - {potion.quantity * 100} WHERE id = {1}"))

            # If a green potion
            if potion.potion_type[1] == 100:
                # Update database
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {potion.quantity}, num_green_ml = num_green_ml - {potion.quantity * 100} WHERE id = {1}"))

            # If a blue potion
            if potion.potion_type[2] == 100:
                # Update database
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions + {potion.quantity}, num_blue_ml = num_blue_ml - {potion.quantity * 100} WHERE id = {1}"))

    return "OK"

# Plan is where you're VIEWING what you have in your table and your intended course of action is what you're returning
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Query your database to see how much ml you have and if it's
    # possible to convert/make potions, if it's possible, return
    # how much you need/want. If you don't have enough, then just
    # return an empty amount

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fetchall: fetches all (or all remaining) rows of a query result set and returns a list of tuples
        rows = result.fetchall()
        # Store the row corresponding to the green potion 
        potionRow = rows[0]

        redML = potionRow[5]
        greenML = potionRow[2]
        blueML = potionRow[7]

        bottle_plan = []

        print(greenML)

        if redML >= 100:
            bottle_plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    # // rounds down to an integer
                    "quantity": (redML // 100),
                }
            )
        if greenML >= 100:
            bottle_plan.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": (greenML // 100),
                }
            )
        if blueML >= 100:
            bottle_plan.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": (blueML // 100),
                }
            )
        
        print("get_bottle_plan() returns: " + str(bottle_plan))

        return bottle_plan
    
    

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