from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3
import json


DATABASE = "inventory_data.db"


def setup_database():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY,
            purchased_on TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_info (
            info_id INTEGER PRIMARY KEY,
            inventory_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY (inventory_id)
                REFERENCES inventory(inventory_id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM inventory")

    if cursor.fetchone()[0] == 0:

        inventory_rows = [
            (101, "2026-02-12", 42000),
            (102, "2026-04-18", 18000),
            (103, "2026-08-05", 65000),
            (104, "2027-01-20", 25000)
        ]

        cursor.executemany("""
            INSERT INTO inventory
            (inventory_id, purchased_on, amount)
            VALUES (?, ?, ?)
        """, inventory_rows)

        detail_rows = [
            (1, 101, "Lenovo Laptop"),
            (2, 102, "HP Monitor"),
            (3, 103, "Dell Workstation"),
            (4, 104, "Canon Printer")
        ]

        cursor.executemany("""
            INSERT INTO inventory_info
            (info_id, inventory_id, description)
            VALUES (?, ?, ?)
        """, detail_rows)

    db.commit()
    db.close()


def find_inventory(start_date, end_date):

    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            i.inventory_id,
            i.purchased_on,
            i.amount,
            d.description
        FROM inventory AS i
        INNER JOIN inventory_info AS d
            ON i.inventory_id = d.inventory_id
        WHERE i.purchased_on BETWEEN ? AND ?
        ORDER BY i.purchased_on
    """, (start_date, end_date))

    rows = cursor.fetchall()
    db.close()

    result = []

    for inventory_id, date, amount, description in rows:
        result.append({
            "inventory_id": inventory_id,
            "purchase_date": date,
            "cost": amount,
            "description": description
        })

    return result


class InventoryAPI(BaseHTTPRequestHandler):

    def do_GET(self):

        url = urlparse(self.path)

        if url.path != "/inventory":
            self.send_error(404, "Endpoint not found")
            return

        values = parse_qs(url.query)

        start_date = values.get("from", [None])[0]
        end_date = values.get("to", [None])[0]

        if not start_date or not end_date:

            self.send_json({
                "error": "Please provide 'from' and 'to' dates"
            }, 400)

            return

        records = find_inventory(
            start_date,
            end_date
        )

        self.send_json(records, 200)

    def send_json(self, data, status_code):

        response = json.dumps(
            data,
            indent=4
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Content-Length",
            str(len(response))
        )
        self.end_headers()

        self.wfile.write(response)


if __name__ == "__main__":

    setup_database()

    server = HTTPServer(
        ("localhost", 8000),
        InventoryAPI
    )

    print("Question 1 API is running.")
    print("Open this in your browser:")
    print(
        "http://localhost:8000/"
        "inventory?from=2026-01-01&to=2026-12-31"
    )

    server.serve_forever()