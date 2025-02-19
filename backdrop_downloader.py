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
BACKDROP_DIR = os.path.join(CONFIG_DIR, "Backdrops")
LOGS_DIR = os.path.join(CONFIG_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "backdrop_download.log")
TITLES_FILE = os.path.join(CONFIG_DIR, "titles.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Ensure backdrop directory and logs directory exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(BACKDROP_DIR, exist_ok=True)

scheduler = BackgroundScheduler()

# Default configuration
default_config = {
    "tmdb_api": "",
    "fanart_api": "",
    "trakt_api": "",
    "movies_source": "TMDB",
    "tvshows_source": "TMDB",
    "backdrop_limit": "1",
    "run_frequency": "manual",
    "schedule_day": "monday",
    "schedule_time": "12:00",
    "data_source": "My Devices",  # Options: My Devices, Trakt List
    "movies_folder": "",
    "tvshows_folder": "",
    "trakt_movies_list": "",  # URL for Trakt Movies List
    "trakt_tvshows_list": "",  # URL for Trakt TV Shows List
    "use_trakt_api": False  # If True, use Trakt API to fetch TMDB IDs, otherwise use TMDB API
}

# Load or create config
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f)

# Ensure settings.conf exists
SETTINGS_CONF_FILE = os.path.join(CONFIG_DIR, "settings.conf")

def ensure_settings_conf():
    """Ensures settings.conf exists and creates a default one if missing."""
    if not os.path.exists(SETTINGS_CONF_FILE):
        default_settings = "[DEFAULT]\ntmdb_api=\nfanart_api=\ntrakt_api=\n"
        with open(SETTINGS_CONF_FILE, "w") as f:
            f.write(default_settings)
        print("LOG: Created missing settings.conf file.")

ensure_settings_conf()

# Load or create the titles.json file
TITLES_FILE = os.path.join(CONFIG_DIR, "titles.json")

if not os.path.exists(TITLES_FILE):
    with open(TITLES_FILE, "w") as f:
        json.dump([], f)  # Create an empty JSON array
    print("LOG: Created missing titles.json file")

