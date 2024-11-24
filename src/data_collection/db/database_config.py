from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client['research_db']
    return db