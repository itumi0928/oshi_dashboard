from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

            if not content.strip():
                return []

            return json.loads(content)

    except json.JSONDecodeError:
        return []

def save_json(filename, data):
    filepath = os.path.join(DATA_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True

    except OSError:
        return False

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if self.path.startswith("/static/"):
            self.serve_static(path)
            return

        if path == '/':
            favorites = load_json("favorites.json")

            favorite_rows = ""

            for item in favorites:
                favorite_rows += f"""
                <tr>
                    <td>{item["id"]}</td>
                    <td>{item["title"]}</td>
                    <td>{item["genre"]}</td>
                </tr>
                """

            news = load_json("news.json")

            news_html = ""

            for article in news["articles"]:
                news_html += f"""
                <li>
                    <a href="{article["url"]}" target="_blank">
                        {article["title"]}
                    </a>
                    <p>{article["summary"]}</p>
                </li>
                """

            quotes = load_json("quotes.json")

            quote = quotes["quotes"][0]

            quote_html = f"""
            <blockquote>
                「{quote["text"]}」
            </blockquote>
            <p>{quote["author"]}</p>
            """

            weather = load_json("weather.json")

            weather_html = f"""
            <p>{weather["weather"]}</p>
            <p>気温:{weather["temperature"]}℃</p>
            """

            images = load_json("images.json")

            image_html = ""

            if images:
                image_html = f"""
                <img src="{images[0]["url"]}" alt="ランダム画像">
                """

            self.render_template(
                "index.html",
                favorite_rows=favorite_rows,
                news_html=news_html,
                quote_html=quote_html,
                weather_html=weather_html,
                image_html=image_html
            )

        elif path == '/favorites':
            favorites = load_json("favorites.json")

            favorite_rows = ""

            for item in favorites:
                favorite_rows += f"""
                <tr>
                    <td>{item["id"]}</td>
                    <td>{item["title"]}</td>
                    <td>{item["genre"]}</td>
                </tr>
                """

            self.render_template(
                'favorites.html',
                favorite_rows=favorite_rows
                )

        elif path == '/add':
            self.render_template('add.html')

        elif path == '/search':
            query = urllib.parse.parse_qs(
                parsed_url.query
            ).get("title", [""])[0].strip()

            if not query:
                self.render_template(
                    "search.html",
                    error="検索するタイトルを入力してください。",
                    search_results=""
                )
                return

            favorites = load_json("favorites.json")

            results = [
                item for item in favorites
                if query.lower() in item["title"].lower()
            ]

            if not results:
                self.render_template(
                    "search.html",
                    error="該当するお気に入りがありません。",
                    search_results=""
                )
                return

            search_results = "<h2>検索結果</h2>"

            search_results += """
            <table>
                <tr>
                    <th>ID</th>
                    <th>タイトル</th>
                    <th>ジャンル</th>
                </tr>
            """

            for item in results:
                search_results += f"""
                <tr>
                    <td>{item["id"]}</td>
                    <td>{item["title"]}</td>
                    <td>{item["genre"]}</td>
                </tr>
                """

            search_results += "</table>"

            self.render_template(
                "search.html",
                error="",
                search_results=search_results
            )

        elif path == '/delete':
            self.render_template('delete.html')

        else:
            self.send_404()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")

        params = urllib.parse.parse_qs(post_data)

        if path == "/add":
            title = params.get("title", [""])[0]
            genre = params.get("genre", [""])[0]

            if not title or not genre:
                self.render_template(
                    "add.html",
                    error="タイトルとジャンルを入力してください。"
                )
                return

            favorites = load_json("favorites.json")

            new_id = 1

            if favorites:
                new_id = max(item["id"] for item in favorites) + 1

            new_item = {
                "id": new_id,
                "title": title,
                "genre": genre
            }

            favorites.append(new_item)

            if not save_json("favorites.json", favorites):
                self.render_template(
                    "add.html",
                    error="お気に入りの保存に失敗しました。"
                )
                return

            favorite_rows = ""

            for item in favorites:
                favorite_rows += f"""
                <tr>
                    <td>{item["id"]}</td>
                    <td>{item["title"]}</td>
                    <td>{item["genre"]}</td>
                </tr>
                """

            self.render_template(
                "favorites.html",
                favorite_rows=favorite_rows
            )

        elif path == "/delete":
            id_text = params.get("id", [""])[0]

            if not id_text:
                self.render_template(
                    "delete.html",
                    error="削除するIDを入力してください。"
                )
                return

            try:
                delete_id = int(id_text)
            except ValueError:
                self.render_template(
                    "delete.html",
                    error="IDには数字を入力してください。"
                )
                return

            favorites = load_json("favorites.json")

            favorites = [
                item for item in favorites
                if item["id"] != delete_id
            ]

            if not save_json("favorites.json", favorites):
                self.render_template(
                    "delete.html",
                error="お気に入りの削除に失敗しました。"
                )
                return

            favorite_rows = ""

            for item in favorites:
                favorite_rows += f"""
                <tr>
                    <td>{item["id"]}</td>
                    <td>{item["title"]}</td>
                    <td>{item["genre"]}</td>
                </tr>
                """

            self.render_template(
                "favorites.html",
                favorite_rows=favorite_rows
            )

        elif path == "/submit":
            message = params.get("message", [""])[0]

            self.render_template(
                "submit.html",
                message=message
            )

        else:
            self.send_404()

    def render_template(self, filename, **kwargs):

        try:
            filepath = os.path.join(BASE_DIR, "templates", filename)

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            for key, value in kwargs.items():
                content = content.replace(f"{{{{ {key} }}}}", str(value))

            self.send_response(200)

            self.send_header("Content-type", "text/html; charset=utf-8")

            self.end_headers()

            self.wfile.write(content.encode("utf-8"))

        except FileNotFoundError:
            self.send_404()

    def serve_static(self, path):
        try:
            filepath = os.path.join(BASE_DIR, path.lstrip("/"))

            with open(filepath, 'rb') as f:
                content = f.read()

            if path.endswith(".css"):
                content_type = "text/css; charset=utf-8"

            else:
                content_type = "application/octet-stream"

            self.send_response(200)

            self.send_header('Content-type', content_type)

            self.end_headers()

            self.wfile.write(content)

        except FileNotFoundError:
            self.send_404()

    def send_404(self):
        self.send_response(404)

        self.send_header('Content-type', 'text/html; charset=utf-8')

        self.end_headers()

        self.wfile.write('<h1>404 Not Found</h1>'.encode('utf-8'))

def run():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MyHandler)
    print('サーバーを起動しました: http://localhost:8000')

    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        print("サーバーを停止しました")

        httpd.server_close()
    
if __name__ == '__main__':
    run()