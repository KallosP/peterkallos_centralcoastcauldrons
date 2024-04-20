from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

# Catalog tells the bots what they can/cannot buy

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    catalog = []

    # Open connection to DB 
    with db.engine.begin() as connection:
        # TODO: don't use *
        result = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM potions"))
        # fetchone: fetches next row of a query result set and returns single sequence (a tuple)
        # Rows is set to: "(#,)"
        rows = result.fetchone()
        # Selecting the first elmt in the tuple (representing the total number of rows currently in the table) 
        numRows = rows[0]

        # NOTE: Python for loops start at 0
        for i in range(numRows):
            # i+1 b/c table starts with IDs at 1
            # TODO: don't use *
            result = connection.execute(sqlalchemy.text(f"SELECT * FROM potions WHERE id = {i+1}"))
            # Current potion/row
            currPotion = result.fetchone()

            # Set attributes
            sku = currPotion[1]
            name = currPotion[2]
            quantity = currPotion[3]
            price = currPotion[4]
            potion_type = currPotion[5]

            # Put all potions that are in stock on the catalog
            if(quantity > 0):
                catalog.append(
                    {
                        "sku": sku,
                        "name": name,
                        "quantity": quantity,
                        "price": price,
                        "potion_type": potion_type
                    }
                )

    print("Catalog: " + str(catalog))
    # Can return empty json [], this means don't advertise anything since you have nothing
    return catalog
        
