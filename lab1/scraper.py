from bs4 import BeautifulSoup, Tag, ResultSet
import re
from zoneinfo import ZoneInfo 
from models import Product
from datetime import datetime
import pydantic
from utils import convert_to_eur_or_mdl, filter_price_range,get_http_response_body
from functools import reduce

url = "https://darwin.md/gadgets"

response = get_http_response_body


scraped_data = []

soup = BeautifulSoup(response, "html.parser")

item_products = soup.find("div", class_ = "item-products")
if item_products is None or not isinstance(item_products, Tag):
    raise ValueError("Required div with class 'item-products' hasn't been found")

items = item_products.find_all("figure")
if not items or not isinstance(items, ResultSet):
    raise ValueError("Required figure tags hasn't been found within div")

for item in items:
    name_tag = item.find("a", class_ = "d-block")
    if name_tag is None or not isinstance(name_tag, Tag):
        continue
    else:
        name = name_tag.text.strip()
    
    price_tag = item.find("span", class_ = "price-new")
    if price_tag is None or not isinstance(price_tag, Tag):
        continue
    else:
        price = price_tag.text.strip()
    
    match = re.findall(r"(\d{1,3}(?:[ ,]\d{3})*|\d+(?:\.\d{2})?)\s*(\w+)", price)
    
    price_num = match[0][0].replace(" ", "").replace(",", "")  # Access price from the tuple
    currency = match[0][1]  # Access currency from the tuple
        
    specifications_tag = item.find("span", class_ = "specification")
    if specifications_tag is None or not isinstance(specifications_tag, Tag):
        continue
    else:
        specifications = specifications_tag.text.strip().replace(",","|").split("|")
    
    try:
        product = Product(
            product_name = name,
            price = int(price_num),
            currency = currency,
            specifications = specifications,
            scrape_time_utc = datetime.now().astimezone(ZoneInfo("UTC")),
        )
        
        scraped_data.append(product)
    except pydantic.ValidationError as exc:
        raise pydantic.ValidationError(f"Validation error:{exc}")

converted_products = list(map(convert_to_eur_or_mdl, scraped_data))
    
filtered_products = list(filter(filter_price_range, converted_products))

total_price = reduce(lambda acc, prod: acc + prod.price, filtered_products, 0)

result = {
    "filtered_products": filtered_products,
    "total_price": total_price,
    "timestamp_utc": datetime.now().astimezone(ZoneInfo("UTC"))
}
