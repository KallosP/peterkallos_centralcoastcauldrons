from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
            # global_inventory
            gold = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM global_inventory")).fetchone()[0]

            total_red_ml = connection.execute(sqlalchemy.text("SELECT SUM(num_red_ml) FROM global_inventory")).fetchone()[0]
            total_green_ml = connection.execute(sqlalchemy.text("SELECT SUM(num_green_ml) FROM global_inventory")).fetchone()[0]
            total_blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(num_blue_ml) FROM global_inventory")).fetchone()[0]
            total_dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(num_dark_ml) FROM global_inventory")).fetchone()[0]

            total_ml = total_red_ml + total_green_ml + total_blue_ml + total_dark_ml

            # potions
            totalPotions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_ledger")).fetchone()[0]
            # Accounts for edge case in which no data in ledger table
            if totalPotions == None:
                totalPotions = 0
            
    return {"number_of_potions": totalPotions, "ml_in_barrels": total_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    # TODO: 
    # - Make capacity table
    # - logic for buying larger capacities
    # - 

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    # TODO: store capacities somewhere (in a table?) to reference in other parts of code
    #       -subtract 1000 gold from inventory if successful

    return "OK"
