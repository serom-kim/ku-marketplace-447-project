from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
import pymysql
import os
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "student_marketplace"),
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
}


def get_db():
    return pymysql.connect(**DB_CONFIG)


def query_db(sql, params=None, fetchone=False, commit=False):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            result = cur.fetchone() if fetchone else cur.fetchall()
        if commit:
            conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


def current_user():
    if "user_id" not in session:
        return None
    return query_db(
        "SELECT UserID, Name, Email, ContactInfo FROM Users WHERE UserID=%s",
        (session["user_id"],),
        fetchone=True
    )


@app.context_processor
def inject_globals():
    return {"current_user": current_user()}


@app.route("/")
def index():
    keyword = request.args.get("keyword", "").strip()
    category_id = request.args.get("category_id", "").strip()
    seller = request.args.get("seller", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    sql = """
        SELECT l.*, c.CategoryName, u.Name AS SellerName,
               (SELECT ImageURL FROM Listing_Images i WHERE i.ListingID = l.ListingID LIMIT 1) AS ImageURL
        FROM Listings l
        JOIN Categories c ON l.CategoryID = c.CategoryID
        JOIN Users u ON l.SellerID = u.UserID
        WHERE 1=1
    """
    params = []

    if keyword:
        sql += " AND (l.Title LIKE %s OR l.Description LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if category_id:
        sql += " AND l.CategoryID = %s"
        params.append(category_id)

    if seller:
        sql += " AND u.Name LIKE %s"
        params.append(f"%{seller}%")

    if min_price:
        sql += " AND l.Price >= %s"
        params.append(min_price)

    if max_price:
        sql += " AND l.Price <= %s"
        params.append(max_price)

    sql += " ORDER BY l.CreatedAt DESC"

    listings = query_db(sql, params)
    categories = query_db("SELECT * FROM Categories ORDER BY CategoryName")
    return render_template("index.html", listings=listings, categories=categories)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        contact = request.form["contact"].strip()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return redirect(url_for("register"))

        existing = query_db("SELECT UserID FROM Users WHERE Email=%s", (email,), fetchone=True)
        if existing:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        query_db(
            "INSERT INTO Users (Name, Email, PasswordHash, ContactInfo) VALUES (%s, %s, %s, %s)",
            (name, email, password_hash, contact),
            commit=True
        )
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = query_db("SELECT * FROM Users WHERE Email=%s", (email,), fetchone=True)
        if user and check_password_hash(user["PasswordHash"], password):
            session["user_id"] = user["UserID"]
            session["user_name"] = user["Name"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))


