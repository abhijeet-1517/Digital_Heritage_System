import logging
from typing import Dict, List, Optional
from neo4j import Driver
from backend.models import (
    AssetCreate,
    AssetResponse,
    AssetStatusUpdate,
    ConservationProjectCreate,
    ConservationProjectResponse,
    FundingCreate,
    FundingReportResponse,
    FundingRecordResponse,
    FundingSummary,
    ArchiveCreate,
    ArchiveResponse,
    ExhibitionCreate,
    ExhibitionResponse,
    FeedbackCreate,
    FeedbackResponse,
    ExhibitionRatingSummary,
    DashboardStats,
    ExplorerEntitySummary,
    ExplorerInventoryResponse,
    ExplorerRelationshipItem,
    ExplorerEntityDetail,
    ExplorerGraphNode,
    ExplorerGraphEdge,
    ExplorerGraphResponse,
)

logger = logging.getLogger("heritage.neo4j_store")


class Neo4jHeritageStore:
    """
    Data-access repository layer backed by Neo4j graph database.
    Reconciles Member 1's schema properties with frontend/API models.
    """

    def __init__(self, driver: Driver, database: Optional[str] = None):
        self.driver = driver
        # Aura default database is often None (connects to default Aura db)
        self.database = database

    def _get_session(self):
        return self.driver.session(database=self.database) if self.database else self.driver.session()

    # -------------------------------------------------------------------------
    # System Health
    # -------------------------------------------------------------------------
    def get_health(self) -> dict:
        """Verify Neo4j connectivity and return node count."""
        try:
            self.driver.verify_connectivity()
            with self._get_session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS count").single()
                node_count = result["count"] if result else 0
            return {
                "status": "healthy",
                "database_mode": "neo4j",
                "connected": True,
                "node_count": node_count,
            }
        except Exception as e:
            logger.error("Neo4j health check failed: %s", e)
            return {
                "status": "unhealthy",
                "database_mode": "neo4j",
                "connected": False,
                "error": str(e),
            }

    # -------------------------------------------------------------------------
    # Dashboard Statistics
    # -------------------------------------------------------------------------
    def get_dashboard_stats(self) -> DashboardStats:
        """
        Compute dashboard counts directly from Neo4j graph nodes.
        Assets needing attention include condition/status containing 'Critical', 'Needs', or 'Attention'.
        """
        cypher = """
        MATCH (a:HeritageAsset)
        WITH count(a) AS total_assets,
             count(CASE WHEN toLower(coalesce(a.preservation_status, '')) CONTAINS 'critical'
                          OR toLower(coalesce(a.preservation_status, '')) CONTAINS 'need'
                          OR toLower(coalesce(a.preservation_status, '')) CONTAINS 'attention'
                          OR toLower(coalesce(a.condition, '')) CONTAINS 'critical'
                          OR toLower(coalesce(a.condition, '')) CONTAINS 'need'
                          OR toLower(coalesce(a.condition, '')) CONTAINS 'attention'
                        THEN 1 END) AS assets_needing_attention

        OPTIONAL MATCH (p:ConservationProject)
        WITH total_assets, assets_needing_attention,
             count(CASE WHEN toLower(coalesce(p.status, '')) IN ['active', 'ongoing'] THEN 1 END) AS active_projects

        OPTIONAL MATCH (d:DigitalArchive)
        WITH total_assets, assets_needing_attention, active_projects,
             count(d) AS total_archives

        OPTIONAL MATCH (e:Exhibition)
        WITH total_assets, assets_needing_attention, active_projects, total_archives,
             count(CASE WHEN toLower(coalesce(e.status, 'current')) = 'current'
                          OR e.status IS NULL THEN 1 END) AS current_exhibitions

        RETURN total_assets, assets_needing_attention, active_projects, total_archives, current_exhibitions
        """
        with self._get_session() as session:
            record = session.run(cypher).single()
            if not record:
                return DashboardStats(
                    total_assets=0,
                    active_projects=0,
                    total_archives=0,
                    current_exhibitions=0,
                    assets_needing_attention=0,
                )
            return DashboardStats(
                total_assets=record["total_assets"] or 0,
                active_projects=record["active_projects"] or 0,
                total_archives=record["total_archives"] or 0,
                current_exhibitions=record["current_exhibitions"] or 0,
                assets_needing_attention=record["assets_needing_attention"] or 0,
            )

    # -------------------------------------------------------------------------
    # Heritage Assets
    # -------------------------------------------------------------------------
    def _map_asset_node(self, node: dict) -> AssetResponse:
        # Reconcile historical_significance vs description, condition vs preservation_status
        desc = node.get("description") or node.get("historical_significance") or ""
        status = node.get("preservation_status") or node.get("condition") or "Good"
        return AssetResponse(
            asset_id=node.get("asset_id", ""),
            name=node.get("name", ""),
            location=node.get("location", ""),
            period=node.get("period") or "",
            preservation_status=status,
            description=desc,
        )

    def get_assets(self, search: Optional[str] = None) -> List[AssetResponse]:
        query = """
        MATCH (a:HeritageAsset)
        WHERE $search IS NULL OR $search = ''
           OR toLower(a.name) CONTAINS toLower($search)
           OR toLower(a.asset_id) CONTAINS toLower($search)
           OR toLower(coalesce(a.location, '')) CONTAINS toLower($search)
        RETURN a ORDER BY a.asset_id ASC
        """
        with self._get_session() as session:
            result = session.run(query, search=search)
            return [self._map_asset_node(dict(record["a"])) for record in result]

    def get_asset(self, asset_id: str) -> Optional[AssetResponse]:
        query = """
        MATCH (a:HeritageAsset)
        WHERE toLower(a.asset_id) = toLower($asset_id)
        RETURN a LIMIT 1
        """
        with self._get_session() as session:
            record = session.run(query, asset_id=asset_id).single()
            if not record:
                return None
            return self._map_asset_node(dict(record["a"]))

    def add_asset(self, asset_data: AssetCreate) -> AssetResponse:
        # Check uniqueness
        if self.get_asset(asset_data.asset_id):
            raise ValueError(f"Heritage Asset with ID '{asset_data.asset_id}' already exists.")

        cypher = """
        MATCH (o:Organization {org_id: 'org001'})
        CREATE (a:HeritageAsset {
            asset_id: $asset_id,
            name: $name,
            location: $location,
            period: $period,
            preservation_status: $preservation_status,
            description: $description,
            historical_significance: $description,
            condition: $preservation_status
        })
        MERGE (o)-[:MANAGES]->(a)
        RETURN a
        """
        with self._get_session() as session:
            record = session.run(
                cypher,
                asset_id=asset_data.asset_id,
                name=asset_data.name,
                location=asset_data.location,
                period=asset_data.period or "",
                preservation_status=asset_data.preservation_status,
                description=asset_data.description or "",
            ).single()
            if not record:
                # If org001 doesn't exist, create without org link
                cypher_standalone = """
                CREATE (a:HeritageAsset {
                    asset_id: $asset_id,
                    name: $name,
                    location: $location,
                    period: $period,
                    preservation_status: $preservation_status,
                    description: $description,
                    historical_significance: $description,
                    condition: $preservation_status
                })
                RETURN a
                """
                record = session.run(
                    cypher_standalone,
                    asset_id=asset_data.asset_id,
                    name=asset_data.name,
                    location=asset_data.location,
                    period=asset_data.period or "",
                    preservation_status=asset_data.preservation_status,
                    description=asset_data.description or "",
                ).single()
            return self._map_asset_node(dict(record["a"]))

    def update_asset_status(self, asset_id: str, update_data: AssetStatusUpdate) -> AssetResponse:
        cypher = """
        MATCH (a:HeritageAsset)
        WHERE toLower(a.asset_id) = toLower($asset_id)
        SET a.preservation_status = $status,
            a.condition = $status
        RETURN a
        """
        with self._get_session() as session:
            record = session.run(cypher, asset_id=asset_id, status=update_data.preservation_status).single()
            if not record:
                raise KeyError(f"Heritage Asset with ID '{asset_id}' not found.")
            return self._map_asset_node(dict(record["a"]))

    def delete_asset(self, asset_id: str) -> dict:
        """
        Safely delete a HeritageAsset node.
        Rule: Check for active dependents (conservation projects, archives, exhibitions) before deletion
        to avoid orphan relationships or accidental cascade.
        """
        dep_cypher = """
        MATCH (a:HeritageAsset)
        WHERE toLower(a.asset_id) = toLower($asset_id)
        OPTIONAL MATCH (p:ConservationProject)-[:CONSERVES]->(a)
        OPTIONAL MATCH (a)-[:DOCUMENTED_IN]->(d:DigitalArchive)
        OPTIONAL MATCH (a)-[:FEATURED_IN]->(e:Exhibition)
        RETURN a.asset_id AS exact_id,
               collect(DISTINCT p.project_id) AS projects,
               collect(DISTINCT d.archive_id) AS archives,
               collect(DISTINCT e.exhibition_id) AS exhibitions
        """
        with self._get_session() as session:
            dep_rec = session.run(dep_cypher, asset_id=asset_id).single()
            if not dep_rec or not dep_rec["exact_id"]:
                raise KeyError(f"Heritage Asset with ID '{asset_id}' not found.")

            projects = [pid for pid in dep_rec["projects"] if pid]
            archives = [did for did in dep_rec["archives"] if did]
            exhibitions = [eid for eid in dep_rec["exhibitions"] if eid]

            conflicts = []
            if projects:
                conflicts.append(f"conservation projects ({', '.join(projects)})")
            if archives:
                conflicts.append(f"digital archives ({', '.join(archives)})")
            if exhibitions:
                conflicts.append(f"exhibitions ({', '.join(exhibitions)})")

            if conflicts:
                raise ValueError(
                    f"Cannot delete asset '{asset_id}' because it is linked to active {'; '.join(conflicts)}. "
                    "Please reassign or delete the associated records first."
                )

            cypher = """
            MATCH (a:HeritageAsset)
            WHERE toLower(a.asset_id) = toLower($asset_id)
            WITH a, a {.*} AS snapshot
            DETACH DELETE a
            RETURN snapshot
            """
            record = session.run(cypher, asset_id=asset_id).single()
            return dict(record["snapshot"])


    # -------------------------------------------------------------------------
    # Conservation Projects
    # -------------------------------------------------------------------------
    def _map_project_node(self, node: dict, target_asset_id: Optional[str] = None) -> ConservationProjectResponse:
        p_name = node.get("project_name") or node.get("name") or ""
        budget = float(node.get("budget", 0) or node.get("funding_amount", 0) or 0.0)
        asset_id = node.get("asset_id") or target_asset_id or ""
        status = node.get("status") or "Planned"
        return ConservationProjectResponse(
            project_id=node.get("project_id", ""),
            project_name=p_name,
            asset_id=asset_id,
            budget=budget,
            status=status,
        )

    def get_projects(self) -> List[ConservationProjectResponse]:
        cypher = """
        MATCH (p:ConservationProject)
        OPTIONAL MATCH (p)-[:CONSERVES]->(a:HeritageAsset)
        RETURN p, a.asset_id AS target_asset_id
        ORDER BY p.project_id ASC
        """
        with self._get_session() as session:
            result = session.run(cypher)
            projects = []
            for record in result:
                p_node = dict(record["p"])
                asset_id = record["target_asset_id"] or p_node.get("asset_id", "")
                projects.append(self._map_project_node(p_node, asset_id))
            return projects

    def add_project(self, project_data: ConservationProjectCreate) -> ConservationProjectResponse:
        # Check uniqueness of project_id
        check_cypher = """
        MATCH (p:ConservationProject)
        WHERE toLower(p.project_id) = toLower($project_id)
        RETURN p LIMIT 1
        """
        with self._get_session() as session:
            if session.run(check_cypher, project_id=project_data.project_id).single():
                raise ValueError(f"Conservation Project with ID '{project_data.project_id}' already exists.")

            # Validate associated asset exists
            asset_cypher = """
            MATCH (a:HeritageAsset)
            WHERE toLower(a.asset_id) = toLower($asset_id)
            RETURN a.asset_id AS exact_id LIMIT 1
            """
            asset_record = session.run(asset_cypher, asset_id=project_data.asset_id).single()
            if not asset_record:
                raise ValueError(f"Associated asset '{project_data.asset_id}' does not exist.")
            exact_asset_id = asset_record["exact_id"]

            cypher = """
            MATCH (a:HeritageAsset {asset_id: $exact_asset_id})
            OPTIONAL MATCH (o:Organization {org_id: 'org001'})
            CREATE (p:ConservationProject {
                project_id: $project_id,
                project_name: $project_name,
                name: $project_name,
                asset_id: $exact_asset_id,
                budget: $budget,
                funding_amount: $budget,
                status: $status
            })
            MERGE (p)-[:CONSERVES]->(a)
            FOREACH (_ IN CASE WHEN o IS NOT NULL THEN [1] ELSE [] END |
                MERGE (o)-[:MANAGES]->(p)
            )
            RETURN p
            """
            rec = session.run(
                cypher,
                exact_asset_id=exact_asset_id,
                project_id=project_data.project_id,
                project_name=project_data.project_name,
                budget=project_data.budget,
                status=project_data.status,
            ).single()
            return self._map_project_node(dict(rec["p"]), exact_asset_id)

    def get_restoration_history(self, asset_id: str) -> List[ConservationProjectResponse]:
        # Verify asset existence first
        asset = self.get_asset(asset_id)
        if not asset:
            raise KeyError(f"Heritage Asset '{asset_id}' does not exist.")

        cypher = """
        MATCH (a:HeritageAsset)
        WHERE toLower(a.asset_id) = toLower($asset_id)
        MATCH (p:ConservationProject)-[:CONSERVES]->(a)
        RETURN p, a.asset_id AS target_asset_id
        ORDER BY p.project_id ASC
        """
        with self._get_session() as session:
            result = session.run(cypher, asset_id=asset_id)
            projects = []
            for record in result:
                p_node = dict(record["p"])
                projects.append(self._map_project_node(p_node, record["target_asset_id"]))
            return projects

    def delete_project(self, project_id: str) -> dict:
        """
        Delete a ConservationProject node.
        Rule: Prevent deletion if project has linked Funding records (:Funding)-[:ALLOCATED_TO]->(p).
        Only remove organization and asset relationships for this project.
        """
        check_funding_cypher = """
        MATCH (p:ConservationProject)
        WHERE toLower(p.project_id) = toLower($project_id)
        OPTIONAL MATCH (f:Funding)-[:ALLOCATED_TO]->(p)
        RETURN p.project_id AS exact_id, collect(DISTINCT f.funding_id) AS funding_ids
        """
        with self._get_session() as session:
            check_rec = session.run(check_funding_cypher, project_id=project_id).single()
            if not check_rec or not check_rec["exact_id"]:
                raise KeyError(f"Conservation Project with ID '{project_id}' not found.")

            f_ids = [fid for fid in check_rec["funding_ids"] if fid]
            if f_ids:
                raise ValueError(
                    f"Cannot delete project '{project_id}': active funding records exist ({', '.join(f_ids)}). "
                    "Please reassign or delete the associated funding records first."
                )

            del_cypher = """
            MATCH (p:ConservationProject)
            WHERE toLower(p.project_id) = toLower($project_id)
            WITH p, p {.*} AS snapshot
            DETACH DELETE p
            RETURN snapshot
            """
            del_rec = session.run(del_cypher, project_id=project_id).single()
            return dict(del_rec["snapshot"])


    # -------------------------------------------------------------------------
    # Funding Management
    # -------------------------------------------------------------------------
    def get_funding_report(self) -> FundingReportResponse:
        """
        Retrieve authoritative funding records from (:Funding) nodes linked to (:ConservationProject),
        falling back gracefully to project budget/preservation reports if no explicit Funding node exists yet.
        """
        cypher = """
        MATCH (p:ConservationProject)
        OPTIONAL MATCH (f:Funding)-[:ALLOCATED_TO]->(p)
        OPTIONAL MATCH (rep:PreservationReport)-[:REPORTS_ON]->(:HeritageAsset)<-[:CONSERVES]-(p)
        RETURN p.project_id AS project_id,
               coalesce(p.project_name, p.name) AS project_name,
               f.funding_id AS funding_id,
               coalesce(f.allocated_amount, p.funding_amount, p.budget, 0.0) AS allocated,
               coalesce(f.utilized_amount, rep.funding_utilized, 0.0) AS utilized
        ORDER BY p.project_id ASC
        """
        with self._get_session() as session:
            result = session.run(cypher)
            records: List[FundingRecordResponse] = []
            seen_projects = set()

            total_allocated = 0.0
            total_utilized = 0.0

            for r in result:
                pid = r["project_id"]
                if pid in seen_projects:
                    continue
                seen_projects.add(pid)

                fid = r["funding_id"] or f"FD-{pid}"
                alloc = float(r["allocated"] or 0.0)
                util = float(r["utilized"] or 0.0)
                remaining = max(0.0, alloc - util)
                pct = f"{(util / alloc * 100):.1f}%" if alloc > 0 else "0.0%"

                total_allocated += alloc
                total_utilized += util

                records.append(
                    FundingRecordResponse(
                        funding_id=fid,
                        project_id=pid,
                        allocated_amount=alloc,
                        utilized_amount=util,
                        remaining=remaining,
                        percentage=pct,
                    )
                )

            total_remaining = max(0.0, total_allocated - total_utilized)
            total_pct = f"{(total_utilized / total_allocated * 100):.1f}%" if total_allocated > 0 else "0.0%"

            summary = FundingSummary(
                allocated=total_allocated,
                utilized=total_utilized,
                remaining=total_remaining,
                percentage=total_pct,
            )
            return FundingReportResponse(summary=summary, records=records)

    def add_funding(self, funding_data: FundingCreate) -> FundingRecordResponse:
        # Check uniqueness of funding_id
        check_cypher = """
        MATCH (f:Funding)
        WHERE toLower(f.funding_id) = toLower($funding_id)
        RETURN f LIMIT 1
        """
        with self._get_session() as session:
            if session.run(check_cypher, funding_id=funding_data.funding_id).single():
                raise ValueError(f"Funding record with ID '{funding_data.funding_id}' already exists.")

            # Check project existence
            proj_cypher = """
            MATCH (p:ConservationProject)
            WHERE toLower(p.project_id) = toLower($project_id)
            RETURN p.project_id AS exact_pid LIMIT 1
            """
            proj_rec = session.run(proj_cypher, project_id=funding_data.project_id).single()
            if not proj_rec:
                raise ValueError(f"Associated conservation project '{funding_data.project_id}' does not exist.")
            exact_pid = proj_rec["exact_pid"]

            cypher = """
            MATCH (p:ConservationProject {project_id: $exact_pid})
            CREATE (f:Funding {
                funding_id: $funding_id,
                project_id: $exact_pid,
                allocated_amount: $allocated_amount,
                utilized_amount: $utilized_amount
            })
            MERGE (f)-[:ALLOCATED_TO]->(p)
            RETURN f
            """
            session.run(
                cypher,
                exact_pid=exact_pid,
                funding_id=funding_data.funding_id,
                allocated_amount=funding_data.allocated_amount,
                utilized_amount=funding_data.utilized_amount,
            )

            remaining = max(0.0, funding_data.allocated_amount - funding_data.utilized_amount)
            pct = (
                f"{(funding_data.utilized_amount / funding_data.allocated_amount * 100):.1f}%"
                if funding_data.allocated_amount > 0
                else "0.0%"
            )
            return FundingRecordResponse(
                funding_id=funding_data.funding_id,
                project_id=exact_pid,
                allocated_amount=funding_data.allocated_amount,
                utilized_amount=funding_data.utilized_amount,
                remaining=remaining,
                percentage=pct,
            )

    def delete_funding(self, funding_id: str) -> dict:
        """
        Delete a Funding node.
        Rule: Removes the Funding node and its [:ALLOCATED_TO] relationship to the conservation project.
        Does not touch the conservation project node itself.
        """
        cypher = """
        MATCH (f:Funding)
        WHERE toLower(f.funding_id) = toLower($funding_id)
        WITH f, f {.*} AS snapshot
        DETACH DELETE f
        RETURN snapshot
        """
        with self._get_session() as session:
            record = session.run(cypher, funding_id=funding_id).single()
            if not record:
                raise KeyError(f"Funding record with ID '{funding_id}' not found.")
            return dict(record["snapshot"])


    # -------------------------------------------------------------------------
    # Digital Archives
    # -------------------------------------------------------------------------
    def _map_archive_node(self, node: dict, target_asset_id: Optional[str] = None) -> ArchiveResponse:
        title = node.get("title") or node.get("description") or "Digital Archive Document"
        asset_id = node.get("asset_id") or target_asset_id or "N/A"
        file_ref = node.get("file_reference") or node.get("type") or "Document Reference"
        access = node.get("access_level") or "Public"
        return ArchiveResponse(
            archive_id=node.get("archive_id", ""),
            title=title,
            asset_id=asset_id,
            file_reference=file_ref,
            access_level=access,
        )

    def get_archives(self, query: Optional[str] = None) -> List[ArchiveResponse]:
        cypher = """
        MATCH (d:DigitalArchive)
        OPTIONAL MATCH (a:HeritageAsset)-[:DOCUMENTED_IN]->(d)
        WITH d, collect(DISTINCT a.asset_id) AS asset_ids
        WHERE $search_term IS NULL OR $search_term = ''
           OR toLower(coalesce(d.title, d.description, '')) CONTAINS toLower($search_term)
           OR toLower(d.archive_id) CONTAINS toLower($search_term)
           OR toLower(coalesce(d.asset_id, '')) CONTAINS toLower($search_term)
           OR any(aid IN asset_ids WHERE toLower(aid) CONTAINS toLower($search_term))
        RETURN d,
               CASE
                   WHEN size(asset_ids) > 0 THEN asset_ids[0]
                   WHEN d.asset_id IS NOT NULL AND d.asset_id <> '' THEN d.asset_id
                   ELSE 'N/A'
               END AS target_asset_id
        ORDER BY d.archive_id ASC
        """
        with self._get_session() as session:
            result = session.run(cypher, {"search_term": query})
            archives = []
            for record in result:
                d_node = dict(record["d"])
                archives.append(self._map_archive_node(d_node, record["target_asset_id"]))
            return archives

    def add_archive(self, archive_data: ArchiveCreate) -> ArchiveResponse:
        # Check uniqueness of archive_id
        check_cypher = """
        MATCH (d:DigitalArchive)
        WHERE toLower(d.archive_id) = toLower($archive_id)
        RETURN d LIMIT 1
        """
        with self._get_session() as session:
            if session.run(check_cypher, archive_id=archive_data.archive_id).single():
                raise ValueError(f"Digital Archive with ID '{archive_data.archive_id}' already exists.")

            # Validate asset exists
            asset_cypher = """
            MATCH (a:HeritageAsset)
            WHERE toLower(a.asset_id) = toLower($asset_id)
            RETURN a.asset_id AS exact_id LIMIT 1
            """
            asset_rec = session.run(asset_cypher, asset_id=archive_data.asset_id).single()
            if not asset_rec:
                raise ValueError(f"Associated asset '{archive_data.asset_id}' does not exist.")
            exact_asset_id = asset_rec["exact_id"]

            cypher = """
            MATCH (a:HeritageAsset {asset_id: $exact_asset_id})
            CREATE (d:DigitalArchive {
                archive_id: $archive_id,
                title: $title,
                description: $title,
                asset_id: $exact_asset_id,
                file_reference: $file_reference,
                type: $file_reference,
                access_level: $access_level
            })
            MERGE (a)-[:DOCUMENTED_IN]->(d)
            RETURN d
            """
            rec = session.run(
                cypher,
                exact_asset_id=exact_asset_id,
                archive_id=archive_data.archive_id,
                title=archive_data.title,
                file_reference=archive_data.file_reference,
                access_level=archive_data.access_level,
            ).single()
            return self._map_archive_node(dict(rec["d"]), exact_asset_id)

    def delete_archive(self, archive_id: str) -> dict:
        """
        Delete a DigitalArchive node.
        Rule: Safely detaches the archive from HeritageAsset (:HeritageAsset)-[:DOCUMENTED_IN]->(d)
        and Researcher (:Researcher)-[:ACCESSES]->(d), deleting the archive record without affecting the asset or researcher.
        """
        cypher = """
        MATCH (d:DigitalArchive)
        WHERE toLower(d.archive_id) = toLower($archive_id)
        WITH d, d {.*} AS snapshot
        DETACH DELETE d
        RETURN snapshot
        """
        with self._get_session() as session:
            record = session.run(cypher, archive_id=archive_id).single()
            if not record:
                raise KeyError(f"Digital Archive with ID '{archive_id}' not found.")
            return dict(record["snapshot"])


    # -------------------------------------------------------------------------
    # Exhibitions & Visitor Feedback
    # -------------------------------------------------------------------------
    def _map_exhibition_node(self, node: dict, target_asset_id: Optional[str] = None) -> ExhibitionResponse:
        return ExhibitionResponse(
            exhibition_id=node.get("exhibition_id", ""),
            name=node.get("name", "Exhibition"),
            start_date=node.get("start_date") or "2024-01-01",
            end_date=node.get("end_date") or "2024-12-31",
            status=node.get("status") or "Current",
            asset_id=node.get("asset_id") or target_asset_id or "N/A",
        )

    def get_exhibitions(self) -> List[ExhibitionResponse]:
        cypher = """
        MATCH (e:Exhibition)
        OPTIONAL MATCH (a:HeritageAsset)-[:FEATURED_IN]->(e)
        WITH e, collect(DISTINCT a.asset_id) AS asset_ids
        RETURN e, CASE WHEN size(asset_ids) > 0 THEN asset_ids[0] ELSE NULL END AS target_asset_id
        ORDER BY e.exhibition_id ASC
        """
        with self._get_session() as session:
            result = session.run(cypher)
            exhibitions = []
            for record in result:
                e_node = dict(record["e"])
                exhibitions.append(self._map_exhibition_node(e_node, record["target_asset_id"]))
            return exhibitions

    def add_exhibition(self, exhibition_data: ExhibitionCreate) -> ExhibitionResponse:
        check_cypher = """
        MATCH (e:Exhibition)
        WHERE toLower(e.exhibition_id) = toLower($exhibition_id)
        RETURN e LIMIT 1
        """
        with self._get_session() as session:
            if session.run(check_cypher, exhibition_id=exhibition_data.exhibition_id).single():
                raise ValueError(f"Exhibition with ID '{exhibition_data.exhibition_id}' already exists.")

            asset_cypher = """
            MATCH (a:HeritageAsset)
            WHERE toLower(a.asset_id) = toLower($asset_id)
            RETURN a.asset_id AS exact_id LIMIT 1
            """
            asset_rec = session.run(asset_cypher, asset_id=exhibition_data.asset_id).single()
            if not asset_rec:
                raise ValueError(f"Associated asset '{exhibition_data.asset_id}' does not exist.")
            exact_asset_id = asset_rec["exact_id"]

            cypher = """
            MATCH (a:HeritageAsset {asset_id: $exact_asset_id})
            CREATE (e:Exhibition {
                exhibition_id: $exhibition_id,
                name: $name,
                start_date: $start_date,
                end_date: $end_date,
                status: $status,
                asset_id: $exact_asset_id,
                type: 'Physical and Virtual'
            })
            MERGE (a)-[:FEATURED_IN]->(e)
            RETURN e
            """
            rec = session.run(
                cypher,
                exact_asset_id=exact_asset_id,
                exhibition_id=exhibition_data.exhibition_id,
                name=exhibition_data.name,
                start_date=exhibition_data.start_date,
                end_date=exhibition_data.end_date,
                status=exhibition_data.status,
            ).single()
            return self._map_exhibition_node(dict(rec["e"]), exact_asset_id)

    def add_feedback(self, feedback_data: FeedbackCreate) -> FeedbackResponse:
        # Check exhibition exists
        ex_cypher = """
        MATCH (e:Exhibition)
        WHERE toLower(e.exhibition_id) = toLower($exhibition_id)
        RETURN e.exhibition_id AS exact_eid LIMIT 1
        """
        with self._get_session() as session:
            ex_rec = session.run(ex_cypher, exhibition_id=feedback_data.exhibition_id).single()
            if not ex_rec:
                raise ValueError(f"Exhibition with ID '{feedback_data.exhibition_id}' does not exist.")
            exact_eid = ex_rec["exact_eid"]

            # Count existing feedback to generate unique feedback_id and integer id
            count_rec = session.run("MATCH (f:VisitorFeedback) RETURN count(f) AS count").single()
            next_idx = (count_rec["count"] if count_rec else 0) + 1
            feedback_str_id = f"f{next_idx:03d}"

            cypher = """
            MATCH (e:Exhibition {exhibition_id: $exact_eid})
            CREATE (f:VisitorFeedback {
                feedback_id: $feedback_id,
                num_id: $num_id,
                exhibition_id: $exact_eid,
                rating: $rating,
                comments: $comment,
                comment: $comment
            })
            MERGE (f)-[:GIVEN_FOR]->(e)
            RETURN f
            """
            session.run(
                cypher,
                exact_eid=exact_eid,
                feedback_id=feedback_str_id,
                num_id=next_idx,
                rating=feedback_data.rating,
                comment=feedback_data.comment or "",
            )
            return FeedbackResponse(
                id=next_idx,
                exhibition_id=exact_eid,
                rating=feedback_data.rating,
                comment=feedback_data.comment or "",
            )

    def get_exhibition_ratings(self) -> List[ExhibitionRatingSummary]:
        cypher = """
        MATCH (e:Exhibition)
        OPTIONAL MATCH (f:VisitorFeedback)-[:GIVEN_FOR]->(e)
        WITH e,
             count(f) AS fb_count,
             avg(f.rating) AS avg_rating,
             collect(coalesce(f.comment, f.comments, '')) AS all_comments
        RETURN e.exhibition_id AS exhibition_id,
               e.name AS name,
               coalesce(avg_rating, 0.0) AS average_rating,
               fb_count AS feedback_count,
               [c IN all_comments WHERE c <> ''] AS comments
        ORDER BY e.exhibition_id ASC
        """
        with self._get_session() as session:
            result = session.run(cypher)
            summaries = []
            for r in result:
                summaries.append(
                    ExhibitionRatingSummary(
                        exhibition_id=r["exhibition_id"],
                        name=r["name"],
                        average_rating=round(float(r["average_rating"]), 1),
                        feedback_count=int(r["feedback_count"]),
                        comments=r["comments"],
                    )
                )
            return summaries

    def delete_exhibition(self, exhibition_id: str) -> dict:
        """
        Delete an Exhibition node.
        Rule: Safely deletes the Exhibition node, its [:FEATURED_IN] relationship to HeritageAsset,
        and visitor feedback given for this exhibition (:VisitorFeedback)-[:GIVEN_FOR]->(e).
        Does not delete or alter the associated HeritageAsset.
        """
        cypher = """
        MATCH (e:Exhibition)
        WHERE toLower(e.exhibition_id) = toLower($exhibition_id)
        WITH e, e {.*} AS snapshot
        OPTIONAL MATCH (f:VisitorFeedback)-[:GIVEN_FOR]->(e)
        DETACH DELETE f
        DETACH DELETE e
        RETURN snapshot
        """
        with self._get_session() as session:
            record = session.run(cypher, exhibition_id=exhibition_id).single()
            if not record:
                raise KeyError(f"Exhibition with ID '{exhibition_id}' not found.")
            return dict(record["snapshot"])
    # -------------------------------------------------------------------------
    # Database Explorer Operations
    # -------------------------------------------------------------------------
    LABEL_ID_MAP = {
        "HeritageAsset": "asset_id",
        "ConservationProject": "project_id",
        "Funding": "funding_id",
        "DigitalArchive": "archive_id",
        "Exhibition": "exhibition_id",
        "VisitorFeedback": "feedback_id",
        "Organization": "org_id",
        "Researcher": "researcher_id",
        "PreservationReport": "report_id",
    }

    ALLOWED_LABELS = set(LABEL_ID_MAP.keys())
    ALLOWED_REL_TYPES = {
        "FEATURED_IN",
        "CONSERVES",
        "ALLOCATED_TO",
        "DOCUMENTED_IN",
        "GIVEN_FOR",
        "MANAGES",
        "ACCESSES",
        "REPORTS_ON",
    }

    @staticmethod
    def _extract_entity_info(node_dict: dict, label: str):
        id_prop = Neo4jHeritageStore.LABEL_ID_MAP.get(label, "id")
        entity_id = str(node_dict.get(id_prop) or node_dict.get("id") or "")

        name = ""
        subtitle = ""

        if label == "HeritageAsset":
            name = node_dict.get("name") or entity_id
            loc = node_dict.get("location") or ""
            status = node_dict.get("preservation_status") or node_dict.get("condition") or ""
            subtitle = f"{loc} • {status}".strip(" •")
        elif label == "ConservationProject":
            name = node_dict.get("project_name") or node_dict.get("name") or entity_id
            status = node_dict.get("status") or ""
            budget = node_dict.get("budget") or node_dict.get("funding_amount")
            amt = f"₹{float(budget):,.0f}" if budget is not None else ""
            subtitle = f"{status} • {amt}".strip(" •")
        elif label == "Funding":
            name = f"Funding {entity_id}"
            alloc = node_dict.get("allocated_amount")
            util = node_dict.get("utilized_amount")
            alloc_str = f"Alloc: ₹{float(alloc):,.0f}" if alloc is not None else ""
            util_str = f"Util: ₹{float(util):,.0f}" if util is not None else ""
            subtitle = f"{alloc_str} • {util_str}".strip(" •")
        elif label == "DigitalArchive":
            name = node_dict.get("title") or node_dict.get("description") or entity_id
            access = node_dict.get("access_level") or "Public"
            f_ref = node_dict.get("file_reference") or ""
            subtitle = f"{access} • {f_ref}".strip(" •")
        elif label == "Exhibition":
            name = node_dict.get("name") or entity_id
            status = node_dict.get("status") or "Current"
            start = node_dict.get("start_date") or ""
            subtitle = f"{status} • {start}".strip(" •")
        elif label == "VisitorFeedback":
            rating = node_dict.get("rating")
            comment = node_dict.get("comment") or node_dict.get("comments") or ""
            name = f"Feedback (★ {rating})" if rating else "Visitor Feedback"
            subtitle = comment[:50] + ("..." if len(comment) > 50 else "")
        elif label == "Organization":
            name = node_dict.get("name") or entity_id
            subtitle = "Heritage Organization"
        elif label == "Researcher":
            name = node_dict.get("name") or entity_id
            access = node_dict.get("access_level") or ""
            subtitle = f"Access: {access}"
        elif label == "PreservationReport":
            name = f"Report {entity_id}"
            cond = node_dict.get("condition") or ""
            prog = node_dict.get("restoration_progress") or ""
            subtitle = f"{cond} • {prog}".strip(" •")
        else:
            name = node_dict.get("name") or entity_id
            subtitle = label

        return entity_id, name, subtitle

    def get_explorer_entities(
        self,
        label: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ExplorerInventoryResponse:
        """
        Query actual Neo4j entities with pagination, label filtering, and search.
        Validates label against allowlist to strictly prevent arbitrary Cypher execution.
        """
        if label and label not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid entity label '{label}'. Allowed labels: {sorted(self.ALLOWED_LABELS)}")

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        skip = (page - 1) * page_size

        label_clause = f":`{label}`" if label else ""

        # Build search condition
        search_filter = ""
        params = {"skip": skip, "limit": page_size}
        if search and search.strip():
            params["search_term"] = search.strip().lower()
            # Match against common string properties across all nodes
            search_filter = """
            AND (
                toLower(coalesce(n.name, '')) CONTAINS $search_term
                OR toLower(coalesce(n.project_name, '')) CONTAINS $search_term
                OR toLower(coalesce(n.title, '')) CONTAINS $search_term
                OR toLower(coalesce(n.asset_id, '')) CONTAINS $search_term
                OR toLower(coalesce(n.project_id, '')) CONTAINS $search_term
                OR toLower(coalesce(n.funding_id, '')) CONTAINS $search_term
                OR toLower(coalesce(n.archive_id, '')) CONTAINS $search_term
                OR toLower(coalesce(n.exhibition_id, '')) CONTAINS $search_term
                OR toLower(coalesce(n.feedback_id, '')) CONTAINS $search_term
                OR toLower(coalesce(n.location, '')) CONTAINS $search_term
                OR toLower(coalesce(n.description, '')) CONTAINS $search_term
                OR toLower(coalesce(n.comment, '')) CONTAINS $search_term
            )
            """

        count_cypher = f"""
        MATCH (n{label_clause})
        WHERE 1=1 {search_filter}
        RETURN count(n) AS total
        """

        items_cypher = f"""
        MATCH (n{label_clause})
        WHERE 1=1 {search_filter}
        WITH n, labels(n) AS lbls
        ORDER BY head(lbls), coalesce(n.asset_id, n.project_id, n.funding_id, n.archive_id, n.exhibition_id, n.feedback_id, n.org_id, n.researcher_id, n.report_id, id(n)) ASC
        SKIP $skip
        LIMIT $limit
        RETURN n, labels(n) AS lbls
        """

        with self._get_session() as session:
            count_rec = session.run(count_cypher, **params).single()
            total = count_rec["total"] if count_rec else 0

            result = session.run(items_cypher, **params)
            items = []
            for r in result:
                node_props = dict(r["n"])
                lbls = r["lbls"]
                matched_label = next((l for l in lbls if l in self.ALLOWED_LABELS), lbls[0] if lbls else "Node")
                eid, name, subtitle = self._extract_entity_info(node_props, matched_label)
                items.append(
                    ExplorerEntitySummary(
                        id=eid,
                        label=matched_label,
                        name=name,
                        subtitle=subtitle,
                        properties=node_props,
                    )
                )

            total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
            return ExplorerInventoryResponse(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                items=items,
            )

    def get_explorer_entity_detail(self, label: str, entity_id: str) -> ExplorerEntityDetail:
        """
        Inspect the full properties and immediate connected relationships of a specific node.
        """
        if label not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid entity label '{label}'. Allowed labels: {sorted(self.ALLOWED_LABELS)}")

        id_prop = self.LABEL_ID_MAP[label]
        cypher = f"""
        MATCH (n:`{label}`)
        WHERE toLower(toString(n.{id_prop})) = toLower($entity_id)
        OPTIONAL MATCH (n)-[r_out]->(m_out)
        OPTIONAL MATCH (n)<-[r_in]-(m_in)
        RETURN n,
               collect(DISTINCT {{
                   rel_type: type(r_out),
                   direction: 'outgoing',
                   target_props: properties(m_out),
                   target_labels: labels(m_out)
               }}) AS out_rels,
               collect(DISTINCT {{
                   rel_type: type(r_in),
                   direction: 'incoming',
                   target_props: properties(m_in),
                   target_labels: labels(m_in)
               }}) AS in_rels
        LIMIT 1
        """

        with self._get_session() as session:
            rec = session.run(cypher, entity_id=entity_id).single()
            if not rec or not rec["n"]:
                raise KeyError(f"Entity '{entity_id}' of type '{label}' not found.")

            node_props = dict(rec["n"])
            eid, name, _ = self._extract_entity_info(node_props, label)

            relationships: List[ExplorerRelationshipItem] = []

            # Process outgoing relationships
            for item in rec["out_rels"]:
                rel_type = item.get("rel_type")
                if not rel_type or not item.get("target_props"):
                    continue
                t_labels = item.get("target_labels") or []
                t_label = next((l for l in t_labels if l in self.ALLOWED_LABELS), t_labels[0] if t_labels else "Node")
                t_props = item.get("target_props") or {}
                t_id, t_name, _ = self._extract_entity_info(t_props, t_label)
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type=rel_type,
                        direction="outgoing",
                        target_id=t_id,
                        target_label=t_label,
                        target_name=t_name,
                    )
                )

            # Process incoming relationships
            for item in rec["in_rels"]:
                rel_type = item.get("rel_type")
                if not rel_type or not item.get("target_props"):
                    continue
                t_labels = item.get("target_labels") or []
                t_label = next((l for l in t_labels if l in self.ALLOWED_LABELS), t_labels[0] if t_labels else "Node")
                t_props = item.get("target_props") or {}
                t_id, t_name, _ = self._extract_entity_info(t_props, t_label)
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type=rel_type,
                        direction="incoming",
                        target_id=t_id,
                        target_label=t_label,
                        target_name=t_name,
                    )
                )

            # Determine corresponding management URL
            mgmt_urls = {
                "HeritageAsset": "/assets.html",
                "ConservationProject": "/conservation.html",
                "Funding": "/funding.html",
                "DigitalArchive": "/archives.html",
                "Exhibition": "/exhibitions.html",
                "VisitorFeedback": "/exhibitions.html",
            }

            return ExplorerEntityDetail(
                id=eid,
                label=label,
                properties=node_props,
                relationships=relationships,
                management_url=mgmt_urls.get(label),
            )

    def get_explorer_graph(
        self,
        focus_label: Optional[str] = None,
        focus_id: Optional[str] = None,
        label_filter: Optional[str] = None,
        rel_filter: Optional[str] = None,
        limit: int = 40,
    ) -> ExplorerGraphResponse:
        """
        Fetch bounded relationship graph nodes and edges with actual Neo4j types and directions.
        Supports single-node neighborhood expansion via focus_label and focus_id.
        """
        limit = max(1, min(limit, 100))

        if focus_label and focus_label not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid focus label '{focus_label}'")
        if label_filter and label_filter not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid label filter '{label_filter}'")
        if rel_filter and rel_filter not in self.ALLOWED_REL_TYPES:
            raise ValueError(f"Invalid relationship filter '{rel_filter}'")

        nodes_dict: Dict[str, ExplorerGraphNode] = {}
        edges_list: List[ExplorerGraphEdge] = []
        seen_edges = set()

        with self._get_session() as session:
            if focus_id and focus_label:
                # Neighborhood expansion around focus node
                id_prop = self.LABEL_ID_MAP[focus_label]
                rel_match = f":`{rel_filter}`" if rel_filter else ""
                cypher = f"""
                MATCH (center:`{focus_label}`)
                WHERE toLower(toString(center.{id_prop})) = toLower($focus_id)
                OPTIONAL MATCH (center)-[r{rel_match}]-(neighbor)
                RETURN center, labels(center) AS center_labels,
                       r, type(r) AS rel_type, startNode(r) = center AS is_outgoing,
                       neighbor, labels(neighbor) AS neighbor_labels
                LIMIT $limit
                """
                results = session.run(cypher, focus_id=focus_id, limit=limit)
                for rec in results:
                    c_props = dict(rec["center"])
                    c_labels = rec["center_labels"]
                    c_label = next((l for l in c_labels if l in self.ALLOWED_LABELS), focus_label)
                    cid, cname, csub = self._extract_entity_info(c_props, c_label)

                    if cid not in nodes_dict:
                        nodes_dict[cid] = ExplorerGraphNode(
                            id=cid,
                            label=c_label,
                            name=cname,
                            subtitle=csub,
                            properties=c_props,
                        )

                    if rec["r"] and rec["neighbor"]:
                        n_props = dict(rec["neighbor"])
                        n_labels = rec["neighbor_labels"]
                        n_label = next((l for l in n_labels if l in self.ALLOWED_LABELS), n_labels[0] if n_labels else "Node")
                        nid, nname, nsub = self._extract_entity_info(n_props, n_label)

                        if nid not in nodes_dict:
                            nodes_dict[nid] = ExplorerGraphNode(
                                id=nid,
                                label=n_label,
                                name=nname,
                                subtitle=nsub,
                                properties=n_props,
                            )

                        rtype = rec["rel_type"]
                        is_out = rec["is_outgoing"]
                        src_id = cid if is_out else nid
                        tgt_id = nid if is_out else cid
                        edge_key = (src_id, tgt_id, rtype)

                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            edges_list.append(
                                ExplorerGraphEdge(
                                    id=f"{src_id}->{tgt_id}:{rtype}",
                                    source=src_id,
                                    target=tgt_id,
                                    type=rtype,
                                    label=rtype,
                                )
                            )
            else:
                # Global overview bounded graph
                where_clauses = []
                params = {"limit": limit}

                if label_filter:
                    where_clauses.append("($label_filter IN labels(a) OR $label_filter IN labels(b))")
                    params["label_filter"] = label_filter

                rel_match = f":`{rel_filter}`" if rel_filter else ""
                filter_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

                cypher = f"""
                MATCH (a)-[r{rel_match}]->(b)
                {filter_sql}
                RETURN a, labels(a) AS a_labels,
                       r, type(r) AS rel_type,
                       b, labels(b) AS b_labels
                LIMIT $limit
                """

                results = session.run(cypher, **params)
                for rec in results:
                    a_props = dict(rec["a"])
                    a_labels = rec["a_labels"]
                    a_label = next((l for l in a_labels if l in self.ALLOWED_LABELS), a_labels[0] if a_labels else "Node")
                    aid, aname, asub = self._extract_entity_info(a_props, a_label)

                    b_props = dict(rec["b"])
                    b_labels = rec["b_labels"]
                    b_label = next((l for l in b_labels if l in self.ALLOWED_LABELS), b_labels[0] if b_labels else "Node")
                    bid, bname, bsub = self._extract_entity_info(b_props, b_label)

                    if aid not in nodes_dict:
                        nodes_dict[aid] = ExplorerGraphNode(
                            id=aid, label=a_label, name=aname, subtitle=asub, properties=a_props
                        )
                    if bid not in nodes_dict:
                        nodes_dict[bid] = ExplorerGraphNode(
                            id=bid, label=b_label, name=bname, subtitle=bsub, properties=b_props
                        )

                    rtype = rec["rel_type"]
                    edge_key = (aid, bid, rtype)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges_list.append(
                            ExplorerGraphEdge(
                                id=f"{aid}->{bid}:{rtype}",
                                source=aid,
                                target=bid,
                                type=rtype,
                                label=rtype,
                            )
                        )

                # If isolated nodes exist and graph is empty or small, include sample nodes
                if len(nodes_dict) < 5 and not rel_filter:
                    if label_filter:
                        isolated_cypher = f"""
                        MATCH (n:`{label_filter}`)
                        RETURN n, labels(n) AS lbls
                        LIMIT 20
                        """
                    else:
                        isolated_cypher = """
                        MATCH (n)
                        RETURN n, labels(n) AS lbls
                        LIMIT 20
                        """
                    for rec in session.run(isolated_cypher):
                        props = dict(rec["n"])
                        lbls = rec["lbls"]
                        lbl = next((l for l in lbls if l in self.ALLOWED_LABELS), lbls[0] if lbls else "Node")
                        nid, nname, nsub = self._extract_entity_info(props, lbl)
                        if nid and nid not in nodes_dict:
                            nodes_dict[nid] = ExplorerGraphNode(
                                id=nid, label=lbl, name=nname, subtitle=nsub, properties=props
                            )

        return ExplorerGraphResponse(
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            total_nodes=len(nodes_dict),
            total_edges=len(edges_list),
            truncated=len(edges_list) >= limit,
        )
