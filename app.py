from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)

def get_db_connection():
    """
    Izveido un atgriež savienojumu ar SQLite datubāzi.
    """
    # Atrod ceļu uz jauno datubāzi (datubaze.db)
    db = Path(__file__).parent / "datubaze.db"

    # Izveido savienojumu ar SQLite datubāzi
    conn = sqlite3.connect(db)

    # Nodrošina, ka rezultāti būs pieejami kā vārdnīcas (piemēram: product["name"])
    conn.row_factory = sqlite3.Row

    # Atgriež savienojumu
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/instrumenti")
def products():
    from flask import request
    conn = get_db_connection()

    # Nolasām izvēlēto tipu un maksimālo cenu no URL parametriem
    selected_type = request.args.get("type")
    max_price = request.args.get("max_price", type=float)

    # SQL vaicājums, kas atlasīs visus instrumentus ar papildinformāciju
    query = """
        SELECT 
            i.id, 
            i.name, 
            i.price, 
            i.image,
            b.name AS brand,
            t.name AS type,
            s.name AS store
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.id
        LEFT JOIN types t ON i.type_id = t.id
        LEFT JOIN stores s ON t.store_id = s.id
        WHERE 1=1
    """
    params = []

    # Ja lietotājs izvēlējies tipu, pievienojam to vaicājumam
    if selected_type:
        query += " AND t.name = ?"
        params.append(selected_type)

    # Ja lietotājs ievadījis maksimālo cenu, pievienojam arī šo filtru
    if max_price is not None:
        query += " AND i.price <= ?"
        params.append(max_price)

    # Izpildām vaicājumu ar filtriem
    instruments = conn.execute(query, params).fetchall()

    # Iegūstam visus unikālos tipus, lai varētu parādīt izvēlnē
    all_types = conn.execute("SELECT DISTINCT name FROM types").fetchall()
    conn.close()

    # Atgriežam veidni ar produktiem un filtru datiem
    return render_template("products.html", products=instruments, types=all_types, selected_type=selected_type, max_price=max_price)


# Maršruts, kas atbild uz pieprasījumu, piemēram: /instrumenti/3
@app.route("/instrumenti/<int:product_id>")
def products_show(product_id):
    conn = get_db_connection()  # Pieslēdzas datubāzei

    # Atlasa vienu instrumentu pēc ID, pievienojot arī citu informāciju
    product = conn.execute("""
        SELECT 
            instruments.*,
            brands.name AS brand,
            types.name AS type,
            stores.name AS store
        FROM instruments
        LEFT JOIN brands ON instruments.brand_id = brands.id
        LEFT JOIN types ON instruments.type_id = types.id
        LEFT JOIN stores ON types.store_id = stores.id
        WHERE instruments.id = ?
    """, (product_id,)).fetchone()

    conn.close()  # Aizver savienojumu ar datubāzi

    # Atgriež HTML veidni 'products_show.html', padodot konkrēto instrumentu veidnei
    return render_template("products_show.html", product=product)

@app.route("/par-mums")
def about():
    return render_template("about.html")

@app.route("/instrumenti/pievienot", methods=["GET", "POST"])
def add_instrument():
    conn = get_db_connection()
    
    if request.method == "POST":
        # Nolasām datus no formas
        name = request.form["name"]
        price = float(request.form["price"])
        image = request.form["image"]
        brand_id = int(request.form["brand_id"])
        type_id = int(request.form["type_id"])

        # Saglabājam jaunu ierakstu datubāzē
        conn.execute(
            "INSERT INTO instruments (name, price, image, brand_id, type_id) VALUES (?, ?, ?, ?, ?)",
            (name, price, image, brand_id, type_id)
        )
        conn.commit()
        conn.close()

        # Pāradresējam uz instrumentu sarakstu
        return redirect(url_for("products"))

    # Ja GET pieprasījums – iegūstam dropdown datus
    brands = conn.execute("SELECT * FROM brands").fetchall()
    types = conn.execute("SELECT * FROM types").fetchall()
    conn.close()

    return render_template("add_instrument.html", brands=brands, types=types)

@app.route("/instrumenti/rediget/<int:product_id>", methods=["GET", "POST"])
def edit_instrument(product_id):
    conn = get_db_connection()

    if request.method == "POST":
        # Nolasām jaunos datus no formas
        name = request.form["name"]
        price = float(request.form["price"])
        image = request.form["image"]
        brand_id = int(request.form["brand_id"])
        type_id = int(request.form["type_id"])

        # Atjaunojam datubāzē
        conn.execute(
            "UPDATE instruments SET name = ?, price = ?, image = ?, brand_id = ?, type_id = ? WHERE id = ?",
            (name, price, image, brand_id, type_id, product_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("products"))

    # Iegūstam esošos datus, ko ievietot formā
    instrument = conn.execute("SELECT * FROM instruments WHERE id = ?", (product_id,)).fetchone()
    brands = conn.execute("SELECT * FROM brands").fetchall()
    types = conn.execute("SELECT * FROM types").fetchall()
    conn.close()

    return render_template("edit_instrument.html", product=instrument, brands=brands, types=types)


@app.route("/instrumenti/dzest/<int:product_id>", methods=["POST"])
def delete_instrument(product_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM instruments WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("products"))


if __name__ == "__main__":
    app.run(debug=True)
