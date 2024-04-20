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
            result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
            globalRows = result.fetchone()

            gold = globalRows[1]
            totalML = globalRows[2] + globalRows[3] + globalRows[4] + globalRows[5]

            # potions
            result2 = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potions"))
            potionsRow = result2.fetchone()
            
            totalPotions = potionsRow[0]

    return {"number_of_potions": totalPotions, "ml_in_barrels": totalML, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

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

    return "OK"
