from db_config import get_connection

def insert_extra_clothing():
    conn = get_connection()
    cur = conn.cursor()
    try:
        total = 52
        for i in range(1, total + 1):
            if i <= 26:
                name = f"Men Clothing Product {i}"
                desc = f"Stylish men clothing item {i}."
            else:
                j = i - 26
                name = f"Women Clothing Product {j}"
                desc = f"Trendy women clothing item {j}."

            price = 500 + (i * 25) % 1500
            stock = 20 + (i * 3) % 50

            cur.execute(
                """
                INSERT INTO products (category_id, name, description, price, stock_quantity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (2, name, desc, price, stock)
            )

        conn.commit()
        print("Inserted 52 extra clothing products successfully!")
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_extra_clothing()
