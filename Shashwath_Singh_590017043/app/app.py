from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "super_secret_key_buyhaven_123"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1954",
        database="ecommerce_db"
    )

PRODUCT_IMAGE_KEYWORDS = {
    "Nivea Men Face Wash": "nivea men face wash",
    "MamaEarth Aloe Vera Gel": "mamaearth aloe vera gel",
    "Dove Intense Repair Shampoo": "dove intense repair shampoo",
    "Himalaya Neem Face Wash": "himalaya neem face wash",
    "Vaseline Body Lotion": "vaseline body lotion",
    "Parachute Coconut Oil": "parachute coconut oil",
    "Gillette Shaving Foam": "gillette shaving foam",
    "Colgate Total Toothpaste": "colgate toothpaste",
    "Sensodyne Sensitive Toothpaste": "sensodyne toothpaste",
    "Biotique Hair Oil": "biotique hair oil",
    "Clinic Plus Shampoo": "clinic plus shampoo",
    "Pantene Silky Smooth Care": "pantene silky smooth shampoo",
    "Pears Pure Gentle Soap": "pears gentle soap",
    "Fiama Shower Gel": "fiama shower gel",
    "Garnier Men AcnoFight FaceWash": "garnier men facewash",
    "Sunsilk Black Shine Shampoo": "sunsilk shampoo",
}

def get_logged_in_user():
    user_id = session.get("user_id")
    name = session.get("user_name")
    email = session.get("user_email")
    if (not name or str(name).strip() == "" or name is None) and email:
        name = email.split("@")[0]
    if not name:
        name = "Guest"
    return {"id": user_id, "name": name}

@app.route("/")
def home():
    search = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT category_id, name FROM categories ORDER BY category_id")
    categories = cursor.fetchall()

    query = """
        SELECT p.product_id, p.category_id, p.name, p.price, p.image_url,
               c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
    """

    params = []
    conditions = []

    if search:
        conditions.append("p.name LIKE %s")
        params.append(f"%{search}%")

    if category_id:
        conditions.append("p.category_id = %s")
        params.append(category_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY p.product_id"
    cursor.execute(query, params)
    products = cursor.fetchall()

    for p in products:
        keyword = PRODUCT_IMAGE_KEYWORDS.get(p["name"], p["category_name"] + " product")
        p["final_image"] = p["image_url"] or f"https://source.unsplash.com/featured/600x400/?{keyword}"

    cursor.close()
    conn.close()

    user = get_logged_in_user()
    cart = session.get("cart", {})

    return render_template("products.html",
                           products=products,
                           categories=categories,
                           selected_category=category_id,
                           search=search,
                           user=user,
                           cart_count=sum(cart.values()))

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    flash("Item added to cart!")
    return redirect(url_for("home"))

@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    user = get_logged_in_user()

    if not cart:
        return render_template("cart.html",
                               items=[],
                               total=0,
                               user=user,
                               cart_count=0)

    ids = list(cart.keys())
    placeholders = ",".join(["%s"] * len(ids))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        f"SELECT product_id, name, price, image_url FROM products WHERE product_id IN ({placeholders})",
        ids
    )
    items = cursor.fetchall()

    total = Decimal("0.00")
    for item in items:
        pid = str(item["product_id"])
        qty = cart.get(pid, 0)
        item["qty"] = qty
        item["subtotal"] = item["price"] * qty
        item["final_image"] = item["image_url"] or "https://source.unsplash.com/featured/400x300/?shopping"
        total += item["subtotal"]

    cursor.close()
    conn.close()

    return render_template("cart.html",
                           items=items,
                           total=total,
                           user=user,
                           cart_count=sum(cart.values()))

@app.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    action = request.form.get("action")
    cart = session.get("cart", {})
    pid = str(product_id)

    if pid not in cart:
        return redirect(url_for("view_cart"))

    if action == "inc":
        cart[pid] += 1
    elif action == "dec":
        if cart[pid] > 1:
            cart[pid] -= 1
        else:
            cart.pop(pid, None)
    elif action == "remove":
        cart.pop(pid, None)

    session["cart"] = cart
    return redirect(url_for("view_cart"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name") or ""
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM customers WHERE email=%s", (email,))
        existing = cursor.fetchone()

        if existing:
            flash("Email already registered. Please login.")
            return redirect(url_for("login"))

        hashed = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO customers(full_name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, hashed)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password!")
            return redirect(url_for("login"))

        session["user_id"] = user["customer_id"]
        session["user_email"] = user["email"]

        display_name = user["full_name"]
        if not display_name:
            display_name = user["email"].split("@")[0]

        session["user_name"] = display_name

        flash("Login successful!")
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
