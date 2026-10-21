from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AssetBase(BaseModel):
    asset_id: str = Field(..., min_length=1, description="Unique asset identifier (e.g. HA001)")
    name: str = Field(..., min_length=1, description="Asset name")
    location: str = Field(..., min_length=1, description="Location of heritage asset")
    period: Optional[str] = Field(default="", description="Historical period or era")
    preservation_status: str = Field(..., description="Good, Needs Attention, or Critical")
    description: Optional[str] = Field(default="", description="Description of the asset")

    @field_validator("asset_id", "name", "location", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty or whitespace only.")
        return value


class AssetCreate(AssetBase):
    pass


class AssetStatusUpdate(BaseModel):
    preservation_status: str = Field(..., min_length=1, description="New preservation status")

    @field_validator("preservation_status", mode="before")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Status cannot be empty.")
        return value


class AssetResponse(AssetBase):
    pass


# Conservation Models
class ConservationProjectBase(BaseModel):
    project_id: str = Field(..., min_length=1, description="Unique project identifier (e.g. CP001)")
    project_name: str = Field(..., min_length=1, description="Name of the conservation project")
    asset_id: str = Field(..., min_length=1, description="Associated asset identifier")
    budget: float = Field(..., ge=0, description="Project budget amount")
    status: str = Field(..., description="Planned, Active, or Completed")

    @field_validator("project_id", "project_name", "asset_id", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty.")
        return value


class ConservationProjectCreate(ConservationProjectBase):
    pass


class ConservationProjectResponse(ConservationProjectBase):
    pass


# Funding Models
class FundingCreate(BaseModel):
    funding_id: str = Field(..., min_length=1, description="Unique funding record identifier (e.g. FD001)")
    project_id: str = Field(..., min_length=1, description="Associated conservation project ID")
    allocated_amount: float = Field(..., gt=0, description="Allocated budget amount")
    utilized_amount: float = Field(default=0.0, ge=0, description="Utilized budget amount")

    @field_validator("funding_id", "project_id", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty.")
        return value


class FundingRecordResponse(BaseModel):
    funding_id: str
    project_id: str
    allocated_amount: float
    utilized_amount: float
    remaining: float
    percentage: str


class FundingSummary(BaseModel):
    allocated: float
    utilized: float
    remaining: float
    percentage: str


class FundingReportResponse(BaseModel):
    summary: FundingSummary
    records: List[FundingRecordResponse]


# Archive Models
class ArchiveBase(BaseModel):
    archive_id: str = Field(..., min_length=1, description="Unique archive identifier (e.g. AR001)")
    title: str = Field(..., min_length=1, description="Archive document/media title")
    asset_id: str = Field(..., min_length=1, description="Associated asset ID")
    file_reference: str = Field(..., min_length=1, description="File name, link or catalog reference")
    access_level: str = Field(..., description="Public or Restricted")

    @field_validator("archive_id", "title", "asset_id", "file_reference", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty.")
        return value


class ArchiveCreate(ArchiveBase):
    pass


class ArchiveResponse(ArchiveBase):
    pass


# Exhibition Models
class ExhibitionBase(BaseModel):
    exhibition_id: str = Field(..., min_length=1, description="Unique exhibition identifier (e.g. EX001)")
    name: str = Field(..., min_length=1, description="Exhibition title")
    start_date: str = Field(..., min_length=1, description="Exhibition start date (YYYY-MM-DD)")
    end_date: str = Field(..., min_length=1, description="Exhibition end date (YYYY-MM-DD)")
    status: str = Field(..., description="Planned, Current, or Completed")
    asset_id: str = Field(..., min_length=1, description="Associated primary asset ID")

    @field_validator("exhibition_id", "name", "asset_id", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty.")
        return value


class ExhibitionCreate(ExhibitionBase):
    pass


class ExhibitionResponse(ExhibitionBase):
    pass


# Feedback Models
class FeedbackCreate(BaseModel):
    exhibition_id: str = Field(..., min_length=1, description="Target exhibition ID")
    rating: int = Field(..., ge=1, le=5, description="Visitor rating from 1 to 5")
    comment: Optional[str] = Field(default="", description="Visitor review or comment")

    @field_validator("exhibition_id", mode="before")
    @classmethod
    def strip_id(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Exhibition ID cannot be empty.")
        return value


class FeedbackResponse(BaseModel):
    id: int
    exhibition_id: str
    rating: int
    comment: Optional[str]


class ExhibitionRatingSummary(BaseModel):
    exhibition_id: str
    name: str
    average_rating: float
    feedback_count: int
    comments: List[str]


# Dashboard Models
class DashboardStats(BaseModel):
    total_assets: int
    active_projects: int
    total_archives: int
    current_exhibitions: int
    assets_needing_attention: int


# =============================================================================
# Database Explorer Models
# =============================================================================
class ExplorerEntitySummary(BaseModel):
    id: str = Field(..., description="Primary identifier of entity")
    label: str = Field(..., description="Neo4j node label (e.g. HeritageAsset, ConservationProject)")
    name: str = Field(default="", description="Display name or title of entity")
    subtitle: str = Field(default="", description="Useful secondary info (e.g. location, period, status, amount)")
    properties: dict = Field(default_factory=dict, description="Concise property key-values")


class ExplorerInventoryResponse(BaseModel):
    total: int = Field(..., description="Total count of matching entities")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Page size limit")
    total_pages: int = Field(..., description="Total available pages")
    items: List[ExplorerEntitySummary] = Field(default_factory=list, description="Page of entities")


class ExplorerRelationshipItem(BaseModel):
    rel_type: str = Field(..., description="Neo4j relationship type (e.g. MANAGES, CONSERVES)")
    direction: str = Field(..., description="'outgoing' (source -> target) or 'incoming' (source <- target)")
    target_id: str = Field(..., description="Neighbor entity ID")
    target_label: str = Field(..., description="Neighbor entity Neo4j label")
    target_name: str = Field(default="", description="Neighbor entity name or title")


class ExplorerEntityDetail(BaseModel):
    id: str = Field(..., description="Entity ID")
    label: str = Field(..., description="Neo4j label")
    properties: dict = Field(default_factory=dict, description="All actual properties stored on the node")
    relationships: List[ExplorerRelationshipItem] = Field(default_factory=list, description="Connected relationships")
    management_url: Optional[str] = Field(default=None, description="Frontend management URL if applicable")


class ExplorerGraphNode(BaseModel):
    id: str = Field(..., description="Unique node ID in graph")
    label: str = Field(..., description="Neo4j node label")
    name: str = Field(default="", description="Node display name or title")
    subtitle: str = Field(default="", description="Concise subtitle")
    properties: dict = Field(default_factory=dict, description="Node properties")


class ExplorerGraphEdge(BaseModel):
    id: str = Field(..., description="Edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Neo4j relationship type")
    label: str = Field(default="", description="Display label for the edge")


class ExplorerGraphResponse(BaseModel):
    nodes: List[ExplorerGraphNode] = Field(default_factory=list)
    edges: List[ExplorerGraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    truncated: bool = False
