from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
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

        for barrel in barrels_delivered:
            # TODO: (CHANGE LATER for future versions) filter out all other barrels
            # Red
            if barrel.sku == "MINI_RED_BARREL" or barrel.sku == "SMALL_RED_BARREL" or barrel.sku == "LARGE_RED_BARREL":
                # Note multiplying by barrel.quantity in case I buy more than a single barrel
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {barrel.ml_per_barrel * barrel.quantity}, gold = gold - {barrel.price * barrel.quantity} WHERE id = {1}"))

            # Green
            if barrel.sku == "MINI_GREEN_BARREL" or barrel.sku == "SMALL_GREEN_BARREL" or barrel.sku == "LARGE_GREEN_BARREL":
                # Note multiplying by barrel.quantity in case I buy more than a single barrel
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {barrel.ml_per_barrel * barrel.quantity}, gold = gold - {barrel.price * barrel.quantity} WHERE id = {1}"))

            # Blue
            if barrel.sku == "MINI_BLUE_BARREL" or barrel.sku == "SMALL_BLUE_BARREL" or barrel.sku == "LARGE_BLUE_BARREL":
                # Note multiplying by barrel.quantity in case I buy more than a single barrel
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {barrel.ml_per_barrel * barrel.quantity}, gold = gold - {barrel.price * barrel.quantity} WHERE id = {1}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
# wholesale_catalog = the parameter
# : = a type hint (which is optional syntax) that indicates the expected type of a variable, in this case list[Barrel]
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    purchasPlan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fetchall: fetches all (or all remaining) rows of a query result set and returns a list of tuples
        rows = result.fetchall()
        # Store the row corresponding to the green potion 
        potionRow = rows[0]
        numGold = potionRow[3]
        # Red
        numRedPotions = potionRow[4]
        # Green
        numGreenPotions = potionRow[1]
        # Blue
        numBluePotions = potionRow[6]

        print("Gold from purchase plan: " + str(numGold))
        print("Green from purchase plan: " + str(numGreenPotions))
        print("Red from purchase plan: " + str(numRedPotions))
        print("Blue from purchase plan: " + str(numBluePotions))

        # Priorities:
        #   1) Always be in stock


        # NOTE: !! Currently ONLY focusing on buying mini barrels !!

        # 60 = cheapest possible barrel you can buy, if you have less, just return nothing
        if numGold < 60:
            return []

        for barrel in wholesale_catalog:
            # NOTE: Change this logic in the future to be more efficient,
            #       intentionally blocking the purchase of barrels if i have all potion types (r,g,b) in inventory.
            #       Basically, I'm always purchasing barrels when I don't have potions of a certain type, otherwise,don't purchase.
            # Always prioritizes purchasing a barrel for the potions I don't have in stock
            # NOTE: can't rely on your code ordering to prioritize certain barrel types, 
            #       the wholesale_catalog is always ordered randomly
            if numRedPotions <= 0 and barrel.sku == "MINI_RED_BARREL" and numGold >= barrel.price:
                print("Entered red")
                numGold = numGold - barrel.price
                purchasPlan.append(
                    {
                        "sku": "MINI_RED_BARREL",
                        "quantity": 1
                    }
                )
            if numGreenPotions <= 0 and barrel.sku == "MINI_GREEN_BARREL" and numGold >= barrel.price:
                print("Entered green")
                numGold = numGold - barrel.price
                purchasPlan.append(
                    {
                        "sku": "MINI_GREEN_BARREL",
                        "quantity": 1
                    }
                )
            if numBluePotions <= 0 and barrel.sku == "MINI_BLUE_BARREL" and numGold >= barrel.price:
                numGold = numGold - barrel.price
                print("Entered blue")
                purchasPlan.append(
                    {
                        "sku": "MINI_BLUE_BARREL",
                        "quantity": 1
                    }
                )

    # Don't make a purchase
    return purchasPlan

