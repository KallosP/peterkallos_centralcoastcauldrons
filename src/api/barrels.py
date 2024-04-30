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
        # TODO: Can make this more efficient by only having one SELECT statement/putting
        #       commas between each column (i.e. ...SUM(gold), SUM(num_red_ml),... ...)
        numGold = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM global_inventory")).fetchone()[0]
        #numGold = 3500
        print("PURCHASE PLAN: Gold = " + str(numGold))

        numRedMl = connection.execute(sqlalchemy.text("SELECT SUM(num_red_ml) FROM global_inventory")).fetchone()[0]
        #numRedMl = 200
        print("PURCHASE PLAN: Num Red ml = " + str(numRedMl))

        numGreenMl = connection.execute(sqlalchemy.text("SELECT SUM(num_green_ml) FROM global_inventory")).fetchone()[0]
        #numGreenMl = 200
        print("PURCHASE PLAN: Num Green ml = " + str(numGreenMl))

        numBlueMl = connection.execute(sqlalchemy.text("SELECT SUM(num_blue_ml) FROM global_inventory")).fetchone()[0]
        #numBlueMl = 200
        print("PURCHASE PLAN: Num Blue ml = " + str(numBlueMl))

        numDarkMl = connection.execute(sqlalchemy.text("SELECT SUM(num_dark_ml) FROM global_inventory")).fetchone()[0]
        print("PURCHASE PLAN: Num Dark ml = " + str(numDarkMl))

        # Priorities:
        #   1) Always be in stock


        # If any of the ml colors are at or below this threshold, buy that type
        threshold = 200

        # Stop purchasing when below 60 gold
        # FIXME: Edge case where shop has no potions and gold is less than 60,
        #        then shop will get stuck: won't buy or sell (probably will never happen??)
        if numGold < 300:
            for barrel in wholesale_catalog:
                # < 300 b/c potion bottling threshold/min to have in stock is 2 potions in bottler;
                # when that gets sold will have 300 red ml left, don't buy more, buy other ml's that
                # are at 0
                if numRedMl < 100 and barrel.sku == "SMALL_RED_BARREL" and numGold >= barrel.price:
                    print("Entered init red")
                    numGold = numGold - barrel.price
                    purchasePlan.append(
                        {
                            "sku": "SMALL_RED_BARREL",
                            "quantity": 1
                        }
                    )
                if numGreenMl < 100 and barrel.sku == "SMALL_GREEN_BARREL" and numGold >= barrel.price:
                    print("Entered init green")
                    numGold = numGold - barrel.price
                    purchasePlan.append(
                        {
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1
                        }
                    )
                if numBlueMl < 100 and barrel.sku == "SMALL_BLUE_BARREL" and numGold >= barrel.price:
                    print("Entered init blue")
                    numGold = numGold - barrel.price
                    purchasePlan.append(
                        {
                            "sku": "SMALL_BLUE_BARREL",
                            "quantity": 1
                        }
                    )
        # TODO: Check if capacity has been reached, don't purchase if so

        # If any ml type is below the threshold, this purchase plan will only restock 
        #if (numRedMl < threshold or numBlueMl < threshold or numGreenMl < threshold):
        #    for barrel in wholesale_catalog:
        #        # NOTE: Change this logic in the future to be more efficient,
        #        #       intentionally blocking the purchase of barrels if i have all potion types (r,g,b) in inventory.
        #        #       Basically, I'm always purchasing barrels when I don't have potions of a certain type, otherwise,don't purchase.
        #        # Always prioritizes purchasing a barrel for the potions I don't have in stock
        #        # NOTE: can't rely on your code ordering to prioritize certain barrel types, 
        #        #       the wholesale_catalog is always ordered randomly

        #        # If below threshold, resupply
        #        # If above threshold, buy large barrel if possible
        #        # TODO: improve logic to be more efficient later
        #        # NOTE: blue seems to cost more for larger barrels (more valuable?)

        #        if numRedMl < threshold and barrel.sku == "SMALL_RED_BARREL" and numGold >= barrel.price:
        #            print("Entered red")
        #            numGold = numGold - barrel.price
        #            purchasePlan.append(
        #                {
        #                    "sku": "SMALL_RED_BARREL",
        #                    "quantity": 1
        #                }
        #            )
        #        if numGreenMl < threshold and barrel.sku == "SMALL_GREEN_BARREL" and numGold >= barrel.price:
        #            print("Entered green")
        #            numGold = numGold - barrel.price
        #            purchasePlan.append(
        #                {
        #                    "sku": "SMALL_GREEN_BARREL",
        #                    "quantity": 1
        #                }
        #            )
        #        if numBlueMl < threshold and barrel.sku == "SMALL_BLUE_BARREL" and numGold >= barrel.price:
        #            print("Entered blue")
        #            numGold = numGold - barrel.price
        #            purchasePlan.append(
        #                {
        #                    "sku": "SMALL_BLUE_BARREL",
        #                    "quantity": 1
        #                }
        #            )
        ## FIXME: Change this to be more spread out/efficient, don't just buy one type
        else:
            # If red is under threshold or has the least amount, buy red
            if numRedMl < threshold or ((numRedMl < numBlueMl) and (numRedMl < numGreenMl)):
                mlTypeToBuy = "RED"
            # If blue is under threshold or has the least amount, buy blue 
            elif numBlueMl < threshold or ((numBlueMl < numRedMl) and (numBlueMl< numGreenMl)):
                mlTypeToBuy = "BLUE"
            # If green is under threshold or has the least amount, buy green 
            elif numGreenMl < threshold or ((numGreenMl < numRedMl) and (numGreenMl < numBlueMl)):
                mlTypeToBuy = "GREEN"
            # Otherwise choose randomly (edge case in which all ml types are exactly at the threshold)
            else:
                randInt = random.randint(0, 3)
                if randInt == 0:
                    mlTypeToBuy = "RED"
                elif randInt == 1:
                    mlTypeToBuy = "GREEN"
                else: 
                    mlTypeToBuy = "BLUE"

        # If have a good amount of gold (currently at 2000 b/c always want to only
        # spend a portion of gold and dark barrels can only be purchased
        # at 750; ensuring gold amount is well over 1500), 
        # then roll a dice to determine whether or not to change mlTypeToBuy
        # to dark barrels
        if numGold >= 2000:
            # Random number from 1-100 (100 = exclusive in function)
            randInt = random.randint(0, 100)
            # 0-74 = don't change mlTypeToBuy
            # 75-100 = buy dark ml
            # => 25% chance of buying dark
            if randInt >= 75:
                mlTypeToBuy = "DARK"
        
        
        for barrel in wholesale_catalog:
            # Flooring/rounding down to stay safe with purchases
            # TODO: Find a good number to divide by for a more efficient
            #       way of deciding how much gold to spend. Currently
            #       spending half of what I currently have. This will get
            #       very inefficient with larger amounts of gold. Also when
            #       deciding what to make this value, good idea to change the
            #       current logic with the threshold in the if block before this
            #       else block.
            goldToSpend = numGold // 3
            if goldToSpend >= barrel.price and (mlTypeToBuy in barrel.sku):
                print("Buying extra ml from " + barrel.sku)

                amtToBuy = goldToSpend // barrel.price
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
    print("My attempted Purchase Plan: " + str(purchasePlan))
    return purchasePlan

