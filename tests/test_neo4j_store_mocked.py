import pytest
from unittest.mock import MagicMock
from backend.neo4j_store import Neo4jHeritageStore
from backend.models import (
    AssetCreate,
    AssetStatusUpdate,
    ConservationProjectCreate,
    FundingCreate,
    ArchiveCreate,
    ExhibitionCreate,
    FeedbackCreate,
)


class DummyRecord:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, item):
        return self._data[item]

    def get(self, item, default=None):
        return self._data.get(item, default)


class DummyResult:
    def __init__(self, records):
        self._records = records

    def single(self):
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


@pytest.fixture
def mock_driver():
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    return driver, session


def test_neo4j_store_health(mock_driver):
    driver, session = mock_driver
    session.run.return_value.single.return_value = {"count": 17}

    store = Neo4jHeritageStore(driver=driver)
    health = store.get_health()

    assert health["status"] == "healthy"
    assert health["database_mode"] == "neo4j"
    assert health["connected"] is True
    assert health["node_count"] == 17


def test_neo4j_store_dashboard_stats(mock_driver):
    driver, session = mock_driver
    stats_record = {
        "total_assets": 10,
        "active_projects": 1,
        "total_archives": 1,
        "current_exhibitions": 1,
        "assets_needing_attention": 2,
    }
    session.run.return_value.single.return_value = stats_record

    store = Neo4jHeritageStore(driver=driver)
    stats = store.get_dashboard_stats()

    assert stats.total_assets == 10
    assert stats.active_projects == 1
    assert stats.assets_needing_attention == 2


def test_neo4j_store_get_assets(mock_driver):
    driver, session = mock_driver
    asset_node = {
        "asset_id": "h001",
        "name": "Brihadisvara Temple",
        "location": "Thanjavur, Tamil Nadu",
        "period": "Chola period",
        "preservation_status": "Maintained",
        "historical_significance": "Chola architecture",
    }
    session.run.return_value = DummyResult([{"a": asset_node}])

    store = Neo4jHeritageStore(driver=driver)
    assets = store.get_assets()

    assert len(assets) == 1
    assert assets[0].asset_id == "h001"
    assert assets[0].description == "Chola architecture"
    assert assets[0].preservation_status == "Maintained"


def test_neo4j_store_duplicate_asset_prevention(mock_driver):
    driver, session = mock_driver
    # Return existing asset on check
    existing_asset_node = {
        "asset_id": "h001",
        "name": "Brihadisvara Temple",
        "location": "Thanjavur, Tamil Nadu",
        "period": "Chola period",
        "preservation_status": "Maintained",
    }
    session.run.return_value.single.return_value = {"a": existing_asset_node}

    store = Neo4jHeritageStore(driver=driver)
    new_asset = AssetCreate(
        asset_id="h001",
        name="Duplicate Temple",
        location="Somewhere",
        preservation_status="Good",
    )

    with pytest.raises(ValueError, match="already exists"):
        store.add_asset(new_asset)


def test_neo4j_store_funding_report_calculation(mock_driver):
    driver, session = mock_driver
    funding_rows = [
        {
            "project_id": "cp001",
            "project_name": "Heritage Restoration Project",
            "funding_id": "fd001",
            "allocated": 500000.0,
            "utilized": 150000.0,
        }
    ]
    session.run.return_value = DummyResult(funding_rows)

    store = Neo4jHeritageStore(driver=driver)
    report = store.get_funding_report()

    assert report.summary.allocated == 500000.0
    assert report.summary.utilized == 150000.0
    assert report.summary.remaining == 350000.0
    assert report.summary.percentage == "30.0%"
    assert len(report.records) == 1
    assert report.records[0].funding_id == "fd001"


def test_neo4j_store_delete_asset_success(mock_driver):
    driver, session = mock_driver
    # Mock dependency check: returns exact_id with empty dependents
    dep_record = {
        "exact_id": "test_asset_001",
        "projects": [],
        "archives": [],
        "exhibitions": [],
    }
    deleted_snapshot = {
        "asset_id": "test_asset_001",
        "name": "Test Asset",
    }
    session.run.return_value.single.side_effect = [dep_record, {"snapshot": deleted_snapshot}]

    store = Neo4jHeritageStore(driver=driver)
    res = store.delete_asset("test_asset_001")
    assert res["asset_id"] == "test_asset_001"


def test_neo4j_store_delete_asset_prevented_by_dependencies(mock_driver):
    driver, session = mock_driver
    dep_record = {
        "exact_id": "h001",
        "projects": ["cp001"],
        "archives": [],
        "exhibitions": [],
    }
    session.run.return_value.single.return_value = dep_record

    store = Neo4jHeritageStore(driver=driver)
    with pytest.raises(ValueError, match="is linked to active"):
        store.delete_asset("h001")


def test_neo4j_store_delete_project_prevented_by_funding(mock_driver):
    driver, session = mock_driver
    check_rec = {
        "exact_id": "cp001",
        "funding_ids": ["fd001"],
    }
    session.run.return_value.single.return_value = check_rec

    store = Neo4jHeritageStore(driver=driver)
    with pytest.raises(ValueError, match="active funding records exist"):
        store.delete_project("cp001")


def test_neo4j_store_delete_funding_success(mock_driver):
    driver, session = mock_driver
    deleted_snapshot = {"funding_id": "fd999", "project_id": "cp999"}
    session.run.return_value.single.return_value = {"snapshot": deleted_snapshot}

    store = Neo4jHeritageStore(driver=driver)
    res = store.delete_funding("fd999")
    assert res["funding_id"] == "fd999"


def test_neo4j_store_delete_archive_success(mock_driver):
    driver, session = mock_driver
    deleted_snapshot = {"archive_id": "da999", "title": "Test Archive"}
    session.run.return_value.single.return_value = {"snapshot": deleted_snapshot}

    store = Neo4jHeritageStore(driver=driver)
    res = store.delete_archive("da999")
    assert res["archive_id"] == "da999"


def test_neo4j_store_delete_exhibition_success(mock_driver):
    driver, session = mock_driver
    deleted_snapshot = {"exhibition_id": "ex999", "name": "Test Exhibition"}
    session.run.return_value.single.return_value = {"snapshot": deleted_snapshot}

    store = Neo4jHeritageStore(driver=driver)
    res = store.delete_exhibition("ex999")
    assert res["exhibition_id"] == "ex999"

