from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy import create_engine, Table, MetaData
from src import database as db
from datetime import datetime
import os

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

    db_uri = os.getenv('POSTGRES_URI')
    engine = create_engine(db_uri)
    metadata = MetaData()

    carts = Table('carts', metadata, autoload_with=engine)
    cart_items = Table('cart_items', metadata, autoload_with=engine)
    potions = Table('potions', metadata, autoload_with=engine)

    #for col in cart_items.c:
    #    print(f"name: {col.name} type: {col.type}")

    # Number of results per page
    results_per_page = 5

    # Calculate offset based on page number
    offset = (int(search_page) - 1) * results_per_page if search_page else 0

    # Determine the column to sort by
    if sort_col is search_sort_options.customer_name:
        order_by = carts.c.customer
    elif sort_col is search_sort_options.item_sku:
        order_by = potions.c.sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = potions.c.price
    elif sort_col is search_sort_options.timestamp:
        order_by = cart_items.c.timestamp
    else:  
        assert False

    # Determine the sort order
    if sort_order is search_sort_order.asc:
        order_by = sqlalchemy.asc(order_by)
    else:  # default is desc
        order_by = sqlalchemy.desc(order_by)

    # Construct the query
    stmt = (
        sqlalchemy.select(
            cart_items.c.item_id,
            potions.c.sku,
            carts.c.customer,
            # Multiply quantity they bought by price of potion to get total spent
            (cart_items.c.quantity * potions.c.price).label('line_item_total'),
            cart_items.c.timestamp,
        )
        .select_from(
            cart_items.join(carts, cart_items.c.cart_id == carts.c.cart_id)
                .join(potions, cart_items.c.potion_id == potions.c.id)
        )
        .limit(results_per_page)  # max results is 5
        .offset(offset)  # Skip rows for pagination
        .order_by(order_by, cart_items.c.item_id)
    )

    # Apply filters if parameters are passed
    if customer_name != "":
        stmt = stmt.where(carts.c.customer.ilike(f"%{customer_name}%"))
    if potion_sku != "":
        stmt = stmt.where(potions.c.sku.ilike(f"%{potion_sku}%"))

    # Execute the query
    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        json = []
        for row in result:
            json.append(
                {
                    "line_item_id": row.item_id,
                    "item_sku": row.sku,
                    "customer_name": row.customer,
                    "line_item_total": row.line_item_total,
                    "timestamp": row.timestamp,
                }
            )

    # Return the results
    return {
        "previous": str(int(search_page) - 1) if int(search_page) > 1 else "",
        "next": str(int(search_page) + 1) if json else "",
        "results": json,
    }
    
    
    #return {
    #    "previous": "",
    #    "next": "",
    #    "results": [
    #        {
    #            "line_item_id": 1,
    #            "item_sku": "1 oblivion potion",
    #            "customer_name": "Scaramouche",
    #            "line_item_total": 50,
    #            "timestamp": "2021-01-01T00:00:00Z",
    #        }
    #    ],
    #}


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
                                    [{"customer": new_cart.customer_name}])
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
            INSERT INTO cart_items (cart_id, quantity, potion_id, timestamp) 
            SELECT :cart_id, :quantity, potions.id, :timestamp 
            FROM potions WHERE potions.sku = :item_sku
            """
            ), [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku, "timestamp": datetime.utcnow().isoformat()}])

        # Raise error if requested sku doesn't exist in potions table
        if result.rowcount == 0:
            return Response(content=f"No potion found with SKU {item_sku}", status_code=400)

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

        # Update potions
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

        # present_time table
        current_time = str(connection.execute(sqlalchemy.text("SELECT time from present_time WHERE id = 1")).fetchone()[0])

        # Get potion_id
        potion_id = connection.execute(sqlalchemy.text(
            """
            SELECT potion_id
            FROM cart_items 
            WHERE cart_items.cart_id = :cart_id 
            """
            ), [{"cart_id": cart_id}]).fetchone()[0]

        # Insert into potion_ledger
        connection.execute(sqlalchemy.text(
                """
                INSERT INTO potion_ledger (potion_id, cart_id, quantity, description, changed_at)
                VALUES
                (:potion_id, :cart_id, :quantity, :description, :changed_at)
                """
            ), [{"potion_id": potion_id, "cart_id": cart_id, "quantity": -quantityRequested,
                "description": "Selling potion(s)", "changed_at": current_time}])

        # Get the potion's price
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

        total_gold_paid = quantityRequested * potionPrice

        # Insert change in gold into global_inventory
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO global_inventory (gold, cart_id, description, changed_at)
            VALUES
            (:gold, :cart_id, :description, :changed_at)
            """
            ), [{"gold": total_gold_paid, "cart_id": cart_id, "description": "Selling potion(s)",
                "changed_at": current_time}])


        #updateGoldResult = connection.execute(sqlalchemy.text(
        #    """
        #    UPDATE global_inventory
        #    SET gold = global_inventory.gold + cart_items.quantity * potions.price
        #    FROM cart_items
        #    JOIN potions ON potions.id = cart_items.potion_id
        #    WHERE cart_items.cart_id = :cart_id;
        #    """
        #    ), [{"cart_id": cart_id}])

        # Raise error if update didn't work
        #if updateGoldResult.rowcount == 0:
        #    print(f"Gold update failed for cart id: {cart_id}")
        #    return Response(content=f"Gold update failed for cart id: {cart_id}", status_code=400)

        
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
    return {"total_potions_bought": quantityRequested, "total_gold_paid": total_gold_paid}
