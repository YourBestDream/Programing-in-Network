from zoneinfo import ZoneInfo
from datetime import datetime
from bs4 import BeautifulSoup, Tag, ResultSet
import pydantic
from models import Product
from utils import get_http_response_body, convert_to_eur_or_mdl, filter_price_range
from functools import reduce
import pika
import json
from ftplib import FTP

# URL to scrape
url = "https://maximum.md/ro/tehnica-computerizata/laptopuri-si-computere/laptopuri/"
response = get_http_response_body(url=url)

scraped_data = []
soup = BeautifulSoup(response, "html.parser")

products_list_container = soup.find("div", class_="products-list-container")
if products_list_container is None or not isinstance(products_list_container, Tag):
    raise ValueError("No products found")

items = products_list_container.find_all("div", class_="wrap_search_page")
if not items or not isinstance(items, ResultSet):
    raise ValueError('No divs with class "wrap_search_page" found')

for item in items:
    name_tag = item.find("div", class_="product__item__title")
    if name_tag is None or not isinstance(name_tag, Tag):
        continue
    name = name_tag.text.strip()

    price_tag = item.find("div", class_="product__item__price-current")
    if price_tag is None or not isinstance(price_tag, Tag):
        continue

    # Extract price and currency
    price_num = price_tag.find("span").text.strip()
    currency = price_tag.find("span", class_="product__item__price__currency").text.strip()

    try:
        product = Product(
            product_name=name,
            price=float(price_num),
            currency=currency,
            scrape_time_utc=datetime.now().astimezone(ZoneInfo("UTC")),
        )
        scraped_data.append(product)
    except pydantic.ValidationError as exc:
        print(f"Validation error: {exc}")

# Convert and filter
converted_products = list(map(convert_to_eur_or_mdl, scraped_data))
filtered_products = list(filter(filter_price_range, converted_products))
total_price = reduce(lambda acc, prod: acc + prod.price, filtered_products, 0)
result = {
    "filtered_products": [p.dict() for p in filtered_products],
    "total_price": total_price,
    "timestamp_utc": datetime.now().astimezone(ZoneInfo("UTC")).isoformat()
}

print("Scraped and filtered data:", result)

# Publish to RabbitMQ
try:
    credentials = pika.PlainCredentials('user', 'pass')  # Adjust if needed
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue='scraped_data')
    channel.basic_publish(exchange='', routing_key='scraped_data', body=str(result))
    connection.close()
    print("Published scraped data to RabbitMQ")
except Exception as e:
    print("Could not publish to RabbitMQ, run locally or inside Docker after adjusting host:", e)

# Custom JSON serializer for datetime
def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to ISO format string
    raise TypeError(f"Type {type(obj)} not serializable")

# Write to data.json
json_filename = 'data.json'
try:
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4, default=custom_json_serializer)
    print(f"Data written to {json_filename}")
except Exception as e:
    print(f"Error writing {json_filename}:", e)

# Upload data.json to FTP server
ftp_host = 'localhost'   # if running in docker compose network; otherwise 'localhost'
ftp_user = 'user'
ftp_pass = 'pass'

try:
    ftp = FTP()
    ftp.set_debuglevel(2)  # Enables verbose FTP debugging
    ftp.connect('localhost', 21)
    ftp.login(ftp_user, ftp_pass)
    ftp.set_pasv(True)
    with open(json_filename, 'rb') as f:
        ftp.storbinary(f'STOR {json_filename}', f)
    ftp.quit()
    print(f"Uploaded {json_filename} to FTP server.")
except Exception as e:
    print("Error uploading to FTP:", e)
