from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json


DATABASE_FILE = "device_store.db"


def create_database():

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id INTEGER PRIMARY KEY,
            device_name TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            configuration_changed INTEGER NOT NULL
        )
    """)

    # Add sample devices only the first time
    cursor.execute("SELECT COUNT(*) FROM devices")

    if cursor.fetchone()[0] == 0:

        devices = [
            (101, "Office Router", "10.0.0.10", 1),
            (102, "Office Printer", "10.0.0.20", 0),
            (103, "File Server", "10.0.0.30", 1),
            (104, "Backup Server", "10.0.0.40", 0)
        ]

        cursor.executemany("""
            INSERT INTO devices
            (device_id, device_name, ip_address, configuration_changed)
            VALUES (?, ?, ?, ?)
        """, devices)

    connection.commit()
    connection.close()


def generate_notifications():

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            device_id,
            device_name,
            ip_address
        FROM devices
        WHERE configuration_changed = 1
    """)

    changed_devices = cursor.fetchall()

    notifications = []

    for device_id, device_name, ip_address in changed_devices:

        notifications.append({
            "device_id": device_id,
            "device_name": device_name,
            "ip_address": ip_address,
            "message": "Device configuration has changed."
        })

        cursor.execute("""
            UPDATE devices
            SET configuration_changed = 0
            WHERE device_id = ?
        """, (device_id,))

    connection.commit()
    connection.close()

    return notifications


class NotificationAPI(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path != "/notifications":

            self.send_json(
                {"error": "Endpoint not found"},
                404
            )

            return

        notifications = generate_notifications()

        response = {
            "notifications": notifications
        }

        self.send_json(response, 200)

    def send_json(self, data, status):

        response = json.dumps(
            data,
            indent=4
        ).encode("utf-8")

        self.send_response(status)

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

    create_database()

    server = HTTPServer(
        ("localhost", 8001),
        NotificationAPI
    )

    print("Question 2 API is running.")
    print("Open this in your browser:")
    print("http://localhost:8001/notifications")

    server.serve_forever()