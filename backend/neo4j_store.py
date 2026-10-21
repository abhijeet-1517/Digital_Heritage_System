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
        asset_id = node.get("asset_id") or target_asset_id or ""
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
        WHERE $search_term IS NULL OR $search_term = ''
           OR toLower(coalesce(d.title, d.description, '')) CONTAINS toLower($search_term)
           OR toLower(d.archive_id) CONTAINS toLower($search_term)
           OR toLower(coalesce(a.asset_id, '')) CONTAINS toLower($search_term)
        RETURN d, a.asset_id AS target_asset_id
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
            asset_id=node.get("asset_id") or target_asset_id or "",
        )

    def get_exhibitions(self) -> List[ExhibitionResponse]:
        cypher = """
        MATCH (e:Exhibition)
        OPTIONAL MATCH (a:HeritageAsset)-[:FEATURED_IN]->(e)
        RETURN e, a.asset_id AS target_asset_id
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

