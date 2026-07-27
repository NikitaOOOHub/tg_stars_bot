def calculate_stars_price(quantity: int) -> float:
    if quantity <= 300:
        return round(quantity * 1.30, 2)
    elif quantity <= 500:
        return round(quantity * 1.25, 2)
    else:
        return round(quantity * 1.22, 2)