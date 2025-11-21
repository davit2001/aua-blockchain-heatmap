# Bitcoin Node Heatmap - AUA Blockchain Project

This is a [Next.js](https://nextjs.org) project that visualizes Bitcoin network nodes on a world heatmap, demonstrating real P2P network topology through crawling and geolocation.

## 🎉 Node.js Version Update Complete

**✅ Successfully upgraded to Node.js v20.19.1**
- Previous version: v20.8.0 (broken due to missing ICU libraries)
- Current version: v20.19.1 (exceeds requirement of >=20.9.0)
- Installation method: Direct binary installation to `~/local/node`
- npm version: 10.8.2

### Node.js Setup
The project now uses a local Node.js installation at `~/local/node/bin`. This has been added to your `~/.zshrc` for permanent use:

```bash
export PATH="$HOME/local/node/bin:$PATH"
```

To verify your setup:
```bash
node --version  # Should show v20.19.1
npm --version   # Should show 10.8.2
```

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.




##  Bitcoin Node Crawler (Initial Setup)

This is an **initial version** of the Bitcoin network crawler.

It connects to peers using the Bitcoin P2P protocol, discovers new nodes,  
and stores them in a local SQLite database (`nodes.db`).

###  Requirements
- Python 3.8+
- Dependencies: `aiosqlite`
```bash
pip install aiosqlite
```

###  How to Run

1. Go to the script folder:
```bash
cd src/scripts
```
2. Run the crawler:
```bash
python crawler.py
```

You can optionally specify seeds, concurrency, and iterations:
```bash
python crawler.py --seeds seed.bitcoin.sipa.be --iterations 3 --concurrency 200
```

### Output
A SQLite database nodes.db is created in the same folder.  
The database contains a table nodes with discovered IPs.


### Check the results
To see the first 10 nodes:
```bash
sqlite3 nodes.db "SELECT * FROM nodes LIMIT 10;"
```
To count all nodes:
```bash
sqlite3 nodes.db "SELECT COUNT(*) FROM nodes;"
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
