from pydantic import BaseModel
from datetime import datetime

class Product(BaseModel):
    product_name:str
    price:int
    currency: str
    specifications:list | None=None
    scrape_time_utc:datetime