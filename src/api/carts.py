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

    with db.engine.begin() as connection:
        # Create a new cart for the customer by inserting them into the carts table
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:customer) RETURNING cart_id"), 
                                    [{"customer": str(new_cart)}])
        # Get the current id that was generated for the current customer
        id = result.fetchone()[0]

        return {"cart_id": id} 


class CartItem(BaseModel):
    quantity: int

# db layout:
#   when implementing cart items: 
#   when set item quantity is called, insert a row into the cart_items table
#   you get passed a cart id and an item sku, so you have to figure out what the right
#   potion id is to insert
#   - store price in potions table
#   - sample SQL commands recommended for set item quantity in lec. notes
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """


    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            """
            INSERT INTO cart_items (cart_id, quantity, potion_id) 
            SELECT :cart_id, :quantity, potions.id 
            FROM potions WHERE potions.sku = :item_sku
            """
            ), [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])

        # Raise error if requested sku doesn't exist in potions table
        if result.rowcount == 0:
            return Response(content=f"No potion found with SKU {item_sku}", status_code=400)



    # Check if you have that item_sku 
    #if item_sku == "RED_POTION_0":
    #    potionToSell = "num_red_potions"
    #elif item_sku == "GREEN_POTION_0":
    #    potionToSell = "num_green_potions"
    #elif item_sku == "BLUE_POTION_0":
    #    potionToSell = "num_blue_potions"
    #else:
    #    return Response(content="Invalid item_sku. Returned from set_item_quantity PK", status_code=400)

    ## NOTE: this sets the desired potion of the customer from "" to 'potionToSell'
    #carts[cart_id][1] = potionToSell
    ## Store the amount the customer wants to buy
    #carts[cart_id][2] = cart_item.quantity

    return "OK"



class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    with db.engine.begin() as connection:
        # Check how much is in stock of current potions before selling
        numInStock = connection.execute(sqlalchemy.text(
            """
            SELECT quantity
            FROM potions 
            WHERE potions.id IN (
                SELECT potion_id
                FROM cart_items
                WHERE potions.id = cart_items.potion_id and cart_items.cart_id = :cart_id
            )  
            """
            ), [{"cart_id": cart_id}]).fetchone()[0]

        # Check how much of potion has been requested
        quantityRequested = connection.execute(sqlalchemy.text(
            """
            SELECT quantity
            FROM cart_items 
            WHERE cart_items.cart_id = :cart_id 
            """
            ), [{"cart_id": cart_id}]).fetchone()[0]

        # print("req: " +  str(quantityRequested))
        #print(numInStock)

        if quantityRequested > numInStock:
            print(f"Update failed quantity requested exceeds stock. Cart id that failed is: {cart_id}")
            return Response(content=f"Update failed quantity requested exceeds stock. Cart id that failed is: {cart_id}", status_code=400)

        updatePotionresult = connection.execute(sqlalchemy.text(
            """
            UPDATE potions 
            SET quantity = potions.quantity - cart_items.quantity
            FROM cart_items
            WHERE potions.id = cart_items.potion_id and cart_items.cart_id = :cart_id;
            """
            ), [{"cart_id": cart_id}])

        # Raise error if update didn't work
        if updatePotionresult.rowcount == 0:
            print(f"Potion update failed for cart id: {cart_id}")
            return Response(content=f"Potion update failed for cart id: {cart_id}", status_code=400)

        updateGoldResult = connection.execute(sqlalchemy.text(
            """
            UPDATE global_inventory
            SET gold = global_inventory.gold + cart_items.quantity * potions.price
            FROM cart_items
            JOIN potions ON potions.id = cart_items.potion_id
            WHERE cart_items.cart_id = :cart_id;
            """
            ), [{"cart_id": cart_id}])

        # Raise error if update didn't work
        if updateGoldResult.rowcount == 0:
            print(f"Gold update failed for cart id: {cart_id}")
            return Response(content=f"Gold update failed for cart id: {cart_id}", status_code=400)

        potionPrice = connection.execute(sqlalchemy.text(
            """
            SELECT price
            FROM potions
            WHERE potions.id IN (
                SELECT potion_id
                FROM cart_items
                WHERE potions.id = cart_items.potion_id and cart_items.cart_id = :cart_id
            )  
            """
        ), [{"cart_id": cart_id}]).fetchone()[0]

        #print("potion price: " + str(potionPrice))

    # Get the potion type to update in the table
    #potionColumnToUpdate = carts[cart_id][1]
    #print("potionColumnToUpdate: " + potionColumnToUpdate)
    ## Get num potions bought
    #numPotionsBought = carts[cart_id][2]
    #print("numPotionsBought: " + str(numPotionsBought))
    #print("PAYMENT VALUE IS: " + cart_checkout.payment)
    ## Get the amount of gold the customer paid (as an int)
    ## NOTE: don't worry about payment atm, uncomment when needed to be dynamic later
    ##goldPaid = int(cart_checkout.payment)
    ##print("goldPaid: " + str(goldPaid))

    #with db.engine.begin() as connection:
    #    # Update table to reflect purchase
    #    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {potionColumnToUpdate} = {potionColumnToUpdate} - {numPotionsBought}, gold = gold + {40} WHERE id = {1}"))
    
    #print("Returning from cart/checkout function normally, error response not triggered")
    return {"total_potions_bought": quantityRequested, "total_gold_paid": (quantityRequested * potionPrice)}
