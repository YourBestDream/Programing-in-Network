EUR_TO_MDL = 19.6
MDL_TO_EUR = 1 / EUR_TO_MDL

def convert_to_eur_or_mdl(product):
    if product.currency == "lei":
        product.price = product.price * MDL_TO_EUR  # Convert MDL to EUR
        product.currency = "eur"
    elif product.currency == "eur":
        product.price = product.price * EUR_TO_MDL  # Convert EUR to MDL
        product.currency = "lei"
    return product

def filter_price_range(product):
    if product.currency == "eur" and 100 <= product.price <= 500:
        return True
    return False