def extract_titles_from_folders():
    """ Extracts titles and TMDB IDs from either local device folders or Trakt lists. """
    config = load_config()
    data_source = config.get("data_source", "My Devices")  # Check selected data source
    titles = []

    if data_source == "My Devices":
        movies_path = config.get("movies_folder", "")
        tvshows_path = config.get("tvshows_folder", "")

        # Adjust paths if running inside Docker (maps NAS paths to container paths)
        if movies_path.startswith("/volume1/"):
            movies_path = movies_path.replace("/volume1/Movies", "/movies")
        if tvshows_path.startswith("/volume1/"):
            tvshows_path = tvshows_path.replace("/volume1/TV Shows", "/tvshows")

        # Process movies
        if os.path.exists(movies_path):
            for folder in os.listdir(movies_path):
                if "tmdb-" in folder:
                    parts = folder.split("tmdb-")
                    title = parts[0].strip()
                    tmdb_id = parts[1].split("}")[0]
                    titles.append({"title": title, "type": "movie", "id": tmdb_id})
                else:
                    print(f"WARNING: Skipped '{folder}' in Movies (No TMDB ID found)")
                    log_download(f"WARNING: Skipped '{folder}' in Movies (No TMDB ID found)")

        # Process TV shows
        if os.path.exists(tvshows_path):
            for folder in os.listdir(tvshows_path):
                if "tmdb-" in folder:
                    parts = folder.split("tmdb-")
                    title = parts[0].strip()
                    tmdb_id = parts[1].split("}")[0]
                    titles.append({"title": title, "type": "tv", "id": tmdb_id})
                else:
                    print(f"WARNING: Skipped '{folder}' in TV Shows (No TMDB ID found)")
                    log_download(f"WARNING: Skipped '{folder}' in TV Shows (No TMDB ID found)")

    elif data_source == "Trakt List":
        trakt_movies_url = config.get("trakt_movies_list", "")
        trakt_tvshows_url = config.get("trakt_tvshows_list", "")

        # Fetch movies from Trakt
        if trakt_movies_url:
            trakt_movies = fetch_trakt_list(trakt_movies_url, "movie")
            titles.extend(trakt_movies)

        # Fetch TV shows from Trakt
        if trakt_tvshows_url:
            trakt_tvshows = fetch_trakt_list(trakt_tvshows_url, "tv")
            titles.extend(trakt_tvshows)

        # Resolve TMDB IDs using TMDB API if missing
        for entry in titles:
            if not entry["id"]:
                tmdb_id = fetch_tmdb_id(entry["title"], entry["type"])
                if tmdb_id:
                    entry["id"] = str(tmdb_id)
                else:
                    print(f"WARNING: Could not resolve TMDB ID for {entry['title']}, skipping...")
                    log_download(f"WARNING: Could not resolve TMDB ID for {entry['title']}, skipping...")
                    titles.remove(entry)

    # Save extracted titles
    with open(TITLES_FILE, "w") as f:
        json.dump(titles, f, indent=4)

    print(f"LOG: Extracted {len(titles)} titles from {data_source}.")
    log_download(f"Extracted {len(titles)} titles from {data_source}.")

    # Adjust paths if running inside Docker (maps NAS paths to container paths)
    if movies_path.startswith("/volume1/"):
        movies_path = movies_path.replace("/volume1/Movies", "/movies")
    if tvshows_path.startswith("/volume1/"):
        tvshows_path = tvshows_path.replace("/volume1/TV Shows", "/tvshows")

    movie_format = config.get("movies_folder_structure", "{Movie CleanTitle} ({Release Year}) {tmdb-{TmdbId}}")
    tv_format = config.get("tvshows_folder_structure", "{TV Show CleanTitle} ({Release Year}) {tmdb-{TmdbId}}")

    titles = []

    # Process movies
    if os.path.exists(movies_path):
        for folder in os.listdir(movies_path):
            found_id = False
            if "tmdb-" in folder:
                parts = folder.split("tmdb-")
                title = parts[0].strip()
                tmdb_id = parts[1].split("}")[0]
                titles.append({"title": title, "type": "movie", "id": tmdb_id})
                found_id = True
        
            if not found_id:
                if movies_path and os.path.exists(movies_path) and folder in os.listdir(movies_path):
                    log_download(f"WARNING: Skipped '{folder}' in Movies (No TMDB ID found)")
                elif tvshows_path and os.path.exists(tvshows_path) and folder in os.listdir(tvshows_path):
                    log_download(f"WARNING: Skipped '{folder}' in TV Shows (No TMDB ID found)")
                else:
                    log_download(f"WARNING: Skipped '{folder}' (No TMDB ID found)")

    # Process TV shows
    if os.path.exists(tvshows_path):
        for folder in os.listdir(tvshows_path):
            found_id = False
            if "tmdb-" in folder:
                parts = folder.split("tmdb-")
                title = parts[0].strip()
                tmdb_id = parts[1].split("}")[0]
                titles.append({"title": title, "type": "tv", "id": tmdb_id})
                found_id = True

            if not found_id:
                if tvshows_path and os.path.exists(tvshows_path) and folder in os.listdir(tvshows_path):
                    log_download(f"WARNING: Skipped '{folder}' in TV Shows (No TMDB ID found)")
                else:
                    log_download(f"WARNING: Skipped '{folder}' (No TMDB ID found)")
            
    with open(TITLES_FILE, "w") as f:
        json.dump(titles, f, indent=4)

    print(f"LOG: Extracted {len(titles)} titles from Movies & TV folders.")

