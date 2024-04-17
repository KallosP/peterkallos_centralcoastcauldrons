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
        # Reset all table values
        # global_inventory
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {100}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {0}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {0}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {0}"))

        # potions
        # Sets quantity column's values to 0
        connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity = {0}"))

    return "OK"

