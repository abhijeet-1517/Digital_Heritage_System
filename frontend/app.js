const API_BASE = "/api";

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            ...(options.body ? {
                "Content-Type": "application/json"
            } : {}),
            ...options.headers
        }
    });

    if (!response.ok) {
        let message = `Request failed (${response.status})`;

        try {
            const errorData = await response.json();
            message = errorData.detail || errorData.message || message;
        } catch {
            // Keep the default error message if the response is not JSON.
        }

        throw new Error(message);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

function showMessage(elementId, message, type = "info") {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.className = `message ${type}`;
    element.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function formToObject(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function formatCurrency(amount) {
    const num = Number(amount ?? 0);
    return "₹" + num.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


// =============================================================================
// Heritage Assets Module
// =============================================================================
let cachedAssets = [];

async function loadAssets() {
    const tbody = document.getElementById("assets-table-body");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6">Loading assets...</td></tr>';
    }

    try {
        const result = await apiRequest("/assets");
        const assets = Array.isArray(result) ? result : (result.assets || []);

        cachedAssets = assets;
        displayAssets(assets);
        populateAssetSelectors(assets);

        const searchInput = document.getElementById("asset-search");
        if (searchInput && searchInput.value.trim()) {
            filterAssets(searchInput.value);
        }
    } catch (error) {
        showMessage("assets-message", error.message || "Unable to load assets.", "error");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6">Unable to load assets.</td></tr>';
        }
    }
}

function displayAssets(assets) {
    const tbody = document.getElementById("assets-table-body");
    if (!tbody) return;

    if (!assets || assets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No assets found.</td></tr>';
        return;
    }

    tbody.innerHTML = assets.map(asset => `
        <tr>
            <td>${escapeHTML(asset.asset_id)}</td>
            <td><strong>${escapeHTML(asset.name)}</strong></td>
            <td>${escapeHTML(asset.location)}</td>
            <td>${escapeHTML(asset.period || "—")}</td>
            <td>
                <span class="status">
                    ${escapeHTML(asset.preservation_status)}
                </span>
            </td>
            <td>
                <button type="button" data-view-asset="${escapeHTML(asset.asset_id)}">
                    View
                </button>
                <button type="button" data-edit-asset="${escapeHTML(asset.asset_id)}">
                    Update Status
                </button>
                <button type="button" class="button-danger" data-delete-asset="${escapeHTML(asset.asset_id)}">
                    Delete
                </button>
            </td>
        </tr>
    `).join("");
}

function populateAssetSelectors(assets) {
    const selectorIds = [
        "project-asset",
        "restoration-asset",
        "archive-asset",
        "exhibition-asset"
    ];

    selectorIds.forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;

        const previousValue = select.value;
        select.replaceChildren(new Option("Select an asset", ""));

        assets.forEach(asset => {
            const option = new Option(
                `${asset.name} (${asset.asset_id})`,
                asset.asset_id
            );
            select.add(option);
        });

        if (assets.some(asset => asset.asset_id === previousValue)) {
            select.value = previousValue;
        }
    });
}

function filterAssets(searchTerm) {
    const query = searchTerm.trim().toLowerCase();
    const filteredAssets = cachedAssets.filter(asset =>
        String(asset.name ?? "").toLowerCase().includes(query) ||
        String(asset.asset_id ?? "").toLowerCase().includes(query) ||
        String(asset.location ?? "").toLowerCase().includes(query) ||
        String(asset.period ?? "").toLowerCase().includes(query)
    );
    displayAssets(filteredAssets);
}

