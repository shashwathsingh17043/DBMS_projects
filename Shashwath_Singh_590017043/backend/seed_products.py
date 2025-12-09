from db_config import get_connection

categories = [
    "Electronics", "Clothing", "Books", "Home & Kitchen",
    "Sports", "Toys", "Beauty", "Grocery"
]

def seed_categories(cursor):
    for name in categories:
        cursor.execute(
            "INSERT IGNORE INTO categories (name) VALUES (%s)", (name,)
        )

def seed_products(cursor):
    cursor.execute("SELECT category_id FROM categories")
    category_ids = [row[0] for row in cursor.fetchall()]
    
    product_count = 0
    for i in range(1, 201):  # 200 products
        category_id = category_ids[i % len(category_ids)]
        name = f"Product {i}"
        description = f"This is a description for Product {i}."
        price = 100 + (i * 5) % 5000
        stock = 10 + (i * 3) % 100

        cursor.execute(
            """
            INSERT INTO products (category_id, name, description, price, stock_quantity)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (category_id, name, description, price, stock)
        )
        product_count += 1

    return product_count

if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    try:
        seed_categories(cursor)
        count = seed_products(cursor)
        conn.commit()
        print(f"Inserted {count} products successfully!")
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()
