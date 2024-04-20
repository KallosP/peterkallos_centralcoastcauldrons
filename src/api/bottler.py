from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
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
            # json.dumps converts int list to jsonb format
            connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity = quantity + {potion.quantity} WHERE potion_type = :potion_type"), [{"potion_type": json.dumps(potion.potion_type)}])

            red_ml = potion.potion_type[0]
            green_ml = potion.potion_type[1]
            blue_ml = potion.potion_type[2]
            dark_ml = potion.potion_type[3]

            connection.execute(sqlalchemy.text(
            """
            UPDATE global_inventory SET
            num_red_ml = num_red_ml - :red_ml,
            num_green_ml = num_green_ml - :green_ml,
            num_blue_ml = num_blue_ml - :blue_ml,
            num_dark_ml = num_dark_ml - :dark_ml
            """
            ), [{"red_ml": red_ml, "green_ml": green_ml,
                "blue_ml": blue_ml, "dark_ml": dark_ml}])

            ## If a red potion
            #if potion.potion_type[0] == 100:
            #    # Update database
            #    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions + {potion.quantity}, num_red_ml = num_red_ml - {potion.quantity * 100} WHERE id = {1}"))

            ## If a green potion
            #if potion.potion_type[1] == 100:
            #    # Update database
            #    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {potion.quantity}, num_green_ml = num_green_ml - {potion.quantity * 100} WHERE id = {1}"))

            ## If a blue potion
            #if potion.potion_type[2] == 100:
            #    # Update database
            #    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions + {potion.quantity}, num_blue_ml = num_blue_ml - {potion.quantity * 100} WHERE id = {1}"))

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
        # TODO: don't use *
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory WHERE id = 1")).fetchone()[0]
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory WHERE id = 1")).fetchone()[0]
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory WHERE id = 1")).fetchone()[0]
        dark_ml = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory WHERE id = 1")).fetchone()[0]
        # TODO: USE??
        #numGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone()[0]
        #print("PURCHASE PLAN: Gold - " + str(numGold))

        #numRedPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE id = 1")).fetchone()[0]
        #print("PURCHASE PLAN: Num Red Potions - " + str(numRedPotions))

        #numGreenPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE id = 2")).fetchone()[0]
        #print("PURCHASE PLAN: Num Green Potions - " + str(numGreenPotions))

        #numBluePotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE id = 3")).fetchone()[0]
        #print("PURCHASE PLAN: Num Blue Potions - " + str(numBluePotions))

        # POTION MIXING LOGIC:
        # NOT IN STOCK - potions that aren't in stock are iterated through and ATTEMPTED to be restocked up to 
        #                   a certain threshold defined by potionThreshold. It is possible to run out of ml before
        #                   reaching the threshold; this is accounted for and it'll only return as many potions
        #                   as the current number of ml allows. Being at the threshold = in stock.
        potionThreshold = 2
        # Store all potions that are below the threshold
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions WHERE quantity < :quantity"), [{"quantity": potionThreshold}])
        potionTypeNotInStock = result.fetchall()

        bottle_plan = []

        # If list is not empty (i.e. some potions are out of stock), mix all potions that are 0
        # (evaluates to true if not empty)
        # NOT IN STOCK
        if potionTypeNotInStock:
            for potionInfo in potionTypeNotInStock:
                potionType = potionInfo[5]
                realQuantity = potionInfo[3]

                quantityToAdd = 0
                # Try to bottle up to the threshold
                for i in range(potionThreshold):
                    # Only bottle if you have sufficient ml
                    if ((red_ml - potionType[0] >= 0 and green_ml - potionType[1] >= 0
                        and blue_ml - potionType[2] >= 0 and dark_ml - potionType[3] >= 0)
                        # Ensures no purchases go over the threshold (above threshold is handled by IN STOCK logic)
                        and (quantityToAdd + realQuantity) < potionThreshold):

                        quantityToAdd += 1
                        red_ml -= potionType[0]
                        green_ml -= potionType[1]
                        blue_ml -= potionType[2]
                        dark_ml -= potionType[3]
                        #print("Red ml: " + str(red_ml))
                        #print("Blue ml: " + str(blue_ml))
                        
                if quantityToAdd > 0:
                    bottle_plan.append(
                        {
                            "potion_type": potionType,
                            "quantity": quantityToAdd
                        }
                    )

        # Mix remaining ml evenly across all potions in table
        # IN STOCK, only executed when in-stock  
        else:
            result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
            potionTypeList = result.fetchall()

            for potionInfo in potionTypeList:
                potionType = potionInfo[5]

                # Check if enough ml of every type for this particular potion
                if (red_ml - potionType[0] >= 0 and green_ml - potionType[1] >= 0
                    and blue_ml - potionType[2] >= 0 and dark_ml - potionType[3] >= 0):

                    
                    red_ml -= potionType[0]
                    green_ml -= potionType[1]
                    blue_ml -= potionType[2]
                    dark_ml -= potionType[3]

                    bottle_plan.append(
                        {
                            "potion_type": potionType,
                            # FIXME: Change later to make more efficient instead of always returning 1
                            "quantity": 1
                        }
                    )

        # TODO: 1) prioritize making potions that are out of stock
        #       2) if everything is in-stock, randomly distribute the conversion of ml to 
        #           the different potions types that currently exist in the DB (aka make dynamic)

        #print("red: " + str(red_ml))
        #print("blue: " + str(blue_ml))
        #print("green: " + str(green_ml))
        #print("dark: " + str(dark_ml))


        #if red_ml >= 50 and blue_ml >= 50:
        #    bottle_plan.append(
        #        {
        #            "potion_type": [50, 0, 50, 0],
        #            "quantity": (red_ml // 50),
        #        }
        #    )
        #if red_ml >= 100:
        #    bottle_plan.append(
        #        {
        #            "potion_type": [100, 0, 0, 0],
        #            # // rounds down to an integer
        #            "quantity": (red_ml // 100),
        #        }
        #    )
        #if green_ml >= 100:
        #    bottle_plan.append(
        #        {
        #            "potion_type": [0, 100, 0, 0],
        #            "quantity": (green_ml // 100),
        #        }
        #    )
        #if blue_ml >= 100:
        #    bottle_plan.append(
        #        {
        #            "potion_type": [0, 0, 100, 0],
        #            "quantity": (blue_ml // 100),
        #        }
        #    )
        #if dark_ml >= 100:
        #    bottle_plan.append(
        #        {
        #            "potion_type": [0, 0, 0, 100],
        #            "quantity": (dark_ml // 100),
        #        }
        #    )
        
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