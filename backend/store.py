from typing import Dict, List, Optional
from backend.models import (
    AssetCreate,
    AssetStatusUpdate,
    ConservationProjectCreate,
    FundingCreate,
    ArchiveCreate,
    ExhibitionCreate,
    FeedbackCreate,
    DashboardStats,
    FundingReportResponse,
    FundingRecordResponse,
    ExhibitionRatingSummary,
    ExplorerEntitySummary,
    ExplorerInventoryResponse,
    ExplorerRelationshipItem,
    ExplorerEntityDetail,
    ExplorerGraphNode,
    ExplorerGraphEdge,
    ExplorerGraphResponse,
)


class InMemoryHeritageStore:
    """
    In-memory data store for the National Cultural Heritage Management System.
    Keeps all data access and business logic isolated from API routes, ensuring
    future migration to Neo4j requires only swapping this data access layer.
    """

    def __init__(self):
        self.assets: Dict[str, dict] = {}
        self.projects: Dict[str, dict] = {}
        self.funding: Dict[str, dict] = {}
        self.archives: Dict[str, dict] = {}
        self.exhibitions: Dict[str, dict] = {}
        self.feedback: List[dict] = []
        self._feedback_counter: int = 1
        self._seed_sample_data()

    def _seed_sample_data(self):
        """Seed realistic cultural heritage sample data."""
        # 1. Heritage Assets
        sample_assets = [
            {
                "asset_id": "HA001",
                "name": "Brihadisvara Temple",
                "location": "Thanjavur, Tamil Nadu",
                "period": "Chola Dynasty (11th Century)",
                "preservation_status": "Good",
                "description": "Magnificent granite temple dedicated to Lord Shiva, renowned for its towering 216-foot Vimana and UNESCO World Heritage status."
            },
            {
                "asset_id": "HA002",
                "name": "Konark Sun Temple",
                "location": "Konark, Odisha",
                "period": "Eastern Ganga Dynasty (13th Century)",
                "preservation_status": "Needs Attention",
                "description": "Celebrated 13th-century chariot temple featuring 24 carved stone wheels, facing ongoing coastal wind erosion and salinity degradation."
            },
            {
                "asset_id": "HA003",
                "name": "Nalanda Mahavihara",
                "location": "Nalanda, Bihar",
                "period": "Gupta & Pala Empires (5th–12th Century)",
                "preservation_status": "Good",
                "description": "Ancient Buddhist monastic university complex containing ruins of stupas, shrines, viharas, and important stucco artworks."
            },
            {
                "asset_id": "HA004",
                "name": "Hampi Stone Chariot & Complex",
                "location": "Vijayanagara, Karnataka",
                "period": "Vijayanagara Empire (14th–16th Century)",
                "preservation_status": "Critical",
                "description": "Iconic Garuda shrine carved as a stone chariot inside the Vittala temple complex, suffering micro-cracking and vibrational wear."
            },
            {
                "asset_id": "HA005",
                "name": "Ajanta Caves",
                "location": "Aurangabad, Maharashtra",
                "period": "Satavahana & Vakataka Dynasties (2nd BCE–5th CE)",
                "preservation_status": "Needs Attention",
                "description": "Rock-cut Buddhist cave monuments famous for fragile tempera murals and masterwork sculptural panels requiring environmental control."
            }
        ]
        for asset in sample_assets:
            self.assets[asset["asset_id"]] = asset

        # 2. Conservation Projects
        sample_projects = [
            {
                "project_id": "CP001",
                "project_name": "Konark Sandstone Desalination & Stabilization",
                "asset_id": "HA002",
                "budget": 1250000.0,
                "status": "Active"
            },
            {
                "project_id": "CP002",
                "project_name": "Hampi Vittala Complex Vibrational Dampening",
                "asset_id": "HA004",
                "budget": 2400000.0,
                "status": "Active"
            },
            {
                "project_id": "CP003",
                "project_name": "Brihadisvara Fresco Consolidation",
                "asset_id": "HA001",
                "budget": 850000.0,
                "status": "Completed"
            },
            {
                "project_id": "CP004",
                "project_name": "Ajanta Cave 1 Microclimate Control",
                "asset_id": "HA005",
                "budget": 1800000.0,
                "status": "Planned"
            }
        ]
        for proj in sample_projects:
            self.projects[proj["project_id"]] = proj

        # 3. Funding
        sample_funding = [
            {
                "funding_id": "FD001",
                "project_id": "CP001",
                "allocated_amount": 1250000.0,
                "utilized_amount": 875000.0
            },
            {
                "funding_id": "FD002",
                "project_id": "CP002",
                "allocated_amount": 2400000.0,
                "utilized_amount": 1950000.0
            },
            {
                "funding_id": "FD003",
                "project_id": "CP003",
                "allocated_amount": 850000.0,
                "utilized_amount": 850000.0
            },
            {
                "funding_id": "FD004",
                "project_id": "CP004",
                "allocated_amount": 1800000.0,
                "utilized_amount": 250000.0
            }
        ]
        for fund in sample_funding:
            self.funding[fund["funding_id"]] = fund

        # 4. Digital Archives
        sample_archives = [
            {
                "archive_id": "AR001",
                "title": "1868 British Architectural Survey of Konark",
                "asset_id": "HA002",
                "file_reference": "ARCH-1868-KNK-SURVEY.pdf",
                "access_level": "Public"
            },
            {
                "archive_id": "AR002",
                "title": "Brihadisvara Royal Chola Inscription Epigraphy Vol 2",
                "asset_id": "HA001",
                "file_reference": "EPIGRAPHY-TNJ-VOL2.pdf",
                "access_level": "Public"
            },
            {
                "archive_id": "AR003",
                "title": "Hampi Stone Chariot LiDAR 3D Point Cloud",
                "asset_id": "HA004",
                "file_reference": "LIDAR-HMP-3D-SCAN.ply",
                "access_level": "Restricted"
            },
            {
                "archive_id": "AR004",
                "title": "Ajanta Cave 17 Pigment Spectroscopy Analysis",
                "asset_id": "HA005",
                "file_reference": "CHEM-AJN-C17-PIGMENT.pdf",
                "access_level": "Restricted"
            }
        ]
        for archive in sample_archives:
            self.archives[archive["archive_id"]] = archive

        # 5. Exhibitions
        sample_exhibitions = [
            {
                "exhibition_id": "EX001",
                "name": "Living Chola Temples & Bronze Art",
                "start_date": "2026-08-01",
                "end_date": "2026-11-30",
                "status": "Current",
                "asset_id": "HA001"
            },
            {
                "exhibition_id": "EX002",
                "name": "Splendors of Vijayanagara: Echoes of Hampi",
                "start_date": "2026-09-15",
                "end_date": "2026-12-15",
                "status": "Current",
                "asset_id": "HA004"
            },
            {
                "exhibition_id": "EX003",
                "name": "Sun Gods Across Continents: Konark & Beyond",
                "start_date": "2027-01-10",
                "end_date": "2027-04-30",
                "status": "Planned",
                "asset_id": "HA002"
            }
        ]
        for exh in sample_exhibitions:
            self.exhibitions[exh["exhibition_id"]] = exh

        # 6. Feedback
        sample_feedback = [
            {
                "id": self._feedback_counter,
                "exhibition_id": "EX001",
                "rating": 5,
                "comment": "Exquisite display of Chola craftsmanship. The lighting on bronze icons is breathtaking."
            },
            {
                "id": self._feedback_counter + 1,
                "exhibition_id": "EX001",
                "rating": 4,
                "comment": "Informative curation and great interactive digital guides."
            },
            {
                "id": self._feedback_counter + 2,
                "exhibition_id": "EX002",
                "rating": 5,
                "comment": "The virtual 3D reconstruction of Hampi bazaar is an absolute masterpiece."
            },
            {
                "id": self._feedback_counter + 3,
                "exhibition_id": "EX002",
                "rating": 4,
                "comment": "Very insightful historical context regarding stone carving techniques."
            }
        ]
        self._feedback_counter += len(sample_feedback)
        self.feedback.extend(sample_feedback)

    # -------------------------------------------------------------------------
    # Health & Dashboard Statistics
    # -------------------------------------------------------------------------
    def get_health(self) -> dict:
        return {
            "status": "healthy",
            "service": "National Cultural Heritage Management System",
            "database_mode": "in-memory (Neo4j ready)",
            "total_assets": len(self.assets),
        }

    def get_dashboard_stats(self) -> DashboardStats:
        total_assets = len(self.assets)
        active_projects = sum(
            1 for p in self.projects.values() if p.get("status", "").lower() == "active"
        )
        total_archives = len(self.archives)
        current_exhibitions = sum(
            1 for e in self.exhibitions.values() if e.get("status", "").lower() == "current"
        )
        assets_needing_attention = sum(
            1
            for a in self.assets.values()
            if a.get("preservation_status", "").lower() in ["needs attention", "critical"]
        )

        return DashboardStats(
            total_assets=total_assets,
            active_projects=active_projects,
            total_archives=total_archives,
            current_exhibitions=current_exhibitions,
            assets_needing_attention=assets_needing_attention,
        )

    # -------------------------------------------------------------------------
    # Heritage Assets Operations
    # -------------------------------------------------------------------------
    def get_assets(self, search: Optional[str] = None) -> List[dict]:
        items = list(self.assets.values())
        if search:
            query = search.strip().lower()
            items = [
                a for a in items
                if query in str(a.get("name", "")).lower()
                or query in str(a.get("asset_id", "")).lower()
                or query in str(a.get("location", "")).lower()
                or query in str(a.get("period", "")).lower()
            ]
        return items

    def get_asset(self, asset_id: str) -> Optional[dict]:
        return self.assets.get(asset_id)

    def add_asset(self, asset_data: AssetCreate) -> dict:
        asset_id = asset_data.asset_id.strip()
        if asset_id in self.assets:
            raise ValueError(f"Asset ID '{asset_id}' already exists.")

        record = asset_data.model_dump()
        record["asset_id"] = asset_id
        self.assets[asset_id] = record
        return record

    def update_asset_status(self, asset_id: str, update_data: AssetStatusUpdate) -> dict:
        asset = self.assets.get(asset_id)
        if not asset:
            raise KeyError(f"Asset with ID '{asset_id}' does not exist.")

        asset["preservation_status"] = update_data.preservation_status.strip()
        self.assets[asset_id] = asset
        return asset

    def delete_asset(self, asset_id: str) -> dict:
        if asset_id not in self.assets:
            raise KeyError(f"Asset with ID '{asset_id}' does not exist.")
        return self.assets.pop(asset_id)

    # -------------------------------------------------------------------------
    # Conservation Projects Operations
    # -------------------------------------------------------------------------
    def get_projects(self) -> List[dict]:
        return list(self.projects.values())

    def get_project(self, project_id: str) -> Optional[dict]:
        return self.projects.get(project_id)

    def add_project(self, project_data: ConservationProjectCreate) -> dict:
        project_id = project_data.project_id.strip()
        if project_id in self.projects:
            raise ValueError(f"Project ID '{project_id}' already exists.")

        asset_id = project_data.asset_id.strip()
        if asset_id not in self.assets:
            raise ValueError(f"Referenced heritage asset '{asset_id}' does not exist.")

        record = project_data.model_dump()
        record["project_id"] = project_id
        record["asset_id"] = asset_id
        self.projects[project_id] = record
        return record

    def get_restoration_history(self, asset_id: str) -> List[dict]:
        if asset_id not in self.assets:
            raise KeyError(f"Asset with ID '{asset_id}' does not exist.")

        return [p for p in self.projects.values() if p.get("asset_id") == asset_id]

    # -------------------------------------------------------------------------
    # Funding Operations & Report Calculations
    # -------------------------------------------------------------------------
    def get_funding_report(self) -> FundingReportResponse:
        records: List[FundingRecordResponse] = []
        total_allocated = 0.0
        total_utilized = 0.0

        for f in self.funding.values():
            allocated = float(f.get("allocated_amount", 0.0))
            utilized = float(f.get("utilized_amount", 0.0))
            remaining = round(allocated - utilized, 2)
            pct = round((utilized / allocated * 100), 1) if allocated > 0 else 0.0

            total_allocated += allocated
            total_utilized += utilized

            records.append(
                FundingRecordResponse(
                    funding_id=f["funding_id"],
                    project_id=f["project_id"],
                    allocated_amount=allocated,
                    utilized_amount=utilized,
                    remaining=remaining,
                    percentage=f"{pct}%",
                )
            )

        remaining_balance = round(total_allocated - total_utilized, 2)
        overall_pct = (
            round((total_utilized / total_allocated * 100), 1)
            if total_allocated > 0
            else 0.0
        )

        summary = FundingSummary(
            allocated=round(total_allocated, 2),
            utilized=round(total_utilized, 2),
            remaining=remaining_balance,
            percentage=f"{overall_pct}%",
        )

        return FundingReportResponse(summary=summary, records=records)

    def add_funding(self, funding_data: FundingCreate) -> dict:
        funding_id = funding_data.funding_id.strip()
        if funding_id in self.funding:
            raise ValueError(f"Funding ID '{funding_id}' already exists.")

        project_id = funding_data.project_id.strip()
        if project_id not in self.projects:
            raise ValueError(f"Referenced conservation project '{project_id}' does not exist.")

        if funding_data.utilized_amount > funding_data.allocated_amount:
            raise ValueError("Utilized amount cannot exceed allocated amount.")

        record = funding_data.model_dump()
        record["funding_id"] = funding_id
        record["project_id"] = project_id
        self.funding[funding_id] = record
        return record

    # -------------------------------------------------------------------------
    # Digital Archives Operations
    # -------------------------------------------------------------------------
    def get_archives(self, query: Optional[str] = None) -> List[dict]:
        items = list(self.archives.values())
        if query:
            q = query.strip().lower()
            items = [
                a for a in items
                if q in str(a.get("title", "")).lower()
                or q in str(a.get("archive_id", "")).lower()
                or q in str(a.get("asset_id", "")).lower()
                or q in str(a.get("file_reference", "")).lower()
            ]
        return items

    def add_archive(self, archive_data: ArchiveCreate) -> dict:
        archive_id = archive_data.archive_id.strip()
        if archive_id in self.archives:
            raise ValueError(f"Archive ID '{archive_id}' already exists.")

        asset_id = archive_data.asset_id.strip()
        if asset_id not in self.assets:
            raise ValueError(f"Referenced heritage asset '{asset_id}' does not exist.")

        record = archive_data.model_dump()
        record["archive_id"] = archive_id
        record["asset_id"] = asset_id
        self.archives[archive_id] = record
        return record

    # -------------------------------------------------------------------------
    # Exhibitions & Feedback Operations
    # -------------------------------------------------------------------------
    def get_exhibitions(self) -> List[dict]:
        return list(self.exhibitions.values())

    def get_exhibition(self, exhibition_id: str) -> Optional[dict]:
        return self.exhibitions.get(exhibition_id)

    def add_exhibition(self, exhibition_data: ExhibitionCreate) -> dict:
        exhibition_id = exhibition_data.exhibition_id.strip()
        if exhibition_id in self.exhibitions:
            raise ValueError(f"Exhibition ID '{exhibition_id}' already exists.")

        asset_id = exhibition_data.asset_id.strip()
        if asset_id not in self.assets:
            raise ValueError(f"Referenced heritage asset '{asset_id}' does not exist.")

        record = exhibition_data.model_dump()
        record["exhibition_id"] = exhibition_id
        record["asset_id"] = asset_id
        self.exhibitions[exhibition_id] = record
        return record

    def add_feedback(self, feedback_data: FeedbackCreate) -> dict:
        exhibition_id = feedback_data.exhibition_id.strip()
        if exhibition_id not in self.exhibitions:
            raise ValueError(f"Referenced exhibition ID '{exhibition_id}' does not exist.")

        entry = {
            "id": self._feedback_counter,
            "exhibition_id": exhibition_id,
            "rating": feedback_data.rating,
            "comment": feedback_data.comment or "",
        }
        self._feedback_counter += 1
        self.feedback.append(entry)
        return entry

    def get_exhibition_ratings(self) -> List[ExhibitionRatingSummary]:
        results: List[ExhibitionRatingSummary] = []
        for exh_id, exh in self.exhibitions.items():
            exh_feedback = [f for f in self.feedback if f.get("exhibition_id") == exh_id]
            ratings = [f["rating"] for f in exh_feedback]
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
            comments = [f["comment"] for f in exh_feedback if f.get("comment")]

            results.append(
                ExhibitionRatingSummary(
                    exhibition_id=exh_id,
                    name=exh.get("name", ""),
                    average_rating=avg_rating,
                    feedback_count=len(ratings),
                    comments=comments,
                )
            )
        return results

    def delete_project(self, project_id: str) -> dict:
        if project_id not in self.projects:
            raise KeyError(f"Project with ID '{project_id}' does not exist.")
        # Rule: Prevent deletion if project has linked funding records
        linked_funding = [f["funding_id"] for f in self.funding.values() if f.get("project_id") == project_id]
        if linked_funding:
            raise ValueError(f"Cannot delete project '{project_id}': active funding records exist ({', '.join(linked_funding)}). Please remove or reassign funding first.")
        return self.projects.pop(project_id)

    def delete_funding(self, funding_id: str) -> dict:
        if funding_id not in self.funding:
            raise KeyError(f"Funding record with ID '{funding_id}' does not exist.")
        return self.funding.pop(funding_id)

    def delete_archive(self, archive_id: str) -> dict:
        if archive_id not in self.archives:
            raise KeyError(f"Archive with ID '{archive_id}' does not exist.")
        return self.archives.pop(archive_id)

    def delete_exhibition(self, exhibition_id: str) -> dict:
        if exhibition_id not in self.exhibitions:
            raise KeyError(f"Exhibition with ID '{exhibition_id}' does not exist.")
        deleted = self.exhibitions.pop(exhibition_id)
        # Safely remove associated visitor feedback given for this exhibition
        self.feedback = [f for f in self.feedback if f.get("exhibition_id") != exhibition_id]
        return deleted
    # -------------------------------------------------------------------------
    # Database Explorer Operations (In-Memory Implementation)
    # -------------------------------------------------------------------------
    ALLOWED_LABELS = {
        "HeritageAsset",
        "ConservationProject",
        "Funding",
        "DigitalArchive",
        "Exhibition",
        "VisitorFeedback",
    }

    ALLOWED_REL_TYPES = {
        "FEATURED_IN",
        "CONSERVES",
        "ALLOCATED_TO",
        "DOCUMENTED_IN",
        "GIVEN_FOR",
        "MANAGES",
    }

    def _get_all_memory_entities(self) -> List[ExplorerEntitySummary]:
        items: List[ExplorerEntitySummary] = []
        # 1. Assets
        for aid, a in self.assets.items():
            loc = a.get("location") or ""
            status = a.get("preservation_status") or ""
            items.append(
                ExplorerEntitySummary(
                    id=aid,
                    label="HeritageAsset",
                    name=a.get("name") or aid,
                    subtitle=f"{loc} • {status}".strip(" •"),
                    properties=dict(a),
                )
            )
        # 2. Projects
        for pid, p in self.projects.items():
            status = p.get("status") or ""
            budget = p.get("budget", 0)
            items.append(
                ExplorerEntitySummary(
                    id=pid,
                    label="ConservationProject",
                    name=p.get("project_name") or pid,
                    subtitle=f"{status} • ₹{float(budget):,.0f}".strip(" •"),
                    properties=dict(p),
                )
            )
        # 3. Funding
        for fid, f in self.funding.items():
            alloc = f.get("allocated_amount", 0)
            util = f.get("utilized_amount", 0)
            items.append(
                ExplorerEntitySummary(
                    id=fid,
                    label="Funding",
                    name=f"Funding {fid}",
                    subtitle=f"Alloc: ₹{float(alloc):,.0f} • Util: ₹{float(util):,.0f}",
                    properties=dict(f),
                )
            )
        # 4. Archives
        for did, d in self.archives.items():
            access = d.get("access_level") or "Public"
            f_ref = d.get("file_reference") or ""
            items.append(
                ExplorerEntitySummary(
                    id=did,
                    label="DigitalArchive",
                    name=d.get("title") or did,
                    subtitle=f"{access} • {f_ref}".strip(" •"),
                    properties=dict(d),
                )
            )
        # 5. Exhibitions
        for eid, e in self.exhibitions.items():
            status = e.get("status") or "Current"
            start = e.get("start_date") or ""
            items.append(
                ExplorerEntitySummary(
                    id=eid,
                    label="Exhibition",
                    name=e.get("name") or eid,
                    subtitle=f"{status} • {start}".strip(" •"),
                    properties=dict(e),
                )
            )
        # 6. Feedback
        for f in self.feedback:
            fid = f"f{f.get('id', 1):03d}"
            rating = f.get("rating", 5)
            comment = f.get("comment") or ""
            f_props = dict(f)
            f_props["feedback_id"] = fid
            items.append(
                ExplorerEntitySummary(
                    id=fid,
                    label="VisitorFeedback",
                    name=f"Feedback (★ {rating})",
                    subtitle=comment[:50] + ("..." if len(comment) > 50 else ""),
                    properties=f_props,
                )
            )
        return items

    def get_explorer_entities(
        self,
        label: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ExplorerInventoryResponse:
        if label and label not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid entity label '{label}'. Allowed labels: {sorted(self.ALLOWED_LABELS)}")

        all_items = self._get_all_memory_entities()

        if label:
            all_items = [item for item in all_items if item.label == label]

        if search and search.strip():
            s = search.strip().lower()
            all_items = [
                item for item in all_items
                if s in item.id.lower()
                or s in item.name.lower()
                or s in item.subtitle.lower()
                or any(s in str(v).lower() for v in item.properties.values())
            ]

        total = len(all_items)
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        start_idx = (page - 1) * page_size
        paged_items = all_items[start_idx : start_idx + page_size]

        return ExplorerInventoryResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=paged_items,
        )

    def get_explorer_entity_detail(self, label: str, entity_id: str) -> ExplorerEntityDetail:
        if label not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid entity label '{label}'. Allowed labels: {sorted(self.ALLOWED_LABELS)}")

        all_items = self._get_all_memory_entities()
        target = next((item for item in all_items if item.label == label and item.id.lower() == entity_id.lower()), None)
        if not target:
            raise KeyError(f"Entity '{entity_id}' of type '{label}' not found.")

        relationships: List[ExplorerRelationshipItem] = []

        if label == "HeritageAsset":
            aid = target.id
            # Incoming from projects: (:ConservationProject)-[:CONSERVES]->(:HeritageAsset)
            for pid, p in self.projects.items():
                if p.get("asset_id") == aid:
                    relationships.append(
                        ExplorerRelationshipItem(
                            rel_type="CONSERVES",
                            direction="incoming",
                            target_id=pid,
                            target_label="ConservationProject",
                            target_name=p.get("project_name") or pid,
                        )
                    )
            # Incoming from archives: (:HeritageAsset)-[:DOCUMENTED_IN]->(:DigitalArchive)
            for did, d in self.archives.items():
                if d.get("asset_id") == aid:
                    relationships.append(
                        ExplorerRelationshipItem(
                            rel_type="DOCUMENTED_IN",
                            direction="outgoing",
                            target_id=did,
                            target_label="DigitalArchive",
                            target_name=d.get("title") or did,
                        )
                    )
            # Outgoing to exhibitions: (:HeritageAsset)-[:FEATURED_IN]->(:Exhibition)
            for eid, e in self.exhibitions.items():
                if e.get("asset_id") == aid:
                    relationships.append(
                        ExplorerRelationshipItem(
                            rel_type="FEATURED_IN",
                            direction="outgoing",
                            target_id=eid,
                            target_label="Exhibition",
                            target_name=e.get("name") or eid,
                        )
                    )

        elif label == "ConservationProject":
            pid = target.id
            aid = target.properties.get("asset_id")
            if aid and aid in self.assets:
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type="CONSERVES",
                        direction="outgoing",
                        target_id=aid,
                        target_label="HeritageAsset",
                        target_name=self.assets[aid].get("name") or aid,
                    )
                )
            for fid, f in self.funding.items():
                if f.get("project_id") == pid:
                    relationships.append(
                        ExplorerRelationshipItem(
                            rel_type="ALLOCATED_TO",
                            direction="incoming",
                            target_id=fid,
                            target_label="Funding",
                            target_name=f"Funding {fid}",
                        )
                    )

        elif label == "Funding":
            pid = target.properties.get("project_id")
            if pid and pid in self.projects:
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type="ALLOCATED_TO",
                        direction="outgoing",
                        target_id=pid,
                        target_label="ConservationProject",
                        target_name=self.projects[pid].get("project_name") or pid,
                    )
                )

        elif label == "DigitalArchive":
            aid = target.properties.get("asset_id")
            if aid and aid in self.assets:
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type="DOCUMENTED_IN",
                        direction="incoming",
                        target_id=aid,
                        target_label="HeritageAsset",
                        target_name=self.assets[aid].get("name") or aid,
                    )
                )

        elif label == "Exhibition":
            eid = target.id
            aid = target.properties.get("asset_id")
            if aid and aid in self.assets:
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type="FEATURED_IN",
                        direction="incoming",
                        target_id=aid,
                        target_label="HeritageAsset",
                        target_name=self.assets[aid].get("name") or aid,
                    )
                )
            for f in self.feedback:
                if f.get("exhibition_id") == eid:
                    fid = f"f{f.get('id', 1):03d}"
                    relationships.append(
                        ExplorerRelationshipItem(
                            rel_type="GIVEN_FOR",
                            direction="incoming",
                            target_id=fid,
                            target_label="VisitorFeedback",
                            target_name=f"Feedback (★ {f.get('rating', 5)})",
                        )
                    )

        elif label == "VisitorFeedback":
            eid = target.properties.get("exhibition_id")
            if eid and eid in self.exhibitions:
                relationships.append(
                    ExplorerRelationshipItem(
                        rel_type="GIVEN_FOR",
                        direction="outgoing",
                        target_id=eid,
                        target_label="Exhibition",
                        target_name=self.exhibitions[eid].get("name") or eid,
                    )
                )

        mgmt_urls = {
            "HeritageAsset": "/assets.html",
            "ConservationProject": "/conservation.html",
            "Funding": "/funding.html",
            "DigitalArchive": "/archives.html",
            "Exhibition": "/exhibitions.html",
            "VisitorFeedback": "/exhibitions.html",
        }

        return ExplorerEntityDetail(
            id=target.id,
            label=label,
            properties=target.properties,
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
        limit = max(1, min(limit, 100))
        if focus_label and focus_label not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid focus label '{focus_label}'")
        if label_filter and label_filter not in self.ALLOWED_LABELS:
            raise ValueError(f"Invalid label filter '{label_filter}'")
        if rel_filter and rel_filter not in self.ALLOWED_REL_TYPES:
            raise ValueError(f"Invalid relationship filter '{rel_filter}'")

        all_summaries = {item.id: item for item in self._get_all_memory_entities()}
        nodes_dict: Dict[str, ExplorerGraphNode] = {}
        edges_list: List[ExplorerGraphEdge] = []
        seen_edges = set()

        def add_node(entity_id: str):
            if entity_id in all_summaries and entity_id not in nodes_dict:
                s = all_summaries[entity_id]
                nodes_dict[entity_id] = ExplorerGraphNode(
                    id=s.id,
                    label=s.label,
                    name=s.name,
                    subtitle=s.subtitle,
                    properties=s.properties,
                )

        # Build in-memory graph edges
        all_edges: List[ExplorerGraphEdge] = []
        # 1. Projects -> Assets (CONSERVES)
        for pid, p in self.projects.items():
            aid = p.get("asset_id")
            if aid:
                all_edges.append(ExplorerGraphEdge(id=f"{pid}->{aid}:CONSERVES", source=pid, target=aid, type="CONSERVES", label="CONSERVES"))
        # 2. Funding -> Projects (ALLOCATED_TO)
        for fid, f in self.funding.items():
            pid = f.get("project_id")
            if pid:
                all_edges.append(ExplorerGraphEdge(id=f"{fid}->{pid}:ALLOCATED_TO", source=fid, target=pid, type="ALLOCATED_TO", label="ALLOCATED_TO"))
        # 3. Assets -> Archives (DOCUMENTED_IN)
        for did, d in self.archives.items():
            aid = d.get("asset_id")
            if aid:
                all_edges.append(ExplorerGraphEdge(id=f"{aid}->{did}:DOCUMENTED_IN", source=aid, target=did, type="DOCUMENTED_IN", label="DOCUMENTED_IN"))
        # 4. Assets -> Exhibitions (FEATURED_IN)
        for eid, e in self.exhibitions.items():
            aid = e.get("asset_id")
            if aid:
                all_edges.append(ExplorerGraphEdge(id=f"{aid}->{eid}:FEATURED_IN", source=aid, target=eid, type="FEATURED_IN", label="FEATURED_IN"))
        # 5. Feedback -> Exhibitions (GIVEN_FOR)
        for f in self.feedback:
            eid = f.get("exhibition_id")
            fid = f"f{f.get('id', 1):03d}"
            if eid:
                all_edges.append(ExplorerGraphEdge(id=f"{fid}->{eid}:GIVEN_FOR", source=fid, target=eid, type="GIVEN_FOR", label="GIVEN_FOR"))

        if focus_id and focus_label:
            add_node(focus_id)
            for edge in all_edges:
                if len(edges_list) >= limit:
                    break
                if edge.source == focus_id or edge.target == focus_id:
                    if rel_filter and edge.type != rel_filter:
                        continue
                    add_node(edge.source)
                    add_node(edge.target)
                    edges_list.append(edge)
        else:
            for edge in all_edges:
                if len(edges_list) >= limit:
                    break
                if rel_filter and edge.type != rel_filter:
                    continue
                s_lbl = all_summaries.get(edge.source, ExplorerEntitySummary(id="", label="", name="")).label
                t_lbl = all_summaries.get(edge.target, ExplorerEntitySummary(id="", label="", name="")).label
                if label_filter and label_filter not in (s_lbl, t_lbl):
                    continue
                add_node(edge.source)
                add_node(edge.target)
                edges_list.append(edge)

            # Include initial standalone nodes if node count is low
            if len(nodes_dict) < 5:
                for sid, s in all_summaries.items():
                    if len(nodes_dict) >= 15:
                        break
                    add_node(sid)

        return ExplorerGraphResponse(
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            total_nodes=len(nodes_dict),
            total_edges=len(edges_list),
            truncated=len(edges_list) >= limit,
        )


store = InMemoryHeritageStore()


def get_store() -> InMemoryHeritageStore:
    """Dependency injection helper for FastAPI routes."""
    return store
