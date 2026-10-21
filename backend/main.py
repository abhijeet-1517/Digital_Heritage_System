import os
from contextlib import asynccontextmanager
from typing import List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database import init_neo4j_driver, close_neo4j_driver, get_neo4j_driver
from backend.models import (
    AssetCreate,
    AssetResponse,
    AssetStatusUpdate,
    ConservationProjectCreate,
    ConservationProjectResponse,
    FundingCreate,
    FundingReportResponse,
    ArchiveCreate,
    ArchiveResponse,
    ExhibitionCreate,
    ExhibitionResponse,
    FeedbackCreate,
    FeedbackResponse,
    ExhibitionRatingSummary,
    DashboardStats,
)
from backend.store import InMemoryHeritageStore, store as in_memory_store
from backend.neo4j_store import Neo4jHeritageStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup
    if settings.DATABASE_MODE == "neo4j":
        # Raises RuntimeError if connection fails, preventing silent fallback
        init_neo4j_driver()
    yield
    # Shutdown
    close_neo4j_driver()


app = FastAPI(
    title="National Cultural Heritage Management System API",
    description="Backend API supporting the HeritageGraph dashboard, conservation, funding, archives, and exhibitions.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_store() -> Union[Neo4jHeritageStore, InMemoryHeritageStore]:
    """
    Dependency injection for data repository layer.
    Strictly checks DATABASE_MODE:
    - If 'neo4j', connects to Neo4j Aura; fails if driver is not connected.
    - If 'mock', uses in-memory store.
    """
    if settings.DATABASE_MODE == "neo4j":
        driver = get_neo4j_driver()
        if not driver:
            # Attempt to re-initialize or raise error
            driver = init_neo4j_driver()
        return Neo4jHeritageStore(driver=driver, database=settings.NEO4J_DATABASE)
    return in_memory_store


# -----------------------------------------------------------------------------
# Health & Dashboard Statistics
# -----------------------------------------------------------------------------
@app.get("/api/health", tags=["System"])
def get_health(store=Depends(get_store)):
    """Health check endpoint confirming backend service and database status."""
    return store.get_health()


@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(store=Depends(get_store)):
    """Retrieve summary counts for the dashboard overview cards."""
    return store.get_dashboard_stats()


# -----------------------------------------------------------------------------
# Heritage Assets
# -----------------------------------------------------------------------------
@app.get("/api/assets", response_model=List[AssetResponse], tags=["Assets"])
def list_assets(
    search: Optional[str] = Query(None, description="Search term for name, ID, or location"),
    store=Depends(get_store),
):
    """List all registered heritage assets, with optional keyword search."""
    return store.get_assets(search=search)


@app.get("/api/assets/{asset_id}", response_model=AssetResponse, tags=["Assets"])
def get_asset_detail(asset_id: str, store=Depends(get_store)):
    """Fetch details for a single heritage asset by ID."""
    asset = store.get_asset(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID '{asset_id}' not found.",
        )
    return asset


@app.post(
    "/api/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Assets"],
)
def create_asset(
    asset_data: AssetCreate,
    store=Depends(get_store),
):
    """Register a new cultural heritage asset. Validates against duplicate IDs."""
    try:
        return store.add_asset(asset_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/api/assets/{asset_id}", response_model=AssetResponse, tags=["Assets"])
def update_asset_preservation_status(
    asset_id: str,
    update_data: AssetStatusUpdate,
    store=Depends(get_store),
):
    """Update the preservation status of an existing heritage asset."""
    try:
        return store.update_asset_status(asset_id, update_data)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/api/assets/{asset_id}", tags=["Assets"])
def delete_asset(asset_id: str, store=Depends(get_store)):
    """Delete a heritage asset by ID."""
    try:
        deleted = store.delete_asset(asset_id)
        return {"message": f"Asset '{asset_id}' deleted successfully.", "asset": deleted}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



# -----------------------------------------------------------------------------
# Conservation Projects
# -----------------------------------------------------------------------------
@app.get(
    "/api/conservation/projects",
    response_model=List[ConservationProjectResponse],
    tags=["Conservation"],
)
def list_conservation_projects(store=Depends(get_store)):
    """List all conservation and restoration projects."""
    return store.get_projects()


@app.post(
    "/api/conservation/projects",
    response_model=ConservationProjectResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Conservation"],
)
def create_conservation_project(
    project_data: ConservationProjectCreate,
    store=Depends(get_store),
):
    """Create a new conservation project. Validates project ID uniqueness and associated asset existence."""
    try:
        return store.add_project(project_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get(
    "/api/conservation/history/{asset_id}",
    response_model=List[ConservationProjectResponse],
    tags=["Conservation"],
)
def get_restoration_history_by_asset(
    asset_id: str,
    store=Depends(get_store),
):
    """Fetch conservation/restoration history for a specific heritage asset."""
    try:
        return store.get_restoration_history(asset_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/api/conservation/projects/{project_id}", tags=["Conservation"])
def delete_conservation_project(project_id: str, store=Depends(get_store)):
    """Delete a conservation project by ID."""
    try:
        deleted = store.delete_project(project_id)
        return {"message": f"Conservation project '{project_id}' deleted successfully.", "project": deleted}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



# -----------------------------------------------------------------------------
# Funding Management
# -----------------------------------------------------------------------------
@app.get("/api/funding", response_model=FundingReportResponse, tags=["Funding"])
def get_funding_report(store=Depends(get_store)):
    """Retrieve funding allocations, expenditures, remaining balances, and calculated summary metrics."""
    return store.get_funding_report()


@app.post(
    "/api/funding",
    status_code=status.HTTP_201_CREATED,
    tags=["Funding"],
)
def create_funding_allocation(
    funding_data: FundingCreate,
    store=Depends(get_store),
):
    """Allocate or record project funding. Validates funding ID uniqueness and associated project existence."""
    try:
        record = store.add_funding(funding_data)
        return {"message": "Funding allocated successfully.", "funding": record}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete("/api/funding/{funding_id}", tags=["Funding"])
def delete_funding_record(funding_id: str, store=Depends(get_store)):
    """Delete a funding record by ID."""
    try:
        deleted = store.delete_funding(funding_id)
        return {"message": f"Funding record '{funding_id}' deleted successfully.", "funding": deleted}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



# -----------------------------------------------------------------------------
# Digital Archives
# -----------------------------------------------------------------------------
@app.get("/api/archives", response_model=List[ArchiveResponse], tags=["Archives"])
def list_archives(
    query: Optional[str] = Query(None, description="Search term for title, ID, or asset"),
    store=Depends(get_store),
):
    """List all registered digital archive records with optional search filter."""
    return store.get_archives(query=query)


@app.post(
    "/api/archives",
    response_model=ArchiveResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Archives"],
)
def register_archive_document(
    archive_data: ArchiveCreate,
    store=Depends(get_store),
):
    """Register a new digital archive record. Validates archive ID and associated asset existence."""
    try:
        return store.add_archive(archive_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete("/api/archives/{archive_id}", tags=["Archives"])
def delete_archive_document(archive_id: str, store=Depends(get_store)):
    """Delete a digital archive record by ID."""
    try:
        deleted = store.delete_archive(archive_id)
        return {"message": f"Archive document '{archive_id}' deleted successfully.", "archive": deleted}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



# -----------------------------------------------------------------------------
# Exhibitions & Visitor Feedback
# -----------------------------------------------------------------------------
@app.get(
    "/api/exhibitions",
    response_model=List[ExhibitionResponse],
    tags=["Exhibitions"],
)
def list_exhibitions(store=Depends(get_store)):
    """List all scheduled, current, and past exhibitions."""
    return store.get_exhibitions()


@app.post(
    "/api/exhibitions",
    response_model=ExhibitionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Exhibitions"],
)
def create_exhibition(
    exhibition_data: ExhibitionCreate,
    store=Depends(get_store),
):
    """Create a new exhibition. Validates exhibition ID and associated asset existence."""
    try:
        return store.add_exhibition(exhibition_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post(
    "/api/exhibitions/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Exhibitions"],
)
def submit_visitor_feedback(
    feedback_data: FeedbackCreate,
    store=Depends(get_store),
):
    """Submit visitor rating (1-5) and comments for an exhibition."""
    try:
        return store.add_feedback(feedback_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get(
    "/api/exhibitions/ratings",
    response_model=List[ExhibitionRatingSummary],
    tags=["Exhibitions"],
)
def get_exhibition_ratings_summary(store=Depends(get_store)):
    """Retrieve calculated average ratings, feedback counts, and comments for all exhibitions."""
    return store.get_exhibition_ratings()


@app.delete("/api/exhibitions/{exhibition_id}", tags=["Exhibitions"])
def delete_exhibition_record(exhibition_id: str, store=Depends(get_store)):
    """Delete an exhibition by ID."""
    try:
        deleted = store.delete_exhibition(exhibition_id)
        return {"message": f"Exhibition '{exhibition_id}' deleted successfully.", "exhibition": deleted}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



# -----------------------------------------------------------------------------
# Frontend Static Files & Page Routes (Registered AFTER all /api routes)
# -----------------------------------------------------------------------------
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

if os.path.exists(frontend_path):
    @app.get("/", include_in_schema=False)
    def serve_root():
        """Serve index.html at root."""
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/assets", include_in_schema=False)
    def serve_assets_shortcut():
        return FileResponse(os.path.join(frontend_path, "assets.html"))

    @app.get("/conservation", include_in_schema=False)
    def serve_conservation_shortcut():
        return FileResponse(os.path.join(frontend_path, "conservation.html"))

    @app.get("/funding", include_in_schema=False)
    def serve_funding_shortcut():
        return FileResponse(os.path.join(frontend_path, "funding.html"))

    @app.get("/archives", include_in_schema=False)
    def serve_archives_shortcut():
        return FileResponse(os.path.join(frontend_path, "archives.html"))

    @app.get("/exhibitions", include_in_schema=False)
    def serve_exhibitions_shortcut():
        return FileResponse(os.path.join(frontend_path, "exhibitions.html"))

    # Mount static assets (CSS, JS, images, and HTML files) at /
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