async function addAsset(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formToObject(form);

    try {
        await apiRequest("/assets", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();
        showMessage("assets-message", "Heritage asset added successfully.", "success");
        await loadAssets();
    } catch (error) {
        showMessage("assets-message", error.message, "error");
    }
}

function initializeAssetsPage() {
    const form = document.getElementById("asset-form");
    if (form) {
        form.addEventListener("submit", addAsset);
    }

    const searchForm = document.getElementById("asset-search-form");
    if (searchForm) {
        searchForm.addEventListener("submit", event => {
            event.preventDefault();
            const query = document.getElementById("asset-search")?.value || "";
            filterAssets(query);
        });
    }

    const clearButton = document.getElementById("clear-asset-search");
    if (clearButton) {
        clearButton.addEventListener("click", () => {
            const input = document.getElementById("asset-search");
            if (input) input.value = "";
            displayAssets(cachedAssets);
        });
    }

    const searchInput = document.getElementById("asset-search");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            filterAssets(searchInput.value);
        });
    }

    const assetsTableBody = document.getElementById("assets-table-body");
    if (assetsTableBody) {
        assetsTableBody.addEventListener("click", async event => {
            const viewButton = event.target.closest("[data-view-asset]");
            const updateButton = event.target.closest("[data-edit-asset]");

            if (viewButton) {
                const assetId = viewButton.dataset.viewAsset;
                const asset = cachedAssets.find(item => String(item.asset_id) === assetId);
                if (!asset) return;

                const details = document.getElementById("asset-details");
                const content = document.getElementById("asset-details-content");
                if (details && content) {
                    content.textContent = [
                        `Asset ID: ${asset.asset_id}`,
                        `Name: ${asset.name}`,
                        `Location: ${asset.location}`,
                        `Period: ${asset.period || "Not specified"}`,
                        `Preservation status: ${asset.preservation_status}`,
                        `Description: ${asset.description || "Not specified"}`
                    ].join("\n");
                    content.style.whiteSpace = "pre-line";
                    details.hidden = false;
                    details.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }
            }

            if (updateButton) {
                const assetId = updateButton.dataset.editAsset;
                const asset = cachedAssets.find(item => String(item.asset_id) === assetId);
                if (!asset) return;

                const newStatus = window.prompt(
                    "Enter the new preservation status (e.g. Good, Needs Attention, Critical):",
                    asset.preservation_status
                );
                if (newStatus === null || !newStatus.trim()) return;

                try {
                    await apiRequest(`/assets/${encodeURIComponent(assetId)}`, {
                        method: "PUT",
                        body: JSON.stringify({ preservation_status: newStatus.trim() })
                    });
                    showMessage("assets-message", `Asset ${assetId} status updated successfully.`, "success");
                    await loadAssets();
                } catch (error) {
                    showMessage("assets-message", error.message, "error");
                }
            }

            const deleteButton = event.target.closest("[data-delete-asset]");
            if (deleteButton) {
                const assetId = deleteButton.dataset.deleteAsset;
                const asset = cachedAssets.find(item => String(item.asset_id) === assetId);
                const assetName = asset ? asset.name : assetId;

                const confirmed = window.confirm(
                    `Are you sure you want to delete heritage asset "${assetName}" (${assetId})?\n\nThis will safely remove the asset node from the HeritageGraph database if there are no active dependencies.`
                );
                if (!confirmed) return;

                try {
                    deleteButton.disabled = true;
                    await apiRequest(`/assets/${encodeURIComponent(assetId)}`, {
                        method: "DELETE"
                    });
                    showMessage("assets-message", `Heritage asset "${assetName}" (${assetId}) was deleted successfully.`, "success");
                    
                    // Hide details panel if showing the deleted asset
                    const details = document.getElementById("asset-details");
                    if (details && !details.hidden) {
                        const content = document.getElementById("asset-details-content");
                        if (content && content.textContent.includes(assetId)) {
                            details.hidden = true;
                        }
                    }

                    await loadAssets();
                } catch (error) {
                    showMessage("assets-message", error.message || "Failed to delete asset.", "error");
                    deleteButton.disabled = false;
                }
            }
        });
    }

    loadAssets();
}


// =============================================================================
// Dashboard Overview Module
// =============================================================================
async function loadDashboardStats() {
    try {
        const stats = await apiRequest("/dashboard/stats");

        const totalAssetsEl = document.getElementById("total-assets");
        const activeProjectsEl = document.getElementById("active-projects");
        const totalArchivesEl = document.getElementById("total-archives");
        const currentExhibitionsEl = document.getElementById("current-exhibitions");
        const attentionEl = document.getElementById("assets-needing-attention");

        if (totalAssetsEl) totalAssetsEl.textContent = stats.total_assets ?? 0;
        if (activeProjectsEl) activeProjectsEl.textContent = stats.active_projects ?? 0;
        if (totalArchivesEl) totalArchivesEl.textContent = stats.total_archives ?? 0;
        if (currentExhibitionsEl) currentExhibitionsEl.textContent = stats.current_exhibitions ?? 0;
        if (attentionEl) attentionEl.textContent = stats.assets_needing_attention ?? 0;
    } catch (error) {
        showMessage("dashboard-message", error.message || "Unable to load dashboard statistics.", "error");
    }
}

function initializeDashboardPage() {
    loadDashboardStats();
}