@app.route("/listing/new", methods=["GET", "POST"])
@login_required
def create_listing():
    categories = query_db("SELECT * FROM Categories ORDER BY CategoryName")

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        price = request.form["price"]
        condition = request.form["condition"].strip()
        category_id = request.form["category_id"]
        image_url = ""
        image_file = request.files.get("image_file")

        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            image_url = "/" + save_path

        if not title or not price or not category_id:
            flash("Title, price, and category are required.", "danger")
            return redirect(url_for("create_listing"))

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO Listings
                    (Title, Description, Price, ItemCondition, Status, SellerID, CategoryID)
                    VALUES (%s, %s, %s, %s, 'available', %s, %s)
                    """,
                    (title, description, price, condition, session["user_id"], category_id)
                )
                listing_id = cur.lastrowid

                if image_url:
                    cur.execute(
                        "INSERT INTO Listing_Images (ListingID, ImageURL) VALUES (%s, %s)",
                        (listing_id, image_url)
                    )
            conn.commit()
            flash("Listing created.", "success")
            return redirect(url_for("listing_detail", listing_id=listing_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error creating listing: {e}", "danger")
        finally:
            conn.close()

    return render_template("listing_form.html", categories=categories, listing=None)


@app.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = query_db(
        """
        SELECT l.*, c.CategoryName, u.Name AS SellerName, u.Email AS SellerEmail, u.ContactInfo,
               (SELECT ImageURL FROM Listing_Images i WHERE i.ListingID = l.ListingID LIMIT 1) AS ImageURL
        FROM Listings l
        JOIN Categories c ON l.CategoryID = c.CategoryID
        JOIN Users u ON l.SellerID = u.UserID
        WHERE l.ListingID=%s
        """,
        (listing_id,),
        fetchone=True
    )

    if not listing:
        flash("Listing not found.", "danger")
        return redirect(url_for("index"))

    saved = None
    if "user_id" in session:
        saved = query_db(
            "SELECT * FROM Saved WHERE UserID=%s AND ListingID=%s",
            (session["user_id"], listing_id),
            fetchone=True
        )

    return render_template("listing_detail.html", listing=listing, saved=saved)


@app.route("/listing/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):
    listing = query_db("SELECT * FROM Listings WHERE ListingID=%s", (listing_id,), fetchone=True)

    if not listing:
        flash("Listing not found.", "danger")
        return redirect(url_for("index"))

    if listing["SellerID"] != session["user_id"]:
        flash("Only the seller can edit this listing.", "danger")
        return redirect(url_for("listing_detail", listing_id=listing_id))

    categories = query_db("SELECT * FROM Categories ORDER BY CategoryName")
    image = query_db("SELECT ImageURL FROM Listing_Images WHERE ListingID=%s LIMIT 1", (listing_id,), fetchone=True)
    listing["ImageURL"] = image["ImageURL"] if image else ""

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        price = request.form["price"]
        condition = request.form["condition"].strip()
        category_id = request.form["category_id"]
        image_url = listing.get("ImageURL", "")
        image_file = request.files.get("image_file")

        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            image_url = "/" + save_path

        query_db(
            """
            UPDATE Listings
            SET Title=%s, Description=%s, Price=%s, ItemCondition=%s, CategoryID=%s
            WHERE ListingID=%s AND SellerID=%s
            """,
            (title, description, price, condition, category_id, listing_id, session["user_id"]),
            commit=True
        )

        query_db("DELETE FROM Listing_Images WHERE ListingID=%s", (listing_id,), commit=True)
        if image_url:
            query_db(
                "INSERT INTO Listing_Images (ListingID, ImageURL) VALUES (%s, %s)",
                (listing_id, image_url),
                commit=True
            )

        flash("Listing updated.", "success")
        return redirect(url_for("listing_detail", listing_id=listing_id))

    return render_template("listing_form.html", categories=categories, listing=listing)


@app.route("/listing/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    listing = query_db("SELECT * FROM Listings WHERE ListingID=%s", (listing_id,), fetchone=True)

    if not listing:
        flash("Listing not found.", "danger")
    elif listing["SellerID"] != session["user_id"]:
        flash("Only the seller can delete this listing.", "danger")
    else:
        query_db(
            "DELETE FROM Listings WHERE ListingID=%s AND SellerID=%s",
            (listing_id, session["user_id"]),
            commit=True
        )
        flash("Listing deleted.", "success")

    return redirect(url_for("my_listings"))


@app.route("/my-listings")
@login_required
def my_listings():
    listings = query_db(
        """
        SELECT l.*, c.CategoryName,
               (SELECT ImageURL FROM Listing_Images i WHERE i.ListingID = l.ListingID LIMIT 1) AS ImageURL
        FROM Listings l
        JOIN Categories c ON l.CategoryID = c.CategoryID
        WHERE l.SellerID=%s
        ORDER BY l.CreatedAt DESC
        """,
        (session["user_id"],)
    )
    return render_template("my_listings.html", listings=listings)


@app.route("/listing/<int:listing_id>/save", methods=["POST"])
@login_required
def toggle_save(listing_id):
    existing = query_db(
        "SELECT * FROM Saved WHERE UserID=%s AND ListingID=%s",
        (session["user_id"], listing_id),
        fetchone=True
    )

    if existing:
        query_db(
            "DELETE FROM Saved WHERE UserID=%s AND ListingID=%s",
            (session["user_id"], listing_id),
            commit=True
        )
        flash("Removed from saved listings.", "info")
    else:
        query_db(
            "INSERT INTO Saved (UserID, ListingID) VALUES (%s, %s)",
            (session["user_id"], listing_id),
            commit=True
        )
        flash("Saved listing.", "success")

    return redirect(url_for("listing_detail", listing_id=listing_id))


@app.route("/saved")
@login_required
def saved_listings():
    listings = query_db(
        """
        SELECT l.*, c.CategoryName, u.Name AS SellerName,
               (SELECT ImageURL FROM Listing_Images i WHERE i.ListingID = l.ListingID LIMIT 1) AS ImageURL
        FROM Saved s
        JOIN Listings l ON s.ListingID = l.ListingID
        JOIN Categories c ON l.CategoryID = c.CategoryID
        JOIN Users u ON l.SellerID = u.UserID
        WHERE s.UserID=%s
        ORDER BY s.SavedAt DESC
        """,
        (session["user_id"],)
    )
    return render_template("saved.html", listings=listings)


@app.route("/listing/<int:listing_id>/message", methods=["POST"])
@login_required
def send_message(listing_id):
    content = request.form["message"].strip()
    listing = query_db("SELECT * FROM Listings WHERE ListingID=%s", (listing_id,), fetchone=True)

    if not listing:
        flash("Listing not found.", "danger")
    elif listing["SellerID"] == session["user_id"]:
        flash("You cannot message yourself about your own listing.", "warning")
    elif not content:
        flash("Message cannot be empty.", "danger")
    else:
        query_db(
            """
            INSERT INTO Messages (BuyerID, SellerID, ListingID, MessageContent)
            VALUES (%s, %s, %s, %s)
            """,
            (session["user_id"], listing["SellerID"], listing_id, content),
            commit=True
        )
        flash("Message sent.", "success")

    return redirect(url_for("listing_detail", listing_id=listing_id))


@app.route("/messages")
@login_required
def messages():
    msgs = query_db(
        """
        SELECT m.*, l.Title, buyer.Name AS BuyerName, seller.Name AS SellerName
        FROM Messages m
        JOIN Listings l ON m.ListingID = l.ListingID
        JOIN Users buyer ON m.BuyerID = buyer.UserID
        JOIN Users seller ON m.SellerID = seller.UserID
        WHERE m.BuyerID=%s OR m.SellerID=%s
        ORDER BY m.SentAt DESC
        """,
        (session["user_id"], session["user_id"])
    )
    return render_template("messages.html", messages=msgs)


@app.route("/listing/<int:listing_id>/sold", methods=["POST"])
@login_required
def mark_sold(listing_id):
    buyer_id = request.form.get("buyer_id")
    final_price = request.form.get("final_price")

    listing = query_db("SELECT * FROM Listings WHERE ListingID=%s", (listing_id,), fetchone=True)

    if not listing:
        flash("Listing not found.", "danger")
    elif listing["SellerID"] != session["user_id"]:
        flash("Only the seller can mark this item as sold.", "danger")
    elif listing["Status"] == "sold":
        flash("This listing is already sold.", "warning")
    elif not buyer_id or not final_price:
        flash("Buyer and final price are required.", "danger")
    else:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE Listings SET Status='sold' WHERE ListingID=%s AND SellerID=%s",
                    (listing_id, session["user_id"])
                )
                cur.execute(
                    """
                    INSERT INTO Transactions (ListingID, BuyerID, FinalPrice)
                    VALUES (%s, %s, %s)
                    """,
                    (listing_id, buyer_id, final_price)
                )
            conn.commit()
            flash("Listing marked as sold and transaction recorded.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Could not mark as sold: {e}", "danger")
        finally:
            conn.close()

    return redirect(url_for("listing_detail", listing_id=listing_id))


@app.route("/transactions")
@login_required
def transactions():
    rows = query_db(
        """
        SELECT t.*, l.Title, seller.Name AS SellerName, buyer.Name AS BuyerName
        FROM Transactions t
        JOIN Listings l ON t.ListingID = l.ListingID
        JOIN Users seller ON l.SellerID = seller.UserID
        JOIN Users buyer ON t.BuyerID = buyer.UserID
        WHERE l.SellerID=%s OR t.BuyerID=%s
        ORDER BY t.PurchaseDate DESC
        """,
        (session["user_id"], session["user_id"])
    )
    return render_template("transactions.html", transactions=rows)


@app.route("/users")
@login_required
def users():
    rows = query_db("SELECT UserID, Name, Email FROM Users ORDER BY Name")
    return render_template("users.html", users=rows)


if __name__ == "__main__":
    app.run(debug=True)
