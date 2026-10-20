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
    FundingSummary,
    ExhibitionRatingSummary,
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


# Global singleton instance of the store
store = InMemoryHeritageStore()


def get_store() -> InMemoryHeritageStore:
    """Dependency injection helper for FastAPI routes."""
    return store
