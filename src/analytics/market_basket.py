from collections import Counter
from itertools import combinations
from src.core.db import db_cursor 

def run_market_basket_analysis():
    with db_cursor(dictionary=True) as cur:
        cur.execute("SELECT OrderID, DishName FROM vw_MarketBasketData")
        data = cur.fetchall()

    if not data:
        return []

    orders = {}
    for row in data:
        oid = row['OrderID']
        dish = row['DishName']
        if oid not in orders:
            orders[oid] = []
        orders[oid].append(dish)

    pair_counter = Counter()
    for items in orders.values():
        for pair in combinations(sorted(items), 2):
            pair_counter[pair] += 1

    top_pairs = pair_counter.most_common(5)
    
    result_data = []
    for pair, count in top_pairs:
        result_data.append({
            "item_1": pair[0],
            "item_2": pair[1],
            "times_ordered_together": count
        })
        
    return result_data