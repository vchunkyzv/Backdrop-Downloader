# Backdrop Downloader

## 📌 Overview

Backdrop Downloader is a web-based tool that automatically fetches and downloads **backdrops** (posters, wallpapers) for your **movies and TV shows** stored on a NAS, local drive, or selected from a **Trakt list**. It supports **TMDB and Fanart.tv**, allowing users to mix and match sources.

The tool runs inside a **Docker container** and provides a **web-based GUI** accessible from any device on the network.

## 🚀 Features

✔ **Fetch from Local Folders or Trakt Lists** – Pull movies/TV shows from your devices or directly from a Trakt list.\
✔ **Dynamic TMDB ID Resolution** – If TMDB IDs are missing, they will be fetched using the TMDB API.\
✔ **Supports TMDB & Fanart.tv** – Fetch backdrops using TMDB IDs (Fanart.tv uses TMDB IDs for movies and TVDB IDs for TV shows).\
✔ **Web-Based GUI** – Easily control the tool from a browser (`http://NAS_IP:8500`).\
✔ **Manual Input for Backdrop Limits** – Enter the number of backdrops to download (or select "All").\
✔ **Automatic Organization** – Saves backdrops in structured folders inside the Docker container.\
✔ **Supports "No Language" Backdrops** – Ensures that only backdrops from TMDB’s **"No Languages"** section are downloaded.\
✔ **Runs on Docker** – Lightweight, easy to deploy.\
✔ **Trakt API or TMDB API for ID Resolution** – Users can choose to resolve missing TMDB IDs using either Trakt API or TMDB API.

## 🛠 Installation

### **1⃣ Create Necessary Folders**
Before running the container, create the required directories for configuration:

```bash
mkdir -p /path/to/Backdrop-Downloader/config /path/to/Backdrop-Downloader/templates
```

This ensures that settings and downloaded images persist across container restarts.

### **2⃣ Pull the Docker Image**

Once the image is on Docker Hub, you’ll be able to pull it using:

```bash
docker pull vchunkyzv/backdrop-downloader
```

### **3⃣ Run the Container**

Use the following command to start the container:

```bash
docker run -d \
   --name=backdrop-downloader \
   -p 8500:8500 \
   -v /path/to/movies:/movies:ro \
   -v /path/to/tvshows:/tvshows:ro \
   -v /path/to/Backdrop-Downloader/config:/config \
   vchunkyzv/backdrop-downloader
```

💡 Replace `/path/to/movies` and `/path/to/tvshows` with your actual movie & TV show source folders.\
💡 Replace `/path/to/Backdrop-Downloader/config` with where you want the configuration to be stored.

### **4⃣ Access the Web GUI**

Once running, open your browser and go to:

```
http://NAS_IP:8500
```

Here, you can enter your API keys, select sources, and start downloading backdrops! 🎮

## 🔧 Configuration Options

Once inside the web UI, you can choose from:

- **Source Selection**:  
  - `My Devices` → Uses local folders (`/movies` and `/tvshows`).  
  - `Trakt List` → Uses Trakt list URLs (Movies & TV Shows).  

- **Trakt API Usage**:
  - If selected, fetches TMDB IDs directly from Trakt.
  - If **not** selected, titles from Trakt will be resolved using the **TMDB API**.

- **Backdrop Sources**:
  - **TMDB** → Uses TMDB API for movies & TV shows.
  - **Fanart.tv** → Uses TMDB IDs for movies, TVDB IDs for TV shows.

- **Backdrop Limits**:
  - You can specify how many backdrops per title or choose **"All"**.

## 💜 License

This project is licensed under the **MIT License**.

## 💚 Contributions

Contributions, feature requests, and bug reports are welcome! Open an issue or fork the repository.
