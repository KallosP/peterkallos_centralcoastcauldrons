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

    potion_cap_to_buy = 0
    ml_cap_to_buy = 0
    with db.engine.begin() as connection:
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

        ml_cap = (connection.execute(sqlalchemy.text("SELECT SUM(ml_cap) FROM capacity")).fetchone()[0]) * 10000
        potion_cap = (connection.execute(sqlalchemy.text("SELECT SUM(potion_cap) FROM capacity")).fetchone()[0]) * 50

        # 2000 ml buffer zone for buying capacity
        if total_ml >= (ml_cap - 2000) and gold >= 2000:
           ml_cap_to_buy = 1 

        # 10 below capacity buffer zone for buying potion capacity
        if totalPotions >= (potion_cap - 10) and gold >= 2000:
            potion_cap_to_buy = 1
             

    return {
        "potion_capacity": potion_cap_to_buy,
        "ml_capacity": ml_cap_to_buy
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

    with db.engine.begin() as connection:
        if capacity_purchase.ml_capacity > 0:
            # Update ml capacity table
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO capacity (ml_cap)
                VALUES 
                (:ml_cap)
                """), 
                [{"ml_cap": capacity_purchase.ml_capacity}])
            # Update gold table
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO global_inventory (gold, description)
                VALUES 
                (:gold, :description)
                """), 
                [{"gold": -((capacity_purchase.ml_capacity) * 1000),
                "description": "Bought ML Capacity"}])


        if capacity_purchase.potion_capacity > 0:
            # Update potion capacity table
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO capacity (potion_cap)
                VALUES 
                (:potion_cap)
                """), 
                [{"potion_cap": capacity_purchase.potion_capacity}])
            # Update gold
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO global_inventory (gold, description)
                VALUES 
                (:gold, :description)
                """), 
                [{"gold": -((capacity_purchase.potion_capacity) * 1000),
                "description": "Bought Potion Capacity"}])

    return "OK"
