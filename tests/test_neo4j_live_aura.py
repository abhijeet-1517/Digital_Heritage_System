import os
import pytest
from dotenv import load_dotenv
from neo4j import GraphDatabase
from backend.neo4j_store import Neo4jHeritageStore
from backend.models import (
    AssetCreate,
    ConservationProjectCreate,
    FundingCreate,
    ArchiveCreate,
    ExhibitionCreate,
)

load_dotenv(".env")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

skip_if_no_creds = pytest.mark.skipif(
    not NEO4J_URI or "<dbid>" in NEO4J_URI or not NEO4J_PASSWORD,
    reason="Neo4j Aura credentials not configured in local .env",
)


@skip_if_no_creds
def test_live_neo4j_aura_connectivity_and_operations():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    store = Neo4jHeritageStore(driver=driver)
    test_id = "test_asset_live_aura_999"

    try:
        # 1. Health check
        health = store.get_health()
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["node_count"] >= 10

        # 2. Dashboard stats
        stats = store.get_dashboard_stats()
        assert stats.total_assets >= 10

        # 3. Read initial assets
        assets = store.get_assets()
        assert len(assets) >= 10

        # 4. Safe write test record
        created = store.add_asset(
            AssetCreate(
                asset_id=test_id,
                name="Aura Live Integration Test Temple",
                location="Aura Live Cloud",
                period="21st Century",
                preservation_status="Good",
                description="Temporary test node for live Neo4j Aura verification.",
            )
        )
        assert created.asset_id == test_id

        # 5. Read back
        fetched = store.get_asset(test_id)
        assert fetched is not None
        assert fetched.name == "Aura Live Integration Test Temple"

        # 6. Delete test record (cleanup)
        deleted = store.delete_asset(test_id)
        assert deleted is not None

        # 7. Verify deletion
        assert store.get_asset(test_id) is None

        # 8. Test digital archive safe lifecycle & deletion
        test_archive_id = "test_da_live_999"
        created_archive = store.add_archive(
            ArchiveCreate(
                archive_id=test_archive_id,
                title="Live Aura Test Archive",
                asset_id="h001",
                file_reference="TEST-SCAN-999.ply",
                access_level="Public",
            )
        )
        assert created_archive.archive_id == test_archive_id
        deleted_archive = store.delete_archive(test_archive_id)
        assert deleted_archive is not None

        # 9. Test exhibition safe lifecycle & deletion
        test_exh_id = "test_ex_live_999"
        created_exh = store.add_exhibition(
            ExhibitionCreate(
                exhibition_id=test_exh_id,
                name="Live Aura Test Exhibition",
                start_date="2026-11-01",
                end_date="2026-11-30",
                status="Planned",
                asset_id="h001",
            )
        )
        assert created_exh.exhibition_id == test_exh_id
        deleted_exh = store.delete_exhibition(test_exh_id)
        assert deleted_exh is not None

        # 10. Test project safe lifecycle & deletion
        test_proj_id = "test_cp_live_999"
        created_proj = store.add_project(
            ConservationProjectCreate(
                project_id=test_proj_id,
                project_name="Live Aura Test Project",
                asset_id="h001",
                budget=10000.0,
                status="Planned",
            )
        )
        assert created_proj.project_id == test_proj_id

        # Funding safe lifecycle on test project
        test_fund_id = "test_fd_live_999"
        created_fund = store.add_funding(
            FundingCreate(
                funding_id=test_fund_id,
                project_id=test_proj_id,
                allocated_amount=10000.0,
                utilized_amount=0.0,
            )
        )
        assert created_fund.funding_id == test_fund_id
        # Project deletion must be blocked while funding exists
        with pytest.raises(ValueError):
            store.delete_project(test_proj_id)

        # Delete funding first, then project
        store.delete_funding(test_fund_id)
        deleted_proj = store.delete_project(test_proj_id)
        assert deleted_proj is not None

        # 11. Read reports to ensure existing baseline intact
        funding = store.get_funding_report()
        assert funding.summary.allocated >= 0

        archives = store.get_archives()
        assert len(archives) >= 1

        exhibitions = store.get_exhibitions()
        assert len(exhibitions) >= 1

        # 12. Read-only Database Explorer verification on live Aura
        inv = store.get_explorer_entities(page=1, page_size=10)
        assert inv.total >= 10
        assert len(inv.items) >= 1

        # Detail inspection on existing asset h001
        h001_detail = store.get_explorer_entity_detail("HeritageAsset", "h001")
        assert h001_detail.id == "h001"
        assert len(h001_detail.relationships) >= 1

        # Bounded graph query
        graph = store.get_explorer_graph(limit=30)
        assert graph.total_nodes >= 5
        assert graph.total_edges >= 1
    finally:
        with driver.session() as s:
            s.run("MATCH (a:HeritageAsset {asset_id: $id}) DETACH DELETE a", id=test_id)
            s.run("MATCH (d:DigitalArchive {archive_id: 'test_da_live_999'}) DETACH DELETE d")
            s.run("MATCH (e:Exhibition {exhibition_id: 'test_ex_live_999'}) DETACH DELETE e")
            s.run("MATCH (f:Funding {funding_id: 'test_fd_live_999'}) DETACH DELETE f")
            s.run("MATCH (p:ConservationProject {project_id: 'test_cp_live_999'}) DETACH DELETE p")
        driver.close()
