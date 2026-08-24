from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json


DATABASE_NAME = "posts.db"


class PostRepository:
    """Handles all database operations."""

    def __init__(self):
        self.database = DATABASE_NAME

    def connect(self):
        return sqlite3.connect(self.database)

    def create_table(self):
        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Posts (
                id INTEGER PRIMARY KEY,
                post_by TEXT NOT NULL,
                post_dt TEXT NOT NULL,
                post_details TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_date
            ON Posts(post_dt)
        """)

        connection.commit()
        connection.close()

    def add_sample_posts(self):
        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM Posts")
        existing_posts = cursor.fetchone()[0]

        if existing_posts == 0:
            posts = []

            for number in range(1, 51):
                posts.append((
                    number,
                    f"User{number}",
                    f"2026-08-{(number % 28) + 1:02d}",
                    f"Sample social media post number {number}"
                ))

            cursor.executemany("""
                INSERT INTO Posts
                (id, post_by, post_dt, post_details)
                VALUES (?, ?, ?, ?)
            """, posts)

        connection.commit()
        connection.close()

    def get_posts(self, limit, offset):
        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, post_by, post_dt, post_details
            FROM Posts
            ORDER BY post_dt DESC, id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()

        connection.close()

        return rows

    def count_posts(self):
        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM Posts")
        total = cursor.fetchone()[0]

        connection.close()

        return total


class PostService:
    """Contains pagination and business logic."""

    MAX_PAGE_SIZE = 20

    def __init__(self):
        self.repository = PostRepository()

    def fetch_posts(self, page, page_size):

        if page < 1:
            raise ValueError("Page must be greater than or equal to 1.")

        if page_size < 1:
            raise ValueError("Page size must be greater than 0.")

        if page_size > self.MAX_PAGE_SIZE:
            raise ValueError(
                f"Page size cannot be greater than "
                f"{self.MAX_PAGE_SIZE}."
            )

        offset = (page - 1) * page_size

        posts = self.repository.get_posts(
            page_size,
            offset
        )

        total_posts = self.repository.count_posts()

        total_pages = (
            total_posts + page_size - 1
        ) // page_size

        formatted_posts = []

        for post in posts:
            formatted_posts.append({
                "id": post[0],
                "post_by": post[1],
                "post_dt": post[2],
                "post_details": post[3]
            })

        return {
            "page": page,
            "page_size": page_size,
            "total_posts": total_posts,
            "total_pages": total_pages,
            "posts": formatted_posts
        }


class PostsHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests."""

    service = PostService()

    def do_GET(self):

        url = urlparse(self.path)

        if url.path != "/getPostsUploaded":
            self.send_response_data(
                {"error": "Endpoint not found"},
                404
            )
            return

        parameters = parse_qs(url.query)

        try:
            page = int(
                parameters.get("page", ["1"])[0]
            )

            page_size = int(
                parameters.get("page_size", ["10"])[0]
            )

            result = self.service.fetch_posts(
                page,
                page_size
            )

            self.send_response_data(
                result,
                200
            )

        except ValueError as error:
            self.send_response_data(
                {"error": str(error)},
                400
            )

    def send_response_data(self, data, status_code):

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


def prepare_database():

    repository = PostRepository()

    repository.create_table()
    repository.add_sample_posts()


if __name__ == "__main__":

    prepare_database()

    server = HTTPServer(
        ("localhost", 8080),
        PostsHandler
    )

    print("Question 3 API is running.")
    print()
    print(
        "Open: "
        "http://localhost:8080/getPostsUploaded"
        "?page=1&page_size=10"
    )

    server.serve_forever()