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

    for barrel in barrels_delivered:
        # TODO: (CHANGE LATER for future versions) filter out all other barrels
        if barrel.sku == "SMALL_GREEN_BARREL":
            with db.engine.begin() as connection:
                # Note multiplying by barrel.quantity in case I buy more than a single barrel
                result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {barrel.ml_per_barrel * barrel.quantity}, gold = gold - {barrel.price * barrel.quantity} WHERE id = {1}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
# wholesale_catalog = the parameter
# : = a type hint (which is optional syntax) that indicates the expected type of a variable, in this case list[Barrel]
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    # if num potions in inventory is less than 10, purchase small green barrel
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fetchall: fetches all (or all remaining) rows of a query result set and returns a list of tuples
        rows = result.fetchall()
        # Store the row corresponding to the green potion 
        greenPotionRow = rows[0]
        numGreenPotions = greenPotionRow[1]
        print(numGreenPotions)
        if numGreenPotions < 10:
            return [
                {
                    #FIXME: correct name of sku?
                    "sku": "SMALL_GREEN_BARREL",
                    # FIXME: how many to buy?
                    "quantity": 1
                }
            ]

    return [
            {
                "sku": "",
                "quantity": 0
            }
        ]

