from flask import Flask, render_template, request, jsonify, send_file
import os
import requests
import time
import random
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

# Configuration paths
CONFIG_DIR = "/config"
BACKDROP_DIR = os.path.join(CONFIG_DIR, "Backdrops", "All_Backdrops")
LOG_FILE = os.path.join(CONFIG_DIR, "latest_log.txt")
TITLES_FILE = os.path.join(CONFIG_DIR, "titles.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Ensure backdrop directory exists
os.makedirs(BACKDROP_DIR, exist_ok=True)

scheduler = BackgroundScheduler()

# Default configuration
default_config = {
    "tmdb_api": "",
    "tvdb_api": "",
    "fanart_api": "",
    "movies_source": "TMDB",
    "tvshows_source": "TVDB",
    "backdrop_limit": "10",
    "run_frequency": "manual",
    "schedule_day": "monday",
    "schedule_time": "12:00"
}

# Load or create config
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return default_config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def log_download(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {message}\n")

def download_backdrop(title, source, media_type, media_id):
    config = load_config()
    api_key = config[f"{source.lower()}_api"]
    if not api_key:
        log_download(f"API key missing for {source}")
        return

    backdrop_url = ""
    if source == "TMDB":
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/images?api_key={api_key}"
        response = requests.get(url).json()
        if "backdrops" in response and response["backdrops"]:
            backdrop_url = f"https://image.tmdb.org/t/p/original{response['backdrops'][0]['file_path']}"
    elif source == "TVDB":
        # TVDB API requires authentication, implement proper calls here
        pass
    elif source == "Fanart":
        url = f"https://webservice.fanart.tv/v3/{media_type}/{media_id}?api_key={api_key}"
        response = requests.get(url).json()
        if media_type == "movie" and "moviebackground" in response:
            backdrop_url = response["moviebackground"][0]["url"]
        elif media_type == "tv" and "showbackground" in response:
            backdrop_url = response["showbackground"][0]["url"]

    if backdrop_url:
        img_data = requests.get(backdrop_url).content
        file_name = f"{title.replace(' ', '_')}_{source}.jpg"
        file_path = os.path.join(BACKDROP_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(img_data)
        log_download(f"Downloaded {file_name} from {source}")
    else:
        log_download(f"No backdrops found for {title} on {source}")

@app.route('/')
def index():
    config = load_config()
    return render_template("index.html", config=config)

@app.route('/config', methods=['POST'])
def update_config():
    data = request.json
    config = {
        "tmdb_api": data.get("tmdb_api", ""),
        "tvdb_api": data.get("tvdb_api", ""),
        "fanart_api": data.get("fanart_api", ""),
        "movies_source": data.get("movies_source", "TMDB"),
        "tvshows_source": data.get("tvshows_source", "TVDB"),
        "backdrop_limit": data.get("backdrop_limit", "10"),
        "run_frequency": data.get("run_frequency", "manual"),
        "schedule_day": data.get("schedule_day", "monday").lower(),
        "schedule_time": data.get("schedule_time", "12:00")
    }
    save_config(config)
    schedule_download()
    return jsonify({"message": "Configuration updated", "config": config})

@app.route('/Backdrops/All_Backdrops/<filename>')
def serve_backdrop(filename):
    """ Serves the requested backdrop file """
    file_path = os.path.join(BACKDROP_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/jpeg')
    return "Not Found", 404

@app.route('/random-backdrop')
def random_backdrop():
    """ Selects a random backdrop to serve """
    files = [f for f in os.listdir(BACKDROP_DIR) if f.endswith(".jpg")]
    if files:
        random_file = random.choice(files)
        return send_file(os.path.join(BACKDROP_DIR, random_file), mimetype='image/jpeg')
    return "Not Found", 404

def schedule_download():
    config = load_config()
    if config["run_frequency"] == "weekly":
        day_of_week_map = {
            "monday": "mon",
            "tuesday": "tue",
            "wednesday": "wed",
            "thursday": "thu",
            "friday": "fri",
            "saturday": "sat",
            "sunday": "sun"
        }
        day_of_week = day_of_week_map.get(config["schedule_day"].lower(), "mon")  # Default to Monday if invalid
        schedule_time = config["schedule_time"]
        hour, minute = map(int, schedule_time.split(":"))

        scheduler.add_job(
            run_scheduled_download,
            'cron',
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            id='weekly_download',
            replace_existing=True
        )
        scheduler.start()

def run_scheduled_download():
    log_download("Scheduled weekly download initiated.")
    # Here, implement logic to fetch movie/TV show list and call `download_backdrop`

@app.route('/run-now', methods=['POST'])
def run_now():
    log_download("Manual run initiated.")
    # Implement fetching movie/TV list and calling `download_backdrop`
    return jsonify({"message": "Backdrop download started."})

if __name__ == '__main__':
    schedule_download()
    app.run(host='0.0.0.0', port=8500, debug=True)

