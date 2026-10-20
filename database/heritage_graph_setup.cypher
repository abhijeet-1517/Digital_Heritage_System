// =====================================================================
// Heritage Conservation Graph - Neo4j setup script
// Run top to bottom. Every statement uses MERGE, so it is safe to re-run.
// =====================================================================


// ---------------------------------------------------------------------
// 1. Constraints
// ---------------------------------------------------------------------
CREATE CONSTRAINT asset_id_unique IF NOT EXISTS
FOR (a:HeritageAsset)
REQUIRE a.asset_id IS UNIQUE;

CREATE CONSTRAINT org_id_unique IF NOT EXISTS
FOR (o:Organization)
REQUIRE o.org_id IS UNIQUE;

CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:ConservationProject)
REQUIRE p.project_id IS UNIQUE;


// ---------------------------------------------------------------------
// 2. Supporting nodes
// ---------------------------------------------------------------------
MERGE (o:Organization {org_id: 'org001'})
SET o.name = 'National Cultural Heritage Organization'

MERGE (p:ConservationProject {project_id: 'cp001'})
SET p.name           = 'Heritage Restoration Project',
    p.funding_amount = 500000,
    p.status         = 'Ongoing'

MERGE (d:DigitalArchive {archive_id: 'da001'})
SET d.type        = '3D Scan',
    d.description = 'Digital documentation of heritage asset'

MERGE (r:Researcher {researcher_id: 'r001'})
SET r.name         = 'Heritage Researcher',
    r.access_level = 'Approved'

MERGE (e:Exhibition {exhibition_id: 'ex001'})
SET e.name = 'Indian Heritage Exhibition',
    e.type = 'Physical and Virtual'

MERGE (f:VisitorFeedback {feedback_id: 'f001'})
SET f.rating   = 5,
    f.comments = 'Excellent heritage presentation'

MERGE (rep:PreservationReport {report_id: 'pr001'})
SET rep.condition            = 'Good',
    rep.funding_utilized     = 150000,
    rep.restoration_progress = '30 percent';


// ---------------------------------------------------------------------
// 3. Heritage assets
// ---------------------------------------------------------------------
MERGE (a:HeritageAsset {asset_id: 'h001'})
SET a.name                    = 'Brihadisvara Temple',
    a.type                    = 'Temple',
    a.location                = 'Thanjavur, Tamil Nadu',
    a.period                  = 'Chola period',
    a.condition               = 'Good',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Maintained',
    a.historical_significance = 'Important example of Chola architecture';

MERGE (a:HeritageAsset {asset_id: 'h002'})
SET a.name                    = 'Ajanta Caves',
    a.type                    = 'Cave Monuments',
    a.location                = 'Aurangabad district, Maharashtra',
    a.period                  = '2nd century BCE to 6th century CE',
    a.condition               = 'Needs Monitoring',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Ancient Buddhist cave monuments known for paintings and sculptures';

MERGE (a:HeritageAsset {asset_id: 'h003'})
SET a.name                    = 'Konark Sun Temple',
    a.type                    = 'Temple',
    a.location                = 'Konark, Odisha',
    a.period                  = '13th century CE',
    a.condition               = 'Needs Restoration',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Historic Sun Temple renowned for its Kalinga architecture and stone chariot design';

MERGE (a:HeritageAsset {asset_id: 'h004'})
SET a.name                    = 'Taj Mahal',
    a.location                = 'Agra, Uttar Pradesh',
    a.period                  = '17th century CE',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Mughal mausoleum known for its marble architecture';

MERGE (a:HeritageAsset {asset_id: 'h005'})
SET a.name                    = 'Red Fort',
    a.location                = 'Delhi',
    a.period                  = '17th century CE',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Historic Mughal fort and symbol of Indian independence';

MERGE (a:HeritageAsset {asset_id: 'h006'})
SET a.name                    = 'Hampi',
    a.location                = 'Vijayanagara district, Karnataka',
    a.period                  = '14th to 16th century CE',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Ruins of the Vijayanagara Empire';

MERGE (a:HeritageAsset {asset_id: 'h007'})
SET a.name                    = 'Khajuraho Monuments',
    a.location                = 'Madhya Pradesh',
    a.period                  = '10th to 11th century CE',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Temples renowned for Nagara architecture and sculptures';

MERGE (a:HeritageAsset {asset_id: 'h008'})
SET a.name                    = 'Sanchi Stupa',
    a.location                = 'Sanchi, Madhya Pradesh',
    a.period                  = '3rd century BCE onwards',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Important Buddhist monument and pilgrimage site';

MERGE (a:HeritageAsset {asset_id: 'h009'})
SET a.name                    = 'Qutub Minar',
    a.location                = 'Delhi',
    a.period                  = '12th to 13th century CE',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Historic minaret representing Indo-Islamic architecture';

MERGE (a:HeritageAsset {asset_id: 'h010'})
SET a.name                    = 'Group of Monuments at Mahabalipuram',
    a.location                = 'Mahabalipuram, Tamil Nadu',
    a.period                  = '7th to 8th century CE',
    a.ownership               = 'Government protected heritage',
    a.preservation_status     = 'Protected',
    a.historical_significance = 'Pallava-era rock-cut monuments and structural temples';


// ---------------------------------------------------------------------
// 4. Relationships
// ---------------------------------------------------------------------

// 4a. Organization, project, archive and exhibition links for all assets
MATCH (o:Organization {org_id: 'org001'})
MATCH (p:ConservationProject {project_id: 'cp001'})
MATCH (d:DigitalArchive {archive_id: 'da001'})
MATCH (e:Exhibition {exhibition_id: 'ex001'})
MATCH (a:HeritageAsset)
WHERE a.asset_id IN ['h001', 'h002', 'h003', 'h004', 'h005',
                     'h006', 'h007', 'h008', 'h009', 'h010']
MERGE (o)-[:MANAGES]->(a)
MERGE (p)-[:CONSERVES]->(a)
MERGE (a)-[:DOCUMENTED_IN]->(d)
MERGE (a)-[:FEATURED_IN]->(e);

// 4b. Links between the supporting nodes
MATCH (o:Organization {org_id: 'org001'})
MATCH (p:ConservationProject {project_id: 'cp001'})
MATCH (d:DigitalArchive {archive_id: 'da001'})
MATCH (r:Researcher {researcher_id: 'r001'})
MATCH (e:Exhibition {exhibition_id: 'ex001'})
MATCH (f:VisitorFeedback {feedback_id: 'f001'})
MERGE (o)-[:MANAGES]->(p)
MERGE (r)-[:ACCESSES]->(d)
MERGE (f)-[:GIVEN_FOR]->(e);

// 4c. Preservation report (covers the first three assets)
MATCH (rep:PreservationReport {report_id: 'pr001'})
MATCH (a:HeritageAsset)
WHERE a.asset_id IN ['h001', 'h002', 'h003']
MERGE (rep)-[:REPORTS_ON]->(a);


// ---------------------------------------------------------------------
// 5. Verification (optional)
// ---------------------------------------------------------------------

// All assets
MATCH (a:HeritageAsset)
RETURN a.asset_id AS id,
       a.name AS heritage_site,
       a.location AS location,
       a.period AS period,
       a.preservation_status AS status
ORDER BY a.asset_id;

// Full graph
MATCH (n)
OPTIONAL MATCH (n)-[r]-(m)
RETURN n, r, m;
