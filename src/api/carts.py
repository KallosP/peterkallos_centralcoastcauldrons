from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
import uuid

# dictionary for carts: key = random id, value = list[Customer, desiredPotion, quantity] 
carts = {}

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """

    unique_ID = int(uuid.uuid4())

    carts[unique_ID] = [new_cart, "", 0]

    print("Current carts: " + str(carts))

    return {"cart_id": unique_ID}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    # Check if you have that item_sku 
    if item_sku == "RED_POTION_0":
        potionToSell = "num_red_potions"
    elif item_sku == "GREEN_POTION_0":
        potionToSell = "num_green_potions"
    elif item_sku == "BLUE_POTION_0":
        potionToSell = "num_blue_potions"
    else:
        return Response(content="Invalid item_sku. Returned from set_item_quantity PK", status_code=400)

    # NOTE: this sets the desired potion of the customer from "" to 'potionToSell'
    carts[cart_id][1] = potionToSell
    # Store the amount the customer wants to buy
    carts[cart_id][2] = cart_item.quantity

    return "OK"



class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # Get the potion type to update in the table
    potionColumnToUpdate = carts[cart_id][1]
    print("potionColumnToUpdate: " + potionColumnToUpdate)
    # Get num potions bought
    numPotionsBought = carts[cart_id][2]
    print("numPotionsBought: " + str(numPotionsBought))
    print("FIXME, PAYMENT VALUE IS: " + cart_checkout.payment)
    # Get the amount of gold the customer paid (as an int)
    goldPaid = int(cart_checkout.payment)
    print("goldPaid: " + str(goldPaid))

    with db.engine.begin() as connection:
        # Update table to reflect purchase
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {potionColumnToUpdate} = {potionColumnToUpdate} - {numPotionsBought}, gold = gold + {goldPaid} WHERE id = {1}"))
    
    print("Returning from cart/checkout function normally, error response not triggered")
    return {"total_potions_bought": numPotionsBought, "total_gold_paid": goldPaid}
