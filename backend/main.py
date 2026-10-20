import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
from backend.store import InMemoryHeritageStore, get_store

app = FastAPI(
    title="National Cultural Heritage Management System API",
    description="Backend API supporting the HeritageGraph dashboard, conservation, funding, archives, and exhibitions.",
    version="1.0.0",
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Health & Dashboard Statistics
# -----------------------------------------------------------------------------
@app.get("/api/health", tags=["System"])
def get_health(store: InMemoryHeritageStore = Depends(get_store)):
    """Health check endpoint confirming backend service status."""
    return store.get_health()


@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(store: InMemoryHeritageStore = Depends(get_store)):
    """Retrieve summary counts for the dashboard overview cards."""
    return store.get_dashboard_stats()


# -----------------------------------------------------------------------------
# Heritage Assets
# -----------------------------------------------------------------------------
@app.get("/api/assets", response_model=List[AssetResponse], tags=["Assets"])
def list_assets(
    search: Optional[str] = Query(None, description="Search term for name, ID, or location"),
    store: InMemoryHeritageStore = Depends(get_store),
):
    """List all registered heritage assets, with optional keyword search."""
    return store.get_assets(search=search)


@app.get("/api/assets/{asset_id}", response_model=AssetResponse, tags=["Assets"])
def get_asset_detail(asset_id: str, store: InMemoryHeritageStore = Depends(get_store)):
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
    store: InMemoryHeritageStore = Depends(get_store),
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
    store: InMemoryHeritageStore = Depends(get_store),
):
    """Update the preservation status of an existing heritage asset."""
    try:
        return store.update_asset_status(asset_id, update_data)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/api/assets/{asset_id}", tags=["Assets"])
def delete_asset(asset_id: str, store: InMemoryHeritageStore = Depends(get_store)):
    """Delete a heritage asset by ID."""
    try:
        deleted = store.delete_asset(asset_id)
        return {"message": f"Asset '{asset_id}' deleted successfully.", "asset": deleted}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Conservation Projects
# -----------------------------------------------------------------------------
@app.get(
    "/api/conservation/projects",
    response_model=List[ConservationProjectResponse],
    tags=["Conservation"],
)
def list_conservation_projects(store: InMemoryHeritageStore = Depends(get_store)):
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
    store: InMemoryHeritageStore = Depends(get_store),
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
    store: InMemoryHeritageStore = Depends(get_store),
):
    """Fetch conservation/restoration history for a specific heritage asset."""
    try:
        return store.get_restoration_history(asset_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Funding Management
# -----------------------------------------------------------------------------
@app.get("/api/funding", response_model=FundingReportResponse, tags=["Funding"])
def get_funding_report(store: InMemoryHeritageStore = Depends(get_store)):
    """Retrieve funding allocations, expenditures, remaining balances, and calculated summary metrics."""
    return store.get_funding_report()


@app.post(
    "/api/funding",
    status_code=status.HTTP_201_CREATED,
    tags=["Funding"],
)
def create_funding_allocation(
    funding_data: FundingCreate,
    store: InMemoryHeritageStore = Depends(get_store),
):
    """Allocate or record project funding. Validates funding ID uniqueness and associated project existence."""
    try:
        record = store.add_funding(funding_data)
        return {"message": "Funding allocated successfully.", "funding": record}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------------------------------------------------------
# Digital Archives
# -----------------------------------------------------------------------------
@app.get("/api/archives", response_model=List[ArchiveResponse], tags=["Archives"])
def list_archives(
    query: Optional[str] = Query(None, description="Search term for title, ID, or asset"),
    store: InMemoryHeritageStore = Depends(get_store),
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
    store: InMemoryHeritageStore = Depends(get_store),
):
    """Register a new digital archive record. Validates archive ID and associated asset existence."""
    try:
        return store.add_archive(archive_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------------------------------------------------------
# Exhibitions & Visitor Feedback
# -----------------------------------------------------------------------------
@app.get(
    "/api/exhibitions",
    response_model=List[ExhibitionResponse],
    tags=["Exhibitions"],
)
def list_exhibitions(store: InMemoryHeritageStore = Depends(get_store)):
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
    store: InMemoryHeritageStore = Depends(get_store),
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
    store: InMemoryHeritageStore = Depends(get_store),
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
def get_exhibition_ratings_summary(store: InMemoryHeritageStore = Depends(get_store)):
    """Retrieve calculated average ratings, feedback counts, and comments for all exhibitions."""
    return store.get_exhibition_ratings()


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

