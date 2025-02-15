from flask import Flask, render_template, request, jsonify
import os
import json
import requests

app = Flask(__name__)

# Config file path
CONFIG_PATH = "/config/settings.conf"
DEFAULT_CONFIG = {
    "tmdb_api_key": "",
    "tvdb_api_key": "",
    "fanart_api_key": "",
    "movies_source": "",
    "shows_source": "",
    "backdrop_limit": "All",
    "preferred_source": "TMDB"
}

# Load configuration
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = DEFAULT_CONFIG
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

# Ensure Backdrop folders exist
BACKDROP_DIR = "/config/Backdrops"
MOVIE_BACKDROP_DIR = os.path.join(BACKDROP_DIR, "Movies")
TV_BACKDROP_DIR = os.path.join(BACKDROP_DIR, "TV Shows")
os.makedirs(MOVIE_BACKDROP_DIR, exist_ok=True)
os.makedirs(TV_BACKDROP_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/save_config", methods=["POST"])
def save_config():
    data = request.json
    config.update(data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
    return jsonify({"message": "Configuration updated successfully!"})

@app.route("/fetch_backdrops", methods=["POST"])
def fetch_backdrops():
    source = request.json.get("source")
    limit = request.json.get("limit")
    if source == "TMDB":
        return fetch_tmdb_backdrops(limit)
    elif source == "TVDB":
        return fetch_tvdb_backdrops(limit)
    elif source == "Fanart":
        return fetch_fanart_backdrops(limit)
    return jsonify({"error": "Invalid source selection"}), 400

# Fetch TMDB Backdrops
def fetch_tmdb_backdrops(limit):
    api_key = config["tmdb_api_key"]
    if not api_key:
        return jsonify({"error": "TMDB API key is missing"}), 400
    
    movies_folder = config["movies_source"]
    for movie in os.listdir(movies_folder):
        if "tmdb-" in movie:
            tmdb_id = movie.split("tmdb-")[1].strip("}")
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images?api_key={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                images = response.json().get("backdrops", [])[:int(limit)]
                save_images(images, movie, MOVIE_BACKDROP_DIR)
    return jsonify({"message": "TMDB Backdrops fetched successfully!"})

# Fetch TVDB Backdrops
def fetch_tvdb_backdrops(limit):
    api_key = config["tvdb_api_key"]
    if not api_key:
        return jsonify({"error": "TVDB API key is missing"}), 400
    # TVDB API request handling here...
    return jsonify({"message": "TVDB Backdrops fetched successfully!"})

# Fetch Fanart Backdrops
def fetch_fanart_backdrops(limit):
    api_key = config["fanart_api_key"]
    if not api_key:
        return jsonify({"error": "Fanart API key is missing"}), 400
    # Fanart API request handling here...
    return jsonify({"message": "Fanart Backdrops fetched successfully!"})

# Save images to respective folders
def save_images(images, title, dest_folder):
    title_path = os.path.join(dest_folder, title)
    os.makedirs(title_path, exist_ok=True)
    for index, image in enumerate(images):
        img_url = f"https://image.tmdb.org/t/p/original{image['file_path']}"
        img_data = requests.get(img_url).content
        with open(os.path.join(title_path, f"backdrop_{index+1}.jpg"), "wb") as f:
            f.write(img_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8500, debug=True)
