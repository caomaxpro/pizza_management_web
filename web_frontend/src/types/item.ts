// ...existing code...
export type ItemType =
    | "pizza"
    | "drink"
    | "salad"
    | "sides"
    | "topping"
    | "sauce"
    | "cheese"
    | "dough"
    | "extra"
    | string;

export interface Item {
    id: string;
    name: string;
    type: ItemType;
    subType?: string | null; // meat, veggie, cheese, ...
    price: number;
    description?: string;
    image?: string;

    // Topping-specific
    piece?: string | null;

    // Pizza-specific (nullable for non-pizza)
    dough?: Item | null;
    sauce?: Item | null;
    cheese?: Item | null;
    toppings?: Item[] | null;
    extras?: Item[] | null;

    qty?: number;
}
