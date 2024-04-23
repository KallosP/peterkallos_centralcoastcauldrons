from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import random
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")


    with db.engine.begin() as connection:

        gold_paid = 0
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0

        total_quantity = 0

        for barrel_delivered in barrels_delivered:
            gold_paid += barrel_delivered.price * barrel_delivered.quantity

            total_quantity += barrel_delivered.quantity

            if barrel_delivered.potion_type == [1,0,0,0]:
                red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,1,0,0]:
                green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,0,1,0]:
                blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,0,0,1]:
                dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            else:
                raise Exception("Invalid potion type")

        current_time = str(connection.execute(sqlalchemy.text("SELECT time from present_time WHERE id = 1")).fetchone()[0])

        # next update the table:
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO global_inventory (gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, description, changed_at)
            VALUES
            (:gold_paid, :red_ml, :green_ml, :blue_ml, :dark_ml, :description, :changed_at)
            """
            ), [{"red_ml": red_ml, "green_ml": green_ml,
                "blue_ml": blue_ml, "dark_ml": dark_ml,
                "gold_paid": -gold_paid, "description": f"Purchased {total_quantity} barrels",
                "changed_at": current_time}])

    return "OK"

# Gets called once a day
@router.post("/plan")
# wholesale_catalog = the parameter
# : = a type hint (which is optional syntax) that indicates the expected type of a variable, in this case list[Barrel]
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    # robust inventory scheme = determine a threshold for your ml
    # wait to buy until you're below a certain amount of ml
    # once below, buy to get above that threshold (for each ml type).
    # don't write the logic to only buy when you have 0 ml for a certain type

    print(wholesale_catalog)

    purchasePlan = []

    with db.engine.begin() as connection:
        numGold = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM global_inventory")).fetchone()[0]
        print("PURCHASE PLAN: Gold = " + str(numGold))

        numRedMl = connection.execute(sqlalchemy.text("SELECT SUM(num_red_ml) FROM global_inventory")).fetchone()[0]
        print("PURCHASE PLAN: Num Red ml = " + str(numRedMl))

        numGreenMl = connection.execute(sqlalchemy.text("SELECT SUM(num_green_ml) FROM global_inventory")).fetchone()[0]
        print("PURCHASE PLAN: Num Green ml = " + str(numGreenMl))

        numBlueMl = connection.execute(sqlalchemy.text("SELECT SUM(num_blue_ml) FROM global_inventory")).fetchone()[0]
        print("PURCHASE PLAN: Num Blue ml = " + str(numBlueMl))

        numDarkMl = connection.execute(sqlalchemy.text("SELECT SUM(num_dark_ml) FROM global_inventory")).fetchone()[0]
        print("PURCHASE PLAN: Num Dark ml = " + str(numDarkMl))

        # Priorities:
        #   1) Always be in stock


        # If any of the ml colors are at or below this threshold, buy that type
        threshold = 200

        # Stop purchasing when below 60 gold
        if numGold < 60:
            print("Not purchasing: " + str(purchasePlan))
            return purchasePlan

        # If any ml type is below the threshold, this purchase plan will only restock 
        if numRedMl < threshold or numBlueMl < threshold or numGreenMl < threshold:
            for barrel in wholesale_catalog:
                # NOTE: Change this logic in the future to be more efficient,
                #       intentionally blocking the purchase of barrels if i have all potion types (r,g,b) in inventory.
                #       Basically, I'm always purchasing barrels when I don't have potions of a certain type, otherwise,don't purchase.
                # Always prioritizes purchasing a barrel for the potions I don't have in stock
                # NOTE: can't rely on your code ordering to prioritize certain barrel types, 
                #       the wholesale_catalog is always ordered randomly

                # If below threshold, resupply
                # If above threshold, buy large barrel if possible
                # TODO: improve logic to be more efficient later
                # NOTE: blue seems to cost more for larger barrels (more valuable?)

                if numRedMl < threshold and barrel.sku == "SMALL_RED_BARREL" and numGold >= barrel.price:
                    print("Entered red")
                    numGold = numGold - barrel.price
                    purchasePlan.append(
                        {
                            "sku": "SMALL_RED_BARREL",
                            "quantity": 1
                        }
                    )
                if numGreenMl < threshold and barrel.sku == "SMALL_GREEN_BARREL" and numGold >= barrel.price:
                    print("Entered green")
                    numGold = numGold - barrel.price
                    purchasePlan.append(
                        {
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1
                        }
                    )
                if numBlueMl < threshold and barrel.sku == "SMALL_BLUE_BARREL" and numGold >= barrel.price:
                    print("Entered blue")
                    numGold = numGold - barrel.price
                    purchasePlan.append(
                        {
                            "sku": "SMALL_BLUE_BARREL",
                            "quantity": 1
                        }
                    )
        # FIXME: Change this to be more spread out/efficient, don't just buy one type
        # If all ml are above threshold, dump all gold into random ml type
        else:
            # Only allow dark ml to be purchased if have a good amount of gold; currently set at 850
            if numGold >= 850:
                # 4 = exclusive
                randInt = random.randint(0, 4)
            else:
                randInt = random.randint(0, 3)

            if randInt == 0:
                randMlType = "RED"
            elif randInt == 1:
                randMlType = "GREEN"
            elif randInt == 2:
                randMlType = "BLUE"
            else:
                randMlType = "DARK"

            for barrel in wholesale_catalog:
                if numGold >= barrel.price and (randMlType in barrel.sku):
                    print("Buying extra ml from " + barrel.sku)

                    amtToBuy = numGold // barrel.price
                    if amtToBuy > barrel.quantity:
                        amtToBuy = barrel.quantity

                    print("Amt to buy: " + str(amtToBuy))

                    purchasePlan.append(
                        {
                            "sku": barrel.sku,
                            "quantity": amtToBuy
                        }
                    )               
                    numGold = numGold - (amtToBuy * barrel.price)
                    print("Gold after purchase attempt: " + str(numGold))
    print("My attempted Purchas Plan: " + str(purchasePlan))
    return purchasePlan

