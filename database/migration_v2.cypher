// ==============================================================================
// National Cultural Heritage Management System
// Migration Script v2: Non-destructive Schema Constraints & Funding Normalization
// ==============================================================================
// This migration is 100% IDEMPOTENT and NON-DESTRUCTIVE:
// 1. Adds uniqueness constraints for missing entity IDs (archive_id, exhibition_id, feedback_id, funding_id).
// 2. Normalizes existing records with frontend-compatible aliases (e.g. historical_significance <-> description).
// 3. Introduces dedicated (:Funding) node for existing project 'cp001' with [:ALLOCATED_TO] relationship,
//    ensuring single authoritative allocation/utilization tracking and avoiding double-counting.
// ==============================================================================

// ------------------------------------------------------------------------------
// Step 1: Create Uniqueness Constraints (safe if they already exist)
// ------------------------------------------------------------------------------
CREATE CONSTRAINT archive_id_unique IF NOT EXISTS
FOR (d:DigitalArchive)
REQUIRE d.archive_id IS UNIQUE;

CREATE CONSTRAINT exhibition_id_unique IF NOT EXISTS
FOR (e:Exhibition)
REQUIRE e.exhibition_id IS UNIQUE;

CREATE CONSTRAINT feedback_id_unique IF NOT EXISTS
FOR (f:VisitorFeedback)
REQUIRE f.feedback_id IS UNIQUE;

CREATE CONSTRAINT funding_id_unique IF NOT EXISTS
FOR (fd:Funding)
REQUIRE fd.funding_id IS UNIQUE;

// ------------------------------------------------------------------------------
// Step 2: Harmonize existing Heritage Asset properties
// (Preserves existing data, ensures both 'description' and 'historical_significance' exist)
// ------------------------------------------------------------------------------
MATCH (a:HeritageAsset)
SET a.description = coalesce(a.description, a.historical_significance, ''),
    a.historical_significance = coalesce(a.historical_significance, a.description, ''),
    a.condition = coalesce(a.condition, a.preservation_status, 'Good'),
    a.preservation_status = coalesce(a.preservation_status, a.condition, 'Good');

// ------------------------------------------------------------------------------
// Step 3: Harmonize Conservation Projects & create dedicated Funding node
// ------------------------------------------------------------------------------
MATCH (p:ConservationProject {project_id: 'cp001'})
SET p.project_name = coalesce(p.project_name, p.name, 'Heritage Restoration Project'),
    p.name = coalesce(p.name, p.project_name, 'Heritage Restoration Project'),
    p.budget = coalesce(p.budget, toFloat(p.funding_amount), 500000.0),
    p.funding_amount = coalesce(p.funding_amount, toInteger(p.budget), 500000);

// Authoritative Funding node linked to cp001
// (Allocated: 500000.0 from project, Utilized: 150000.0 from preservation report pr001)
MERGE (fd:Funding {funding_id: 'fd001'})
SET fd.project_id = 'cp001',
    fd.allocated_amount = 500000.0,
    fd.utilized_amount = 150000.0
WITH fd
MATCH (p:ConservationProject {project_id: 'cp001'})
MERGE (fd)-[:ALLOCATED_TO]->(p);

// ------------------------------------------------------------------------------
// Step 4: Harmonize Digital Archive properties
// ------------------------------------------------------------------------------
MATCH (d:DigitalArchive {archive_id: 'da001'})
SET d.title = coalesce(d.title, d.description, '3D Digital Scan Documentation'),
    d.file_reference = coalesce(d.file_reference, 'SCAN-DA001-3D.ply'),
    d.access_level = coalesce(d.access_level, 'Public'),
    d.asset_id = coalesce(d.asset_id, 'h001');

// ------------------------------------------------------------------------------
// Step 5: Harmonize Exhibition properties
// ------------------------------------------------------------------------------
MATCH (e:Exhibition {exhibition_id: 'ex001'})
SET e.start_date = coalesce(e.start_date, '2026-08-01'),
    e.end_date = coalesce(e.end_date, '2026-12-31'),
    e.status = coalesce(e.status, 'Current'),
    e.asset_id = coalesce(e.asset_id, 'h001');

// ------------------------------------------------------------------------------
// Step 6: Harmonize Visitor Feedback properties
// ------------------------------------------------------------------------------
MATCH (f:VisitorFeedback {feedback_id: 'f001'})
SET f.comment = coalesce(f.comment, f.comments, 'Excellent heritage presentation'),
    f.comments = coalesce(f.comments, f.comment, 'Excellent heritage presentation'),
    f.exhibition_id = coalesce(f.exhibition_id, 'ex001'),
    f.num_id = coalesce(f.num_id, 1);
