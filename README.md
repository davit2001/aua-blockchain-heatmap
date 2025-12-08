## About Project

This project visualizes the global distribution of Bitcoin nodes by discovering peer nodes through network crawling, geolocating them, and displaying their geographic distribution on an interactive heatmap. The application demonstrates the decentralized nature of the Bitcoin network and provides insights into where nodes are concentrated worldwide.

## Getting Started

To run a project locally we have so many options which you can choose from however the easiest way to run this project frontend, backend and database is using Docker.
#### Prerequisites
Make sure you have the following installed on your machine:
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Run a docker with Docker Compose
```
docker-compose up --build
```
or if you are using Docker Compose V2
```
docker compose up -d --build
```

## Run a project with shell scripts
Alternatively, you can run the project using shell scripts provided in the `scripts` directory.
Make sure you have Python 3.10+ installed on your machine.
Create a .env file in the root directory and add the following environment variables and put your Google Maps API key:
```
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY
```

#### 1. Install dependencies
```bash
pip install -r src/scripts/requirements.txt
```
#### 2. Populate the database
Run the crawler to populate the SQLite database with Bitcoin node data:
```bash
chmod +x shell-scripts/popuplate_database.sh 
shell-scripts/popuplate_database.sh  
````

#### 3. Start the FastAPI server
Run the server to expose the Bitcoin nodes API:
```bash
chmod +x shell-scripts/start_backend.sh
shell-scripts/start_backend.sh
```

#### 4. Start the frontend
Run the frontend to access the web interface:
```bash
chmod +x shell-scripts/start_frontend.sh
shell-scripts/start_frontend.sh
```

#### 5. Access the application
Open your web browser and navigate to:
```
http://localhost:3000
```

## 🌐 Bitcoin Nodes API

This project includes a lightweight **FastAPI** service that exposes the collected Bitcoin node IPs and statistics from the local SQLite database (`nodes.db`).  
It allows the frontend or other tools to easily fetch live node data.


### Setup & Run

#### 1. Install dependencies

Make sure you have Python 3.10+ installed, then install the required packages:

```bash
pip install fastapi aiosqlite uvicorn
```

#### 2. Start the API server
From the project root, run:
```bash
cd src/scripts
uvicorn app:app --host 0.0.0.0 --port 8000
```
This will start the API at:
http://localhost:8000


### Endpoint Reference

#### 1️⃣ GET /nodes
Fetch a list of discovered Bitcoin node IP addresses.

**URL:** `http://localhost:8000/nodes`

**Method:** `GET`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | `integer` | No | `100` | Maximum number of node IPs to return |


#### 2️⃣ GET /count
Fetch the total number of nodes currently stored in the database.

**URL:** `http://localhost:8000/count`

**Method:** `GET`

**Query Parameters:** `None`

### Notes
- The API reads directly from nodes.db, which is continuously updated by the Bitcoin crawler (crawler.py).
- Both endpoints are asynchronous and optimized for high performance.
- CORS is enabled, so you can easily access the API from your Next.js or React frontend.
---


#### 3️⃣ GET /locations
Fetch a list of geolocation coordinates (`latitude` and `longitude`) for Bitcoin nodes.

**URL:** `http://localhost:8000/locations`

**Method:** `GET`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | `integer` | No | All | Maximum number of location entries to return. If not provided, all rows will be returned |

**Response Example:**
```json
[
  [40.7128, -74.0060],
  [51.5074, -0.1278]
]
