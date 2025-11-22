
# 📘 Product Requirements Document (PRD)
# **Bitcoin Node Discovery & Geolocation Heatmap**
### Version 1.0 — February 2025  
### Prepared by: Ruz

---

# 1. 📌 Project Purpose

The purpose of this project is to design and implement a full-stack system that discovers active Bitcoin nodes through the Bitcoin P2P protocol, geolocates them, and visualizes the global distribution of the Bitcoin network using a geographic heatmap.

This project demonstrates:
- Low-level understanding of the Bitcoin P2P protocol  
- Implementation of a network crawler  
- Integration with geolocation services  
- A modern full‑stack pipeline with backend APIs and an interactive frontend  
- Insight into Bitcoin decentralization and global network topology  

---

# 2. 🎯 Project Goals

### Primary Goals
1. Discover and collect active Bitcoin node IP addresses.
2. Identify approximate geographic coordinates for each node.
3. Expose this data through a backend API.
4. Display the results visually using a heatmap on a world map.
5. Build a system that updates regularly and displays near-real-time network state.

### Secondary Goals
- Provide a clean architecture using modular services.
- Implement data validation, rate limiting, and error handling.
- Produce maintainable documentation and a clear data pipeline.

---

# 3. 📡 High‑Level System Overview

```
Bitcoin Network (P2P) 
      ↓
Node Discovery Crawler (Python)
      ↓
SQLite Database (nodes + geolocations)
      ↓
Geolocation Service (ip-api.com)
      ↓
FastAPI Backend (REST API)
      ↓
Next.js Frontend (Google Maps Heatmap)
```

---

# 4. 📥 Functional Requirements

### 4.1 Node Discovery
The system must:
- Resolve Bitcoin DNS seeds.
- Connect to peers using TCP (port 8333).
- Perform Bitcoin P2P version and verack handshake.
- Send getaddr message.
- Parse addr response containing peer IPs.
- Store IPs in the database.

### 4.2 IP Filtering
System must:
- Accept only public IP addresses.
- Reject:
  - Private ranges (10.x.x.x, 192.168.x.x, etc.)
  - Reserved or 0.0.0.0 addresses
  - Localhost entries

### 4.3 Database Management
System must:
- Create and maintain two tables:
  - nodes (ip, first_seen)
  - geolocations (ip, latitude, longitude)
- Prevent duplicates using PRIMARY KEY.

### 4.4 Geolocation
System must:
- Batch IPs in groups of 100 (per API requirements).
- Query ip-api.com batch endpoint.
- Store latitude & longitude.
- Respect rate limits (15 requests/min for free tier).
- Retry on 429.

### 4.5 Backend API
Expose the following endpoints:
- GET /nodes → List of IPs  
- GET /count → Total node count  
- GET /locations → List of lat/lon for heatmap  

### 4.6 Frontend Heatmap
The system must:
- Render global heatmap using Google Maps Heatmap Layer.
- Display node density with color gradients.
- Load data from /locations endpoint.
- Work on desktop and mobile (responsive).

---

# 5. 🧱 Non‑Functional Requirements

### Performance
- Crawler should handle 200+ concurrent connections.
- Must discover 1000+ nodes per run.
- API response time < 50ms for /locations.

### Scalability
- SQLite should support up to 1M IP records.
- Geolocation must avoid API lockout.

### Reliability
- Automatic retries for:
  - Network timeouts  
  - Rate limit blocks  
  - Partial geolocation failures  

### Security
- Do not store personally identifiable information.
- Only public IPs allowed.

### Maintainability
- Clear code structure with separated services:
  - crawler  
  - geolocation  
  - backend  
  - frontend  

---

# 6. 🧩 System Architecture Details

## 6.1 Crawler

### Responsibilities
- Resolve DNS seeds  
- Connect to Bitcoin nodes  
- Perform handshake  
- Send getaddr  
- Parse addr response  
- Store IPs  

### Key Technical Details
- Use asyncio + semaphores for concurrency
- Timeout = 8 seconds
- BFS-style expansion:
  - Seeds → peers → more peers

### Failure Handling

| Scenario | Expected Behavior |
|---------|-------------------|
| Node doesn't respond | Timeout & skip |
| Invalid version packet | Ignore peer |
| Private IP returned | Filter out |
| Duplicate IP | Ignore (DB constraint) |

---

## 6.2 Geolocation Service

### Responsibilities
- Fetch IPs without coordinates  
- Batch into groups of 100  
- Query ip-api.com batch API  
- Parse lat/lon  
- Insert into DB  

### Rate Limit Handling
- If status=success → store  
- If status=fail → skip  
- If HTTP 429 → wait X seconds then retry  

---

## 6.3 Backend API (FastAPI)

### Endpoint Specification

#### GET /nodes
Returns list of discovered IP addresses.  
Example:
```json
["93.184.216.34", "198.51.100.42"]
```

#### GET /count
Returns total number of nodes.  
Example:
```json
{"count": 1420}
```

#### GET /locations
Returns geolocated node positions.  
Example:
```json
[
  {"latitude": 51.5074, "longitude": -0.1278},
  {"latitude": 40.7128, "longitude": -74.0060}
]
```

---

## 6.4 Frontend (Next.js + Google Maps)

### Heatmap Requirements
- Uses Google Maps JavaScript API with heatmap layer
- Converts coordinates into `LatLng` objects
- Adjusts heatmap radius based on zoom level
- Supports dark mode

### User Experience
- Map loads automatically with global scale
- Marker intensity reflects node density
- SSR makes initial load fast

---

# 7. 🧪 Test Cases

## 7.1 Crawler Test Cases

| Test Case | Input | Expected Result |
|----------|--------|-----------------|
| DNS seeds | run resolver | ≥20 IPs retrieved |
| Handshake success | valid peer | version+verack exchanged |
| Handshake fail | closed port | timeout after 8s |
| Addr parsing | valid addr | extract peers correctly |
| IP filtering | private IPs | filtered out |

---

## 7.2 Geolocation Test Cases

| Test | Input | Expected Output |
|------|--------|----------------|
| Batch lookup | 100 IPs | 100 JSON objs |
| Rate limit | >15 req/min | waits correctly |
| Invalid IP | malformed | skip |
| DB write | lat/lon | stored |

---

## 7.3 Backend API Test Cases

| Endpoint | Test | Expected |
|----------|-------|----------|
| /nodes | limit=10 | 10 IPs |
| /count | none | count integer |
| /locations | limit=50 | 50 records |

---

## 7.4 Frontend Test Cases

| Scenario | Expected |
|----------|----------|
| Load map | Heatmap shows correctly |
| Empty DB | No heat points |
| Slow API | Map loads after fetch |
| Zoom in | Radius adjusts |

---

# 8. 📈 Success Metrics

- ≥1000 nodes discovered per crawl  
- ≥90% geolocation success  
- Heatmap loads in <3 seconds  
- API <50ms response time  
- 0 crawler crashes in 3 iterations  

---

# 9. 🔮 Future Enhancements

- Live WebSocket updates  
- Historical time-lapse visualization  
- Node-level details (ISP, country)  
- Multi-chain support  
- ML predictions  
- Docker & CI/CD  

---

# 10. ✔ Acceptance Criteria

The project is considered complete when:

1. Crawler discovers ≥1000 distinct nodes.  
2. Geolocation succeeds for ≥90%.  
3. Backend exposes /nodes, /count, /locations.  
4. Frontend renders heatmap correctly.  
5. Full documentation delivered.  

---

# 📄 End of Document