// =============================================================================
// Conservation Management Module
// =============================================================================
async function loadConservationProjects() {
    const tbody = document.getElementById("projects-table-body");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6">Loading projects...</td></tr>';
    }

    try {
        const projects = await apiRequest("/conservation/projects");
        if (!tbody) return;

        if (!projects || projects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No conservation projects found.</td></tr>';
            return;
        }

        tbody.innerHTML = projects.map(p => `
            <tr>
                <td>${escapeHTML(p.project_id)}</td>
                <td><strong>${escapeHTML(p.project_name)}</strong></td>
                <td>${escapeHTML(p.asset_id)}</td>
                <td>${formatCurrency(p.budget)}</td>
                <td>
                    <span class="status">${escapeHTML(p.status)}</span>
                </td>
                <td>
                    <button type="button" data-view-history="${escapeHTML(p.asset_id)}">
                        History
                    </button>
                    <button type="button" class="button-danger" data-delete-project="${escapeHTML(p.project_id)}" data-project-name="${escapeHTML(p.project_name)}">
                        Delete
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (error) {
        showMessage("conservation-message", error.message || "Unable to load conservation projects.", "error");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6">Unable to load projects.</td></tr>';
        }
    }
}

async function loadRestorationHistory(assetId) {
    const container = document.getElementById("restoration-history");
    if (!container) return;

    if (!assetId) {
        container.textContent = "Select an asset to view its restoration history.";
        return;
    }

    container.textContent = "Loading history for selected asset...";

    try {
        const history = await apiRequest(`/conservation/history/${encodeURIComponent(assetId)}`);
        if (!history || history.length === 0) {
            container.textContent = `No conservation records found for asset ${assetId}.`;
            return;
        }

        container.innerHTML = `
            <div class="table-wrapper" style="margin-top: 12px;">
                <table>
                    <thead>
                        <tr>
                            <th>Project ID</th>
                            <th>Project Name</th>
                            <th>Budget</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(item => `
                            <tr>
                                <td>${escapeHTML(item.project_id)}</td>
                                <td>${escapeHTML(item.project_name)}</td>
                                <td>${formatCurrency(item.budget)}</td>
                                <td><span class="status">${escapeHTML(item.status)}</span></td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        container.textContent = error.message || "Unable to load restoration history.";
    }
}

async function createConservationProject(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formToObject(form);

    data.budget = parseFloat(data.budget);

    try {
        await apiRequest("/conservation/projects", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();
        showMessage("conservation-message", "Conservation project created successfully.", "success");
        await loadConservationProjects();
    } catch (error) {
        showMessage("conservation-message", error.message, "error");
    }
}

function initializeConservationPage() {
    loadAssets();
    loadConservationProjects();

    const form = document.getElementById("project-form");
    if (form) {
        form.addEventListener("submit", createConservationProject);
    }

    const restorationSelect = document.getElementById("restoration-asset");
    if (restorationSelect) {
        restorationSelect.addEventListener("change", event => {
            loadRestorationHistory(event.target.value);
        });
    }

    const projectsTable = document.getElementById("projects-table-body");
    if (projectsTable) {
        projectsTable.addEventListener("click", async event => {
            const btn = event.target.closest("[data-view-history]");
            if (btn) {
                const assetId = btn.dataset.viewHistory;
                const select = document.getElementById("restoration-asset");
                if (select) {
                    select.value = assetId;
                    loadRestorationHistory(assetId);
                    select.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }
            }

            const deleteBtn = event.target.closest("[data-delete-project]");
            if (deleteBtn) {
                const projectId = deleteBtn.dataset.deleteProject;
                const projectName = deleteBtn.dataset.projectName || projectId;

                const confirmed = window.confirm(
                    `Are you sure you want to delete conservation project "${projectName}" (${projectId})?\n\nThis will safely remove the project node from HeritageGraph.`
                );
                if (!confirmed) return;

                try {
                    deleteBtn.disabled = true;
                    await apiRequest(`/conservation/projects/${encodeURIComponent(projectId)}`, {
                        method: "DELETE"
                    });
                    showMessage("conservation-message", `Conservation project "${projectName}" (${projectId}) deleted successfully.`, "success");
                    await loadConservationProjects();

                    // Refresh history if active asset selection matches
                    const currentAsset = document.getElementById("restoration-asset")?.value;
                    if (currentAsset) {
                        loadRestorationHistory(currentAsset);
                    }
                } catch (error) {
                    showMessage("conservation-message", error.message || "Failed to delete project.", "error");
                    deleteBtn.disabled = false;
                }
            }
        });
    }
}


// =============================================================================
// Funding Module
// =============================================================================
async function loadFundingReport() {
    const tbody = document.getElementById("funding-table-body");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5">Loading report...</td></tr>';
    }

    try {
        const report = await apiRequest("/funding");
        const summary = report.summary || {};
        const records = report.records || [];

        const allocatedEl = document.getElementById("funding-allocated");
        const utilizedEl = document.getElementById("funding-utilized");
        const remainingEl = document.getElementById("funding-remaining");
        const percentageEl = document.getElementById("funding-percentage");

        if (allocatedEl) allocatedEl.textContent = formatCurrency(summary.allocated);
        if (utilizedEl) utilizedEl.textContent = formatCurrency(summary.utilized);
        if (remainingEl) remainingEl.textContent = formatCurrency(summary.remaining);
        if (percentageEl) percentageEl.textContent = summary.percentage || "0.0%";

        if (!tbody) return;

        if (records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No funding records found.</td></tr>';
            return;
        }

        tbody.innerHTML = records.map(r => `
            <tr>
                <td><strong>${escapeHTML(r.project_id)}</strong></td>
                <td>${formatCurrency(r.allocated_amount)}</td>
                <td>${formatCurrency(r.utilized_amount)}</td>
                <td>${formatCurrency(r.remaining)}</td>
                <td>
                    <span class="status">${escapeHTML(r.percentage)}</span>
                </td>
                <td>
                    <button type="button" class="button-danger" data-delete-funding="${escapeHTML(r.funding_id)}" data-project-id="${escapeHTML(r.project_id)}">
                        Delete
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (error) {
        showMessage("funding-message", error.message || "Unable to load funding report.", "error");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6">Unable to load report.</td></tr>';
        }
    }
}

async function saveFunding(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formToObject(form);

    data.allocated_amount = parseFloat(data.allocated_amount);
    data.utilized_amount = parseFloat(data.utilized_amount || 0);

    try {
        await apiRequest("/funding", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();
        showMessage("funding-message", "Funding allocated successfully.", "success");
        await loadFundingReport();
    } catch (error) {
        showMessage("funding-message", error.message, "error");
    }
}

function initializeFundingPage() {
    loadFundingReport();

    const form = document.getElementById("funding-form");
    if (form) {
        form.addEventListener("submit", saveFunding);
    }

    const fundingTable = document.getElementById("funding-table-body");
    if (fundingTable) {
        fundingTable.addEventListener("click", async event => {
            const deleteBtn = event.target.closest("[data-delete-funding]");
            if (deleteBtn) {
                const fundingId = deleteBtn.dataset.deleteFunding;
                const projectId = deleteBtn.dataset.projectId || "";

                const confirmed = window.confirm(
                    `Are you sure you want to delete funding record "${fundingId}" for project "${projectId}"?\n\nThis will safely remove the funding allocation node and update utilization totals.`
                );
                if (!confirmed) return;

                try {
                    deleteBtn.disabled = true;
                    await apiRequest(`/funding/${encodeURIComponent(fundingId)}`, {
                        method: "DELETE"
                    });
                    showMessage("funding-message", `Funding record "${fundingId}" deleted successfully.`, "success");
                    await loadFundingReport();
                } catch (error) {
                    showMessage("funding-message", error.message || "Failed to delete funding record.", "error");
                    deleteBtn.disabled = false;
                }
            }
        });
    }
}


// =============================================================================
// Digital Archives Module
// =============================================================================
let cachedArchives = [];

async function loadArchives(searchTerm = "") {
    const tbody = document.getElementById("archives-table-body");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5">Loading archives...</td></tr>';
    }

    try {
        const query = searchTerm ? `?query=${encodeURIComponent(searchTerm)}` : "";
        const archives = await apiRequest(`/archives${query}`);

        cachedArchives = Array.isArray(archives) ? archives : [];
        if (!tbody) return;

        if (cachedArchives.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No archive records found.</td></tr>';
            return;
        }

        tbody.innerHTML = cachedArchives.map(a => `
            <tr>
                <td>${escapeHTML(a.archive_id)}</td>
                <td><strong>${escapeHTML(a.title)}</strong></td>
                <td>${escapeHTML(a.asset_id)}</td>
                <td><code>${escapeHTML(a.file_reference)}</code></td>
                <td>
                    <span class="status">${escapeHTML(a.access_level)}</span>
                </td>
                <td>
                    <button type="button" class="button-danger" data-delete-archive="${escapeHTML(a.archive_id)}" data-archive-title="${escapeHTML(a.title)}">
                        Delete
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (error) {
        showMessage("archives-message", error.message || "Unable to load archive records.", "error");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6">Unable to load archives.</td></tr>';
        }
    }
}

async function registerArchive(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formToObject(form);

    try {
        await apiRequest("/archives", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();
        showMessage("archives-message", "Digital archive registered successfully.", "success");
        await loadArchives();
    } catch (error) {
        showMessage("archives-message", error.message, "error");
    }
}

function initializeArchivesPage() {
    loadAssets();
    loadArchives();

    const form = document.getElementById("archive-form");
    if (form) {
        form.addEventListener("submit", registerArchive);
    }

    const searchButton = document.getElementById("archive-search-button");
    if (searchButton) {
        searchButton.addEventListener("click", () => {
            const query = document.getElementById("archive-search")?.value || "";
            loadArchives(query);
        });
    }

    const clearButton = document.getElementById("archive-clear-button");
    if (clearButton) {
        clearButton.addEventListener("click", () => {
            const input = document.getElementById("archive-search");
            if (input) input.value = "";
            loadArchives("");
        });
    }

    const searchInput = document.getElementById("archive-search");
    if (searchInput) {
        searchInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                loadArchives(searchInput.value);
            }
        });
    }

    const archivesTable = document.getElementById("archives-table-body");
    if (archivesTable) {
        archivesTable.addEventListener("click", async event => {
            const deleteBtn = event.target.closest("[data-delete-archive]");
            if (deleteBtn) {
                const archiveId = deleteBtn.dataset.deleteArchive;
                const archiveTitle = deleteBtn.dataset.archiveTitle || archiveId;

                const confirmed = window.confirm(
                    `Are you sure you want to delete digital archive "${archiveTitle}" (${archiveId})?\n\nThis will safely remove the archive document node from HeritageGraph.`
                );
                if (!confirmed) return;

                try {
                    deleteBtn.disabled = true;
                    await apiRequest(`/archives/${encodeURIComponent(archiveId)}`, {
                        method: "DELETE"
                    });
                    showMessage("archives-message", `Digital archive "${archiveTitle}" (${archiveId}) deleted successfully.`, "success");
                    const currentSearch = document.getElementById("archive-search")?.value || "";
                    await loadArchives(currentSearch);
                } catch (error) {
                    showMessage("archives-message", error.message || "Failed to delete archive document.", "error");
                    deleteBtn.disabled = false;
                }
            }
        });
    }
}


// =============================================================================
// Exhibitions & Feedback Module
// =============================================================================
async function loadExhibitions() {
    const tbody = document.getElementById("exhibitions-table-body");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6">Loading exhibitions...</td></tr>';
    }

    try {
        const exhibitions = await apiRequest("/exhibitions");
        if (!tbody) return;

        if (!exhibitions || exhibitions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No exhibitions found.</td></tr>';
            return;
        }

        // Deduplicate by exhibition_id to safeguard against any repeated records
        const seen = new Set();
        const uniqueExhibitions = exhibitions.filter(e => {
            const key = (e.exhibition_id || "").toLowerCase();
            if (!key || seen.has(key)) return false;
            seen.add(key);
            return true;
        });

        tbody.innerHTML = uniqueExhibitions.map(e => `
            <tr>
                <td>${escapeHTML(e.exhibition_id)}</td>
                <td><strong>${escapeHTML(e.name)}</strong></td>
                <td>${escapeHTML(e.start_date)}</td>
                <td>${escapeHTML(e.end_date)}</td>
                <td><span class="status">${escapeHTML(e.status)}</span></td>
                <td>
                    <button type="button" class="button-danger" data-delete-exhibition="${escapeHTML(e.exhibition_id)}" data-exhibition-name="${escapeHTML(e.name)}">
                        Delete
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (error) {
        showMessage("exhibitions-message", error.message || "Unable to load exhibitions.", "error");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6">Unable to load exhibitions.</td></tr>';
        }
    }
}

async function loadExhibitionRatings() {
    const container = document.getElementById("exhibition-ratings");
    if (!container) return;

    try {
        const ratings = await apiRequest("/exhibitions/ratings");
        if (!ratings || ratings.length === 0) {
            container.innerHTML = '<p class="status">No ratings recorded yet.</p>';
            return;
        }

        container.innerHTML = `
            <div class="stats-grid" style="margin-top: 12px;">
                ${ratings.map(r => `
                    <article class="card">
                        <h3>${escapeHTML(r.name)} (${escapeHTML(r.exhibition_id)})</h3>
                        <p class="stat-value">${r.average_rating > 0 ? "★ " + r.average_rating : "No ratings"}</p>
                        <p><strong>${r.feedback_count}</strong> visitor review${r.feedback_count === 1 ? "" : "s"}</p>
                        ${r.comments && r.comments.length > 0 ? `
                            <details style="margin-top: 8px;">
                                <summary style="cursor: pointer; color: var(--primary);">View Comments (${r.comments.length})</summary>
                                <ul style="padding-left: 20px; margin-top: 6px;">
                                    ${r.comments.map(c => `<li><em>"${escapeHTML(c)}"</em></li>`).join("")}
                                </ul>
                            </details>
                        ` : ''}
                    </article>
                `).join("")}
            </div>
        `;
    } catch (error) {
        container.innerHTML = `<p class="message error">${escapeHTML(error.message || "Unable to load exhibition ratings.")}</p>`;
    }
}

async function createExhibition(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formToObject(form);

    try {
        await apiRequest("/exhibitions", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();
        showMessage("exhibitions-message", "Exhibition created successfully.", "success");
        await loadExhibitions();
        await loadExhibitionRatings();
    } catch (error) {
        showMessage("exhibitions-message", error.message, "error");
    }
}

async function submitFeedback(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formToObject(form);

    data.rating = parseInt(data.rating, 10);

    try {
        await apiRequest("/exhibitions/feedback", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();
        showMessage("exhibitions-message", "Visitor feedback submitted successfully. Thank you!", "success");
        await loadExhibitionRatings();
    } catch (error) {
        showMessage("exhibitions-message", error.message, "error");
    }
}

function initializeExhibitionsPage() {
    loadAssets();
    loadExhibitions();
    loadExhibitionRatings();

    const form = document.getElementById("exhibition-form");
    if (form) {
        form.addEventListener("submit", createExhibition);
    }

    const feedbackForm = document.getElementById("feedback-form");
    if (feedbackForm) {
        feedbackForm.addEventListener("submit", submitFeedback);
    }

    const exhibitionsTable = document.getElementById("exhibitions-table-body");
    if (exhibitionsTable) {
        exhibitionsTable.addEventListener("click", async event => {
            const deleteBtn = event.target.closest("[data-delete-exhibition]");
            if (deleteBtn) {
                const exhibitionId = deleteBtn.dataset.deleteExhibition;
                const exhibitionName = deleteBtn.dataset.exhibitionName || exhibitionId;

                const confirmed = window.confirm(
                    `Are you sure you want to delete exhibition "${exhibitionName}" (${exhibitionId})?\n\nThis will safely remove the exhibition and its visitor reviews from HeritageGraph.`
                );
                if (!confirmed) return;

                try {
                    deleteBtn.disabled = true;
                    await apiRequest(`/exhibitions/${encodeURIComponent(exhibitionId)}`, {
                        method: "DELETE"
                    });
                    showMessage("exhibitions-message", `Exhibition "${exhibitionName}" (${exhibitionId}) deleted successfully.`, "success");
                    await loadExhibitions();
                    await loadExhibitionRatings();
                } catch (error) {
                    showMessage("exhibitions-message", error.message || "Failed to delete exhibition.", "error");
                    deleteBtn.disabled = false;
                }
            }
        });
    }
}


// =============================================================================
// Global Page Router / Initializer on DOMContentLoaded
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
    // 1. Dashboard
    if (document.getElementById("total-assets")) {
        initializeDashboardPage();
    }

    // 2. Heritage Assets
    if (document.getElementById("asset-form")) {
        initializeAssetsPage();
    }

    // 3. Conservation Projects
    if (document.getElementById("project-form")) {
        initializeConservationPage();
    }

    // 4. Funding Management
    if (document.getElementById("funding-form")) {
        initializeFundingPage();
    }

    // 5. Digital Archives
    if (document.getElementById("archive-form")) {
        initializeArchivesPage();
    }

    // 6. Exhibitions and Visitor Feedback
    if (document.getElementById("exhibition-form")) {
        initializeExhibitionsPage();
    }
});
