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

## 🛠 Installation

### **1️⃣ Create Necessary Folders**
Before running the container, create the required directories for configuration:

```bash
mkdir -p /path/to/Backdrop-Downloader/config /path/to/Backdrop-Downloader/templates
```

This ensures that settings and downloaded images persist across container restarts.

### **2️⃣ Pull the Docker Image**

Once the image is on Docker Hub, you’ll be able to pull it using:

```bash
docker pull vchunkyzv/backdrop-downloader
```

### **3️⃣ Run the Container**

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

### **4️⃣ Access the Web GUI**

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
