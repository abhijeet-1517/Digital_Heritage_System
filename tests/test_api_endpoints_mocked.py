import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from backend.main import app, get_store
from backend.neo4j_store import Neo4jHeritageStore
from backend.models import (
    AssetResponse,
    ConservationProjectResponse,
    FundingReportResponse,
    FundingSummary,
    ArchiveResponse,
    ExhibitionResponse,
    FeedbackResponse,
    ExhibitionRatingSummary,
    DashboardStats,
)


@pytest.fixture
def mock_neo4j_store():
    store = MagicMock(spec=Neo4jHeritageStore)

    # Health
    store.get_health.return_value = {
        "status": "healthy",
        "database_mode": "neo4j",
        "connected": True,
        "node_count": 17,
    }

    # Dashboard Stats
    store.get_dashboard_stats.return_value = DashboardStats(
        total_assets=10,
        active_projects=1,
        total_archives=1,
        current_exhibitions=1,
        assets_needing_attention=2,
    )

    # Assets
    store.get_assets.return_value = [
        AssetResponse(
            asset_id="h001",
            name="Brihadisvara Temple",
            location="Thanjavur, Tamil Nadu",
            period="Chola period",
            preservation_status="Maintained",
            description="Important example of Chola architecture",
        )
    ]
    store.get_asset.return_value = AssetResponse(
        asset_id="h001",
        name="Brihadisvara Temple",
        location="Thanjavur, Tamil Nadu",
        period="Chola period",
        preservation_status="Maintained",
        description="Important example of Chola architecture",
    )

    # Projects
    store.get_projects.return_value = [
        ConservationProjectResponse(
            project_id="cp001",
            project_name="Heritage Restoration Project",
            asset_id="h001",
            budget=500000.0,
            status="Ongoing",
        )
    ]
    store.get_restoration_history.return_value = [
        ConservationProjectResponse(
            project_id="cp001",
            project_name="Heritage Restoration Project",
            asset_id="h001",
            budget=500000.0,
            status="Ongoing",
        )
    ]

    # Funding
    store.get_funding_report.return_value = FundingReportResponse(
        summary=FundingSummary(
            allocated=500000.0,
            utilized=150000.0,
            remaining=350000.0,
            percentage="30.0%",
        ),
        records=[],
    )

    # Archives
    store.get_archives.return_value = [
        ArchiveResponse(
            archive_id="da001",
            title="3D Scan",
            asset_id="h001",
            file_reference="Document Reference",
            access_level="Public",
        )
    ]

    # Exhibitions
    store.get_exhibitions.return_value = [
        ExhibitionResponse(
            exhibition_id="ex001",
            name="Indian Heritage Exhibition",
            start_date="2024-01-01",
            end_date="2024-12-31",
            status="Current",
            asset_id="h001",
        )
    ]

    # Feedback
    store.add_feedback.return_value = FeedbackResponse(
        id=1,
        exhibition_id="ex001",
        rating=5,
        comment="Great!",
    )
    store.get_exhibition_ratings.return_value = [
        ExhibitionRatingSummary(
            exhibition_id="ex001",
            name="Indian Heritage Exhibition",
            average_rating=5.0,
            feedback_count=1,
            comments=["Great!"],
        )
    ]

    # Deletion mock responses
    store.delete_asset.return_value = {"asset_id": "h001", "name": "Brihadisvara Temple"}
    store.delete_project.return_value = {"project_id": "cp001", "project_name": "Heritage Restoration Project"}
    store.delete_funding.return_value = {"funding_id": "fd001", "project_id": "cp001"}
    store.delete_archive.return_value = {"archive_id": "da001", "title": "3D Scan"}
    store.delete_exhibition.return_value = {"exhibition_id": "ex001", "name": "Indian Heritage Exhibition"}

    return store



@pytest.fixture
def client(mock_neo4j_store):
    app.dependency_overrides[get_store] = lambda: mock_neo4j_store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_mode"] == "neo4j"
    assert data["connected"] is True


def test_api_dashboard_stats(client):
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_assets"] == 10
    assert data["active_projects"] == 1


def test_api_assets_list(client):
    res = client.get("/api/assets")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["asset_id"] == "h001"


def test_api_conservation_projects(client):
    res = client.get("/api/conservation/projects")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["project_id"] == "cp001"


def test_api_funding_report(client):
    res = client.get("/api/funding")
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["allocated"] == 500000.0


def test_api_archives(client):
    res = client.get("/api/archives")
    assert res.status_code == 200
    data = res.json()
    assert data[0]["archive_id"] == "da001"


def test_api_exhibitions(client):
    res = client.get("/api/exhibitions")
    assert res.status_code == 200
    data = res.json()
    assert data[0]["exhibition_id"] == "ex001"


def test_api_feedback_submission(client):
    payload = {"exhibition_id": "ex001", "rating": 5, "comment": "Great!"}
    res = client.post("/api/exhibitions/feedback", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["rating"] == 5
    assert data["exhibition_id"] == "ex001"


def test_api_delete_asset(client):
    res = client.delete("/api/assets/h001")
    assert res.status_code == 200
    data = res.json()
    assert "deleted successfully" in data["message"]
    assert data["asset"]["asset_id"] == "h001"


def test_api_delete_conservation_project(client):
    res = client.delete("/api/conservation/projects/cp001")
    assert res.status_code == 200
    data = res.json()
    assert "deleted successfully" in data["message"]
    assert data["project"]["project_id"] == "cp001"


def test_api_delete_funding(client):
    res = client.delete("/api/funding/fd001")
    assert res.status_code == 200
    data = res.json()
    assert "deleted successfully" in data["message"]
    assert data["funding"]["funding_id"] == "fd001"


def test_api_delete_archive(client):
    res = client.delete("/api/archives/da001")
    assert res.status_code == 200
    data = res.json()
    assert "deleted successfully" in data["message"]
    assert data["archive"]["archive_id"] == "da001"


def test_api_delete_exhibition(client):
    res = client.delete("/api/exhibitions/ex001")
    assert res.status_code == 200
    data = res.json()
    assert "deleted successfully" in data["message"]
    assert data["exhibition"]["exhibition_id"] == "ex001"

