ITEM_TYPE_CHOICES = [
    ("pizza", "Pizza"),
    ("drink", "Drink"),
    ("salad", "Salad"),
    ("sides", "Sides"),
    ("other", "Other"),
]


# Sub-type choices for pizza only
PIZZA_SUB_TYPE_CHOICES = [
    ("veggie", "Vegetarian"),
    ("meat", "Meat"),
    ("cheese", "Cheese"),
]

INGREDIENT_TYPE_CHOICES = [
    ("dough", "Dough"),
    ("sauce", "Sauce"),
    ("cheese", "Cheese"),
    ("topping", "Topping"),
    ("extra", "Extra"),
]

# Sub-type choices for each ingredient type (only topping has sub-types)
INGREDIENT_SUB_TYPE_CHOICES_BY_TYPE = {
    "topping": [
        ("veggie", "Vegetarian"),
        ("meat", "Meat"),
        ("cheese", "Cheese"),
    ],
    # Other types (dough, sauce, cheese, extra) don't have sub-types
}