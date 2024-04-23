from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:

        current_time = str(connection.execute(sqlalchemy.text("SELECT time from present_time WHERE id = 1")).fetchone()[0])

        # Reset global_inventory
        # Delete all rows
        connection.execute(sqlalchemy.text(f"DELETE FROM global_inventory_tmp"))
        # Insert initial amounts
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO global_inventory_tmp (gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, description, changed_at)
            VALUES
            (:gold, :red_ml, :green_ml, :blue_ml, :dark_ml, :description, :changed_at)
            """
            ), [{"red_ml": 0, "green_ml": 0,
                "blue_ml": 0, "dark_ml": 0,
                "gold": 100, "description": f"Reset Inventory",
                "changed_at": current_time}])

        # Reset potion_ledger
        connection.execute(sqlalchemy.text(f"DELETE FROM potion_ledger"))

        # Reset potions
        connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity = {0}"))

    return "OK"

