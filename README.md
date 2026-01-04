# Colorchef Server

The Colorchef Server is a dedicated backend service built with FastAPI designed to manage movie data ingestion, color palette extraction, and content synchronization for the Colorchef discovery engine. This server is part of a decoupled "Ghost" architecture, intended for local execution to maintain high security and zero-cost infrastructure.

## Architecture

Colorchef utilizes a multi-layer decoupled architecture:
- **Local Admin Server (Python):** Ingests movie data, extracts aesthetic color palettes, and manages local files.
- **Data Repository (Git):** Serves as a version-controlled database and global CDN for static JSON assets [Colorchef-data](https://github.com/sidchigo/colorchef-data).
- **Frontend (Next.js):** Consumes data from the Git repository using Incremental Static Regeneration (ISR) [Colorchef-next](https://github.com/sidchigo/colorchef-next).

## Core Features

- **Automated Metadata Ingestion:** Fetches movie details and high-resolution backdrops via the TMDB API.
- **Palette Extraction:** Generates hex-based color palettes from movie backdrops using custom clustering algorithms.
- **Dynamic Tagging:** Maps raw plot keywords to a curated niche map for improved film categorization.
- **Git-as-a-Database:** Automatically rebuilds the global index and configuration files for deployment to the data repository.
- **Content Management:** Supports soft and hard deletion workflows with immediate revalidation triggers.

## Technical Stack

- **Framework:** FastAPI
- **HTTP Client:** HTTPX (Asynchronous)
- **Data Format:** JSON
- **Version Control:** Git

## Installation

### Prerequisites
- Python 3.9 or higher
- Access to a local clone of the data repository
- TMDB API Key

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/sidchigo/colorchef-server.git
   cd colorchef-server
   ```
2. Initialize virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in a `.env` file:
   ```env
   DATA_REPO_PATH=path/to/local/data-repo
   ```

## Usage

Start the local server:
```bash
pipenv run start
```

### API Endpoints (v1)
- `POST /admin/cinema/sync`: Ingest new movies and extract palettes.
- `PATCH /admin/cinema/{slug}/archive`: Soft delete a movie from the public index.
- `DELETE /admin/cinema/{slug}/permanent`: Physically remove movie data.
- `GET /admin/cinema/index.json`: Retrieve the local movie index.

## Security Note

This server is strictly intended for local or private environment use. The "Ghost" architecture ensures that no write-capable backend is exposed to the public internet, mitigating typical web attack vectors.
