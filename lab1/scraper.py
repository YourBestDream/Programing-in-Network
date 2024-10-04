import requests
from bs4 import BeautifulSoup, Tag, ResultSet

url = "https://darwin.md/gadgets"

response = requests.get(url)

try:
    response.raise_for_status()
    # with open("html.html","w") as file:
    #     file.write(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    
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
        
        specifications_tag = item.find("span", class_ = "specification")
        if specifications_tag:
            continue
        else:
            specifications = specifications_tag.text.strip().replace(",","|").split("|")

        print(f"Name: {name},\nPrice: {price},\nSpecifications: {specifications}\n")

except requests.exceptions.HTTPError as exc:
    print(f"Something went wrong: {exc}")
    