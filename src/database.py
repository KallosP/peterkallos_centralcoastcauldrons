import os
import dotenv
from sqlalchemy import create_engine

# Establishes a connection to the database setup in Supabase
def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)