def load_config():
    """Loads configuration and ensures new settings are included if missing."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        # Ensure all default keys exist in the loaded config (for backward compatibility)
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        return config

    return default_config

def save_config(config):
    """Saves the user configuration, ensuring only valid keys are stored."""
    valid_config = {key: config.get(key, default) for key, default in default_config.items()}
    with open(CONFIG_FILE, "w") as f:
        json.dump(valid_config, f, indent=4)

def log_download(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} - {message}\n")

def fetch_tmdb_id(title, media_type):
    """Fetch the TMDB ID for a given title from TMDB API."""
    config = load_config()
    api_key = config.get("tmdb_api", "")

    if not api_key:
        print("ERROR: Missing TMDB API key. Cannot fetch TMDB ID.")
        log_download("ERROR: Missing TMDB API key. Cannot fetch TMDB ID.")
        return None

    search_type = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/search/{search_type}?api_key={api_key}&query={requests.utils.quote(title)}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            tmdb_id = data["results"][0]["id"]
            print(f"INFO: Found TMDB ID {tmdb_id} for {title}.")
            return tmdb_id
        else:
            print(f"WARNING: No TMDB ID found for {title}.")
            log_download(f"WARNING: No TMDB ID found for {title}.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: TMDB API request failed - {e}")
        log_download(f"ERROR: TMDB API request failed - {e}")
        return None

def fetch_trakt_list(trakt_url, media_type):
    """
    Fetches movies or TV shows from a given Trakt list URL.
    Extracts TMDB IDs either using the Trakt API or TMDB API.
    """
    config = load_config()
    use_trakt_api = config.get("use_trakt_api", False)
    trakt_api_key = config.get("trakt_api", "")

    headers = {}
    if use_trakt_api and trakt_api_key:
        headers["Content-Type"] = "application/json"
        headers["trakt-api-version"] = "2"
        headers["trakt-api-key"] = trakt_api_key
        api_url = f"https://api.trakt.tv{trakt_url}/items"
    else:
        api_url = trakt_url  # Use direct URL scraping if Trakt API is disabled

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch data from Trakt list: {e}")
        log_download(f"ERROR: Failed to fetch data from Trakt list: {e}")
        return []

    extracted_titles = []
    for item in data:
        media = item.get("movie") if media_type == "movie" else item.get("show")
        if not media:
            continue

        title = media.get("title", "Unknown Title")
        tmdb_id = media.get("ids", {}).get("tmdb", None)

        if not tmdb_id:
            print(f"WARNING: No TMDB ID found for {title}, skipping...")
            log_download(f"WARNING: No TMDB ID found for {title}, skipping...")
            continue

        extracted_titles.append({"title": title, "type": media_type, "id": str(tmdb_id)})

    return extracted_titles

def download_backdrop(title, source, media_type, media_id):
    print(f" Function called: download_backdrop('{title}', '{source}', '{media_type}', {media_id})")

    config = load_config()
    api_key = config.get(f"{source.lower()}_api", "")

    # Check if we need to fetch TMDB ID from TMDB API (when Trakt API is not available)
    if media_id is None or media_id == "":
        print(f"INFO: No TMDB ID found for {title}. Fetching from TMDB API...")
        media_id = fetch_tmdb_id(title, media_type)
        if not media_id:
            log_download(f"ERROR: Unable to fetch TMDB ID for {title}. Skipping backdrop download.")
            return

    # Get backdrop limit from config
    backdrop_limit = config.get("backdrop_limit", "1").strip().lower()

    # Define `url` based on the source
    if source == "TMDB":
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/images?api_key={api_key}"
    elif source == "Fanart":
        url = f"https://webservice.fanart.tv/v3/{media_type}/{media_id}?api_key={api_key}"
    else:
        print(f" ERROR: Invalid source '{source}'")
        log_download(f"ERROR: Invalid source '{source}'")
        return

    # Make the API request
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        response = response.json()
    except requests.exceptions.RequestException as e:
        print(f" ERROR: API request failed for {source} - {e}")
        log_download(f"ERROR: API request failed for {source} - {e}")
        return

    print(f" API Response: {response}")

    # Apply No Languages filter for TMDB
    if source == "TMDB":
        backdrops = [b for b in response.get("backdrops", []) if b.get("iso_639_1") is None]
    elif source == "Fanart":
        backdrops = [b for b in response.get(f"{'moviebackground' if media_type == 'movie' else 'showbackground'}", []) if b.get("lang") == "none"]
    else:
        backdrops = []

    # Determine the limit
    if backdrop_limit in [None, "", "all"]:
        limit = len(backdrops)
    else:
        try:
            limit = max(1, int(backdrop_limit))
        except ValueError:
            limit = 1

    if not backdrops:
        print(f" No backdrops found in 'No Languages' section for {title} on {source}.")
        log_download(f"No backdrops found in 'No Languages' section for {title} on {source}.")
        return

    # Download up to the requested number of backdrops
    for i, backdrop in enumerate(backdrops[:limit]):
        backdrop_url = backdrop["url"] if source == "Fanart" else f"https://image.tmdb.org/t/p/original{backdrop['file_path']}"
        save_backdrop(title, source, backdrop_url, i)

    # Get backdrop limit from config
    backdrop_limit = config.get("backdrop_limit", "1").strip().lower()

    # Define `url` FIRST, before making the request
    if source == "TMDB":
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/images?api_key={api_key}"
    elif source == "Fanart":
        url = f"https://webservice.fanart.tv/v3/{media_type}/{media_id}?api_key={api_key}"
    else:
        print(f" ERROR: Invalid source '{source}'")
        log_download(f"ERROR: Invalid source '{source}'")
        return

    # Make the API request (only once)
    try:
        response = requests.get(url, timeout=10)  # Now `url` exists 
        response.raise_for_status()  
        response = response.json()
    except requests.exceptions.RequestException as e:
        print(f" ERROR: API request failed for {source} - {e}")
        log_download(f"ERROR: API request failed for {source} - {e}")

        # Fallback logic: If Fanart fails, try TMDB
        if source == "Fanart":
            log_download(f"Retrying {title} with TMDB instead of Fanart.tv.")
            download_backdrop(title, "TMDB", media_type, media_id)
        return

    print(f" API Response: {response}")  # Log the API response

    # Now we determine the limit AFTER we have the response
    if backdrop_limit in [None, "", "all"]:  # Handle None, empty, or "all" cases
        limit = len(response.get("backdrops", [])) if "backdrops" in response else 0
    else:
        try:
            limit = max(1, int(backdrop_limit))  # Ensure at least 1
        except ValueError:
            limit = 1  # Fallback to default if invalid input

    # Keep the API key validation check at the end
    if not api_key:
        print(f" API key missing for {source}")
        log_download(f"API key missing for {source}")
        return

        # Fetch API response first
        try:
            response = requests.get(url, timeout=10)  # Timeout to prevent hanging
            response.raise_for_status()  # Raise an error for HTTP failures (4xx, 5xx)
            response = response.json()  # Convert to JSON
        except requests.exceptions.RequestException as e:
            print(f" ERROR: API request failed for {source} - {e}")
            log_download(f"ERROR: API request failed for {source} - {e}")

            # Fallback logic: If Fanart fails, try TMDB
            if source == "Fanart":
                log_download(f"Retrying {title} with TMDB instead of Fanart.tv.")
                download_backdrop(title, "TMDB", media_type, media_id)
            return

        print(f" API Response: {response}")  # Log the API response

        # If user enters "all" or leaves it blank, download everything
        if backdrop_limit == "" or backdrop_limit == "all":
            limit = len(response.get("backdrops", []))
        else:
            try:
                limit = max(1, int(backdrop_limit))  # Ensure minimum of 1
            except ValueError:
                limit = 1  # Fallback to default if input is invalid

        # Download only backdrops from the "No Languages" section
        tmdb_backdrops = [b for b in response.get("backdrops", []) if b.get("iso_639_1") is None]

        if not tmdb_backdrops:
            print(f" No backdrops found in 'No Languages' section for {title} on TMDB.")
            log_download(f"No backdrops found in 'No Languages' section for {title} on TMDB.")
            return

        for i, backdrop in enumerate(tmdb_backdrops[:limit]):  # Apply limit properly
            backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop['file_path']}"
            save_backdrop(title, source, backdrop_url, i)

    elif source == "Fanart":
        url = f"https://webservice.fanart.tv/v3/{media_type}/{media_id}?api_key={api_key}"
        try:
            response = requests.get(url, timeout=10)  # Timeout to prevent hanging
            response.raise_for_status()  # Raise an error for HTTP failures (4xx, 5xx)
            response = response.json()  # Convert to JSON
        except requests.exceptions.RequestException as e:
            print(f" ERROR: API request failed for {source} - {e}")
            log_download(f"ERROR: API request failed for {source} - {e}")

            # Fallback logic: If Fanart fails, try TMDB
            if source == "Fanart":
                log_download(f"Retrying {title} with TMDB instead of Fanart.tv.")
                download_backdrop(title, "TMDB", media_type, media_id)
            return

        print(f" API Response: {response}")  # Log the API response

        backdrops = []
    
        if media_type == "movie" and "moviebackground" in response:
            backdrops = [b for b in response["moviebackground"] if b.get("lang") == "none"]
        elif media_type == "tv" and "showbackground" in response:
            backdrops = [b for b in response["showbackground"] if b.get("lang") == "none"]

        # If user enters "all" or leaves it blank, download everything
        if backdrop_limit in [None, "", "all"]:  # Handle None, empty, or "all" cases
            if media_type == "movie":
                limit = len(response.get("moviebackground", [])) if "moviebackground" in response else 0
            else:
                limit = len(response.get("showbackground", [])) if "showbackground" in response else 0
        else:
            try:
                limit = max(1, int(backdrop_limit))  # Ensure at least 1
            except ValueError:
                limit = 1  # Fallback to default if invalid input

        if backdrops:
            # Determine the number of available backdrops
            available_count = len(backdrops)

            # If limit is None, download all available backdrops
            download_count = available_count if limit is None else min(limit, available_count)

            for i, backdrop in enumerate(backdrops[:download_count]):  # Apply limit properly
                backdrop_url = backdrop["url"]

                print(f" Found Backdrop URL: {backdrop_url}")

                # Store all backdrops inside /config/Backdrops/
                file_name = f"{title.replace(' ', '_')}_{source}_{i+1}.jpg"
                save_path = os.path.join(BACKDROP_DIR, file_name)

                print(f" Saving image to: {save_path}")

                try:
                    img_data = requests.get(backdrop_url).content
                    with open(save_path, "wb") as f:
                        f.write(img_data)
                    print(f" Successfully saved: {save_path}")
                    log_download(f"Downloaded {file_name} from {source}")
                except Exception as e:
                    print(f" Error saving image: {e}")
                    log_download(f"Error saving {file_name}: {e}")

        else:
            log_download(f"Fanart.tv did not return backdrops for {title}. Falling back to TMDB.")
            download_backdrop(title, "TMDB", media_type, media_id)

    if response and "backdrops" in response and response["backdrops"]:
        # Determine the number of available backdrops
        available_count = len(response["backdrops"])

        # If limit is None, download all available backdrops
        download_count = available_count if limit is None else min(limit, available_count)

        for i, backdrop in enumerate(response["backdrops"][:download_count]):  # Apply limit properly
            backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop['file_path']}"

            print(f" Found Backdrop URL: {backdrop_url}")

            # Store all backdrops inside /config/Backdrops/
            file_name = f"{title.replace(' ', '_')}_{source}_{i+1}.jpg"
            save_path = os.path.join(BACKDROP_DIR, file_name)

            print(f" Saving image to: {save_path}")

            try:
                img_data = requests.get(backdrop_url).content
                with open(save_path, "wb") as f:
                    f.write(img_data)
                print(f" Successfully saved: {save_path}")
                log_download(f"Downloaded {file_name} from {source}")
            except Exception as e:
                print(f" Error saving image: {e}")
                log_download(f"Error saving {file_name}: {e}")

    else:
        print(f" No backdrops found for {title} on {source}")
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
        "fanart_api": data.get("fanart_api", ""),
        "movies_source": data.get("movies_source", "TMDB"),
        "tvshows_source": data.get("tvshows_source", "TMDB"),
        "backdrop_limit": data.get("backdrop_limit", "10"),
        "run_frequency": data.get("run_frequency", "manual"),
        "schedule_day": data.get("schedule_day", "monday").lower(),
        "schedule_time": data.get("schedule_time", "12:00"),
        "movies_folder": data.get("movies_folder", ""),
        "tvshows_folder": data.get("tvshows_folder", "")
    }
    save_config(config)
    schedule_download()
    return jsonify({"message": "Configuration updated", "config": config})


@app.route('/Backdrops/<filename>')
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

        log_download(f"Scheduled backdrop download set for {config['schedule_day']} at {config['schedule_time']}.")

def run_scheduled_download():
    log_download("Scheduled weekly download initiated.")

    # Extract titles before running the scheduled job
    print("LOG: Running scheduled extraction of titles...")
    extract_titles_from_folders()

    # Verify if extraction worked
    if not os.path.exists(TITLES_FILE):
        print("ERROR: Titles file not found! Retrying extraction...")
        extract_titles_from_folders()
        if not os.path.exists(TITLES_FILE):  # Double-check after retry
            log_download("ERROR: Titles file missing after retry. Aborting scheduled run.")
            return

    with open(TITLES_FILE, "r") as f:
        try:
            titles = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: Corrupted titles.json! Resetting and re-extracting...")
            log_download("ERROR: Corrupted titles.json detected.")
            extract_titles_from_folders()
            with open(TITLES_FILE, "w") as f:
                json.dump([], f)  # Reset titles.json
            return

    if not titles:
        print("ERROR: No titles found for scheduled run. Skipping...")
        log_download("ERROR: No titles found. Skipping scheduled backdrop download.")
        return

    # Process and download backdrops
    for entry in titles[:]:  # Iterate over a copy to allow removal
        title = entry.get("title")
        media_type = entry.get("type")
        media_id = entry.get("id")

        # If ID is missing, fetch from TMDB
        if not media_id:
            tmdb_id = fetch_tmdb_id(title, media_type)
            if tmdb_id:
                entry["id"] = str(tmdb_id)
            else:
                print(f"WARNING: No valid TMDB ID found for {title}. Skipping...")
                log_download(f"WARNING: No valid TMDB ID found for {title}. Skipping...")
                titles.remove(entry)
                continue  # Skip this entry

        source = load_config().get(f"{media_type}s_source", "TMDB")
        print(f"LOG: Processing {title} ({media_type})")
        download_backdrop(title, source, media_type, entry["id"])

    # Save the updated titles list (in case we fetched new TMDB IDs)
    with open(TITLES_FILE, "w") as f:
        json.dump(titles, f, indent=4)

    log_download("Scheduled backdrop download completed.")

import sys

@app.route('/run-now', methods=['POST'])
def run_now():
    try:
        log_path = "/config/logs/backdrop_download.log"
        print(f"LOG: Attempting to write to {log_path}")  
        sys.stdout.flush()  

        with open(log_path, "a") as log_file:
            log_file.write("Manual run initiated.\n")

        print("LOG: Manual run successfully logged.")
        sys.stdout.flush()

        # Extract Titles & IDs from folder names before downloading
        print("LOG: Extracting titles from folders...")
        extract_titles_from_folders()

        # Verify if the extraction worked
        if not os.path.exists(TITLES_FILE):
            print("ERROR: Titles file not found! Retrying extraction...")
            extract_titles_from_folders()
            if not os.path.exists(TITLES_FILE):
                log_download("ERROR: Titles file not found after retry. Aborting manual run.")
                return jsonify({"message": "No titles found even after retry."}), 400

        with open(TITLES_FILE, "r") as f:
            try:
                titles = json.load(f)
            except json.JSONDecodeError:
                print("ERROR: Corrupted titles.json! Resetting and re-extracting...")
                extract_titles_from_folders()
                with open(TITLES_FILE, "w") as f:
                    json.dump([], f)  # Reset titles.json
                return jsonify({"message": "Titles file was corrupted. Reset and extracted again."}), 400

        if not titles:
            print("ERROR: Titles file is empty! Retrying extraction...")
            extract_titles_from_folders()
            with open(TITLES_FILE, "r") as f:
                titles = json.load(f)
            if not titles:
                return jsonify({"message": "No titles found even after reattempt."}), 400

        # Process and download backdrops
        for entry in titles[:]:  # Iterate over a copy to allow removal
            title = entry.get("title")
            media_type = entry.get("type")
            media_id = entry.get("id")

            # If ID is missing, fetch from TMDB
            if not media_id:
                tmdb_id = fetch_tmdb_id(title, media_type)
                if tmdb_id:
                    entry["id"] = str(tmdb_id)
                else:
                    print(f"WARNING: No valid TMDB ID found for {title}. Skipping...")
                    log_download(f"WARNING: No valid TMDB ID found for {title}. Skipping...")
                    titles.remove(entry)
                    continue  # Skip this entry

            source = load_config().get(f"{media_type}s_source", "TMDB")
            print(f"LOG: Processing {title} ({media_type})")
            download_backdrop(title, source, media_type, entry["id"])

        # Save the updated titles list (in case we fetched new TMDB IDs)
        with open(TITLES_FILE, "w") as f:
            json.dump(titles, f, indent=4)

        log_download("Manual backdrop download completed.")
        return jsonify({"message": "Backdrop download completed."})

    except Exception as e:
        print(f"ERROR: Failed to process run-now: {e}")
        log_download(f"ERROR: Failed to process run-now: {e}")
        sys.stdout.flush()
        return jsonify({"message": "Error running manual backdrop download", "error": str(e)}), 500

if __name__ == '__main__':
    schedule_download()
    app.run(host='0.0.0.0', port=8500, debug=True)
