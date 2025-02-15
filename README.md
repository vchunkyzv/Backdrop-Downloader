# Backdrop Downloader

## 📌 Overview

Backdrop Downloader is a web-based tool that automatically fetches and downloads **backdrops** (posters, wallpapers) for your **movies and TV shows** stored on a NAS or local drive. It supports **TMDB, TVDB, and Fanart.tv**, allowing users to mix and match sources.

The tool runs inside a **Docker container** and provides a **web-based GUI** accessible from any device on the network.

## 🚀 Features

✔ **Custom Folder Parsing** – Detects TMDB/TVDB IDs from user-defined folder naming structures\
✔ **Supports TMDB, TVDB & Fanart.tv** – Choose where to fetch backdrops from\
✔ **Web-Based GUI** – Easily control the tool from a browser (`http://NAS_IP:8500`)\
✔ **Manual Input for Backdrop Limits** – Enter the number of backdrops to download (or select "All")\
✔ **Automatic Organization** – Saves backdrops in structured folders inside the Docker container\
✔ **Runs on Docker** – Lightweight, easy to deploy

## 👤 Folder Structure

Once downloaded, backdrops are saved in:

```
/config/
├── settings.conf  # Stores user preferences & API keys
├── Backdrops/
│   ├── Movies/       # Contains movie-specific backdrops
│   │   ├── [Movie Name (Year)]/
│   │   │   ├── backdrop1.jpg
│   │   │   ├── backdrop2.jpg
│   ├── TV Shows/     # Contains TV show-specific backdrops
│   │   ├── [TV Show Name (Year)]/
│   │   │   ├── background1.jpg
│   │   │   ├── background2.jpg
```

## 🛠 Installation

### **1️⃣ Pull the Docker Image (Coming Soon)**

Once the image is on Docker Hub, you’ll be able to pull it using:

```bash
docker pull vchunkyzv/backdrop-downloader
```

### **2️⃣ Run the Container**

Use the following command to start the container:

```bash
docker run -d \
  --name=backdrop-downloader \
  -p 8500:8500 \
  -v /path/to/movies:/movies \
  -v /path/to/tvshows:/tvshows \
  -v /path/to/config:/config \
  vchunkyzv/backdrop-downloader
```

💡 Replace `/path/to/movies` and `/path/to/tvshows` with your actual movie & TV show source folders.\
💡 Replace `/path/to/config` with where you want the configuration to be stored.

### **3️⃣ Access the Web GUI**

Once running, open your browser and go to:

```
http://NAS_IP:8500
```

Here, you can enter your API keys, select sources, and start downloading backdrops! 🎮

## 💜 License

This project is licensed under the **MIT License**.

## 📢 Contributions

Contributions, feature requests, and bug reports are welcome! Open an issue or fork the repository.

---
