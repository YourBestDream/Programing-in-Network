import requests
from bs4 import BeautifulSoup

url = "https://darwin.md/gadgets"

response = requests.get(url)

try:
    response.raise_for_status()
    # with open("html.html","w") as file:
    #     file.write(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    
    items = soup.find("div", class_ = "item-products")
    for item in items:
        print("============")
        print(item)
except requests.exceptions.HTTPError as exc:
    print(f"Something went wrong: {exc}")
    