# National Cultural Heritage Management System (HeritageGraph)

A comprehensive Cultural Heritage Management and Preservation Information System built with a **Python FastAPI** backend, **Vanilla HTML/CSS/JavaScript** frontend, and **Neo4j Aura Graph Database**.

---

## 🌐 Live Demo

- **Website**: [https://digital-heritage-system.onrender.com](https://digital-heritage-system.onrender.com/)
- **API Health Check**: [https://digital-heritage-system.onrender.com/api/health](https://digital-heritage-system.onrender.com/api/health)
- **Interactive API Documentation**: [https://digital-heritage-system.onrender.com/docs](https://digital-heritage-system.onrender.com/docs)

> **Note:** The hosted application is deployed on Render's free tier and may spin down during periods of inactivity. Please allow 30–60 seconds for the service to wake up on the first request.

---

## ✨ Key Features

- **Heritage asset management**: Register, search, update preservation statuses, and track historical assets.
- **Conservation project tracking and history**: Manage restoration projects, lifecycle statuses, and asset intervention histories.
- **Funding allocation and utilization analytics**: Real-time budget allocation, expenditure monitoring, remaining balance calculations, and utilization percentages.
- **Digital archives**: Document 3D scans, archival records, metadata, and access permissions linked to heritage assets.
- **Exhibition management and visitor feedback**: Schedule public exhibitions and collect structured visitor ratings and reviews.
- **Interactive dashboard**: High-level system overview with real-time asset counts, active projects, and critical attention alerts.
- **Neo4j graph database and relationship management**: Rich graph-native property modeling and dependency tracking (CONSERVES, ALLOCATED_TO, DOCUMENTED_IN, FEATURED_IN).

---

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, Pydantic
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: Neo4j Aura
- **Driver**: Official Neo4j Python driver
- **Server**: Uvicorn
- **Hosting**: Render

---

## 🏛️ System Architecture

- **Backend**: FastAPI with async lifespan management and Pydantic v2 schemas.
- **Database**: Neo4j Aura (Enterprise Graph Database) using official `neo4j` Python driver with parameterized Cypher queries.
- **Frontend**: Responsive UI (HTML5, CSS3, ES6 JavaScript) featuring interactive dashboard metrics, asset management, conservation tracking, funding analytics, digital archives, and exhibition visitor feedback.
- **Data Access Layer**: Clean repository pattern (`Neo4jHeritageStore`) supporting environment-based switching (`DATABASE_MODE=neo4j` or `DATABASE_MODE=mock`).

---

## 🚀 Quick Start Guide (Windows PowerShell)

### 1. Prerequisites & Virtual Environment
Ensure Python 3.10+ is installed:
```powershell
# Navigate to project directory

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure your Neo4j credentials:
```powershell
Copy-Item .env.example .env
```
Edit `.env` (kept strictly git-ignored):
```ini
DATABASE_MODE=neo4j
NEO4J_URI=neo4j+s://<dbid>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_actual_password_here
NEO4J_DATABASE=neo4j
```

> **Safety Notice:** If `DATABASE_MODE=neo4j` is selected, the application validates connectivity at startup and will fail with a clear, actionable error if credentials or network connectivity fail. It will never silently fall back to mock data.

### 3. Initialize or Migrate Neo4j Database

#### Option A: Initialize a Fresh Neo4j Database
If starting with an empty Neo4j Aura database, run Member 1's initial graph setup script:
- Open Neo4j Aura Query Console.
- Execute the contents of `database/heritage_graph_setup.cypher`.

#### Option B: Upgrade / Harmonize Existing Database
To add constraints for archive/exhibition/feedback/funding IDs and seed the dedicated `(:Funding)` node safely without deleting or overwriting any existing data:
- Inspect and review `database/migration_v2.cypher`.
- Execute the script in the Neo4j Aura Query Console.

---

### 4. Running Automated Tests

Run the full automated test suite (mocked repository tests, mocked API route tests, and live Aura integration tests):
```powershell
.venv\Scripts\python -m pytest tests/ -v
```

---

### 5. Starting the Application

Start the FastAPI application with Uvicorn:
```powershell
.venv\Scripts\uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Web Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative API Documentation (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 📊 Endpoints & Feature Mapping

| Endpoint | Method | Graph Operation / Node | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | GET | `MATCH (n) RETURN count(n)` | System health & live Neo4j connectivity |
| `/api/dashboard/stats` | GET | Aggregates across nodes | Total assets, active projects, archives, exhibitions, attention count |
| `/api/assets` | GET, POST | `(:HeritageAsset)` | List/search assets and create new asset with org link |
| `/api/assets/{id}` | GET, PUT, DELETE | `(:HeritageAsset)` | Retrieve detail, update status, detach delete |
| `/api/conservation/projects` | GET, POST | `(:ConservationProject)-[:CONSERVES]->(:HeritageAsset)` | List & create conservation projects |
| `/api/conservation/history/{id}` | GET | `(:ConservationProject)-[:CONSERVES]->(:HeritageAsset)` | Project history for a specific heritage asset |
| `/api/funding` | GET, POST | `(:Funding)-[:ALLOCATED_TO]->(:ConservationProject)` | Authoritative funding analytics & allocations |
| `/api/archives` | GET, POST | `(:HeritageAsset)-[:DOCUMENTED_IN]->(:DigitalArchive)` | Digital archive media documentation |
| `/api/exhibitions` | GET, POST | `(:HeritageAsset)-[:FEATURED_IN]->(:Exhibition)` | Public exhibitions tracking |
| `/api/exhibitions/feedback` | POST | `(:VisitorFeedback)-[:GIVEN_FOR]->(:Exhibition)` | Submit visitor rating (1-5) and comments |
| `/api/exhibitions/ratings` | GET | Aggregated ratings | Computed exhibition ratings & visitor reviews |

---

## 🔒 Security Best Practices
- `.env` is listed in `.gitignore` and must never be committed or pushed to source control.
- All Cypher operations in `Neo4jHeritageStore` use parameterized variables (`$var`) preventing Cypher injection vulnerabilities.
