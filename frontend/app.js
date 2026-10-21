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
// Database Explorer Module
// =============================================================================
let explorerCurrentPage = 1;
const EXPLORER_PAGE_SIZE = 15;
let explorerActiveTab = "table"; // 'table' or 'graph'
let explorerGraphData = { nodes: [], edges: [] };
let explorerSelectedNodeId = null;
let explorerHoveredNodeId = null;
let explorerHoveredEdgeId = null;
let explorerPollingTimer = null;
let explorerGraphTransform = { x: 0, y: 0, scale: 1 };
let explorerGraphHasUserTransform = false;
let explorerNodePositions = {};
let explorerSimAnimFrame = null;
let explorerIsDragging = false;
let explorerDragStart = { x: 0, y: 0 };
let explorerDragNode = null;

async function loadExplorerInventory(page = 1) {
    explorerCurrentPage = page;
    const tbody = document.getElementById("explorer-table-body");
    const syncStatus = document.getElementById("sync-status");
    if (syncStatus) syncStatus.textContent = "Syncing...";

    const label = document.getElementById("explorer-label-filter")?.value || "";
    const search = document.getElementById("explorer-search-input")?.value || "";

    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5">Loading entity records...</td></tr>';
    }

    try {
        const queryParams = new URLSearchParams({
            page: String(page),
            page_size: String(EXPLORER_PAGE_SIZE),
        });
        if (label) queryParams.set("label", label);
        if (search) queryParams.set("search", search);

        const data = await apiRequest(`/explorer/entities?${queryParams.toString()}`);
        if (syncStatus) syncStatus.textContent = "Updated just now";

        if (!tbody) return;

        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No database entities found matching the current filters.</td></tr>';
            updateExplorerPagination(data.total, data.page, data.total_pages);
            return;
        }

        tbody.innerHTML = data.items.map(item => `
            <tr>
                <td><span class="entity-badge badge-${escapeHTML(item.label)}">${escapeHTML(item.label)}</span></td>
                <td><strong>${escapeHTML(item.id)}</strong></td>
                <td>${escapeHTML(item.name || "—")}</td>
                <td><span style="color: var(--muted); font-size: 0.9rem;">${escapeHTML(item.subtitle || "—")}</span></td>
                <td>
                    <button type="button" class="button" data-inspect-label="${escapeHTML(item.label)}" data-inspect-id="${escapeHTML(item.id)}" style="padding: 4px 10px; font-size: 0.85rem;">
                        Inspect
                    </button>
                </td>
            </tr>
        `).join("");

        updateExplorerPagination(data.total, data.page, data.total_pages);
    } catch (error) {
        if (syncStatus) syncStatus.textContent = "Error";
        showMessage("explorer-message", error.message || "Failed to load database entities.", "error");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5">Unable to load entity records.</td></tr>';
        }
    }
}

function updateExplorerPagination(total, page, totalPages) {
    const info = document.getElementById("explorer-pagination-info");
    const prevBtn = document.getElementById("explorer-prev-page");
    const nextBtn = document.getElementById("explorer-next-page");

    if (info) {
        info.textContent = `Page ${page} of ${totalPages} (${total} total entities)`;
    }
    if (prevBtn) {
        prevBtn.disabled = page <= 1;
    }
    if (nextBtn) {
        nextBtn.disabled = page >= totalPages;
    }
}

async function inspectExplorerEntity(label, entityId) {
    const card = document.getElementById("entity-inspector-card");
    const badge = document.getElementById("inspector-badge");
    const idEl = document.getElementById("inspector-id");
    const titleEl = document.getElementById("inspector-title");
    const propsEl = document.getElementById("inspector-properties");
    const relsEl = document.getElementById("inspector-relationships");
    const relCountEl = document.getElementById("inspector-rel-count");
    const mgmtLink = document.getElementById("inspector-mgmt-link");
    const expandBtn = document.getElementById("inspector-expand-graph-btn");

    if (card) {
        card.style.display = "block";
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    if (titleEl) titleEl.textContent = `Inspecting ${label} (${entityId})`;
    if (badge) {
        badge.className = `entity-badge badge-${escapeHTML(label)}`;
        badge.textContent = label;
    }
    if (idEl) idEl.textContent = entityId;

    if (propsEl) propsEl.innerHTML = '<p class="status">Loading properties...</p>';
    if (relsEl) relsEl.innerHTML = '<p class="status">Loading relationships...</p>';

    try {
        const detail = await apiRequest(`/explorer/entities/${encodeURIComponent(label)}/${encodeURIComponent(entityId)}`);

        // Render properties
        if (propsEl) {
            const keys = Object.keys(detail.properties || {}).sort();
            if (keys.length === 0) {
                propsEl.innerHTML = '<p style="color: var(--muted);">No properties stored on this node.</p>';
            } else {
                propsEl.innerHTML = keys.map(k => `
                    <div class="property-item">
                        <strong>${escapeHTML(k)}</strong>
                        <span>${escapeHTML(String(detail.properties[k]))}</span>
                    </div>
                `).join("");
            }
        }

        // Render relationships
        const rels = detail.relationships || [];
        if (relCountEl) relCountEl.textContent = String(rels.length);

        if (relsEl) {
            if (rels.length === 0) {
                relsEl.innerHTML = '<p style="color: var(--muted);">No connected relationships found for this entity.</p>';
            } else {
                relsEl.innerHTML = rels.map(r => {
                    const dirArrow = r.direction === "outgoing" ? "→" : "←";
                    const dirText = r.direction === "outgoing" ? "points to" : "connected from";
                    return `
                        <div class="relationship-chip">
                            <div>
                                <span style="font-weight: bold; color: var(--primary);">${escapeHTML(r.rel_type)}</span>
                                <span style="color: var(--muted); margin: 0 6px;">${dirArrow} (${dirText})</span>
                                <span class="entity-badge badge-${escapeHTML(r.target_label)}">${escapeHTML(r.target_label)}</span>
                                <strong style="margin-left: 6px;">${escapeHTML(r.target_id)}</strong>
                                ${r.target_name ? `<span style="color: var(--muted); margin-left: 6px;">"${escapeHTML(r.target_name)}"</span>` : ""}
                            </div>
                            <button type="button" class="button" data-inspect-label="${escapeHTML(r.target_label)}" data-inspect-id="${escapeHTML(r.target_id)}" style="padding: 3px 8px; font-size: 0.8rem;">
                                Inspect
                            </button>
                        </div>
                    `;
                }).join("");
            }
        }

        // Management page link
        if (mgmtLink) {
            if (detail.management_url) {
                mgmtLink.href = detail.management_url;
                mgmtLink.style.display = "inline-block";
            } else {
                mgmtLink.style.display = "none";
            }
        }

        // Expand in graph button
        if (expandBtn) {
            expandBtn.onclick = () => {
                switchExplorerTab("graph");
                loadExplorerGraph(label, entityId);
            };
        }

    } catch (error) {
        showMessage("explorer-message", error.message || "Failed to inspect entity.", "error");
    }
}

async function loadExplorerGraph(focusLabel = null, focusId = null, preserveTransform = false) {
    const syncStatus = document.getElementById("sync-status");
    if (syncStatus) syncStatus.textContent = "Loading graph...";

    const labelFilter = document.getElementById("explorer-label-filter")?.value || "";
    const relFilter = document.getElementById("explorer-rel-filter")?.value || "";

    const queryParams = new URLSearchParams({ limit: "50" });
    if (focusLabel && focusId) {
        queryParams.set("focus_label", focusLabel);
        queryParams.set("focus_id", focusId);
    } else if (labelFilter) {
        queryParams.set("label_filter", labelFilter);
    }
    if (relFilter) {
        queryParams.set("rel_filter", relFilter);
    }

    try {
        const data = await apiRequest(`/explorer/graph?${queryParams.toString()}`);
        explorerGraphData = data;
        renderExplorerGraphSVG(data, focusId, preserveTransform);
        if (syncStatus) syncStatus.textContent = "Graph updated";
    } catch (error) {
        if (syncStatus) syncStatus.textContent = "Graph error";
        showMessage("explorer-message", error.message || "Failed to load graph data.", "error");
    }
}

function getNodeColor(label) {
    const colors = {
        HeritageAsset: "#0284c7",
        ConservationProject: "#d97706",
        Funding: "#16a34a",
        DigitalArchive: "#9333ea",
        Exhibition: "#ea580c",
        VisitorFeedback: "#db2777",
        Organization: "#475569",
        Researcher: "#5b21b6",
        PreservationReport: "#475569",
    };
    return colors[label] || "#64748b";
}

function applyGraphTransform() {
    const contentGroup = document.getElementById("graph-content-group");
    const zoomLevelEl = document.getElementById("graph-zoom-level");
    if (contentGroup) {
        contentGroup.setAttribute(
            "transform",
            `translate(${explorerGraphTransform.x}, ${explorerGraphTransform.y}) scale(${explorerGraphTransform.scale})`
        );
    }
    if (zoomLevelEl) {
        zoomLevelEl.textContent = `${Math.round(explorerGraphTransform.scale * 100)}%`;
    }
}

function zoomExplorerGraph(deltaScale, clientOriginX = null, clientOriginY = null) {
    const svg = document.getElementById("explorer-graph-svg");
    if (!svg) return;

    const oldScale = explorerGraphTransform.scale;
    let newScale = oldScale * deltaScale;
    newScale = Math.max(0.2, Math.min(3.5, newScale));

    const rect = svg.getBoundingClientRect();
    const originX = (clientOriginX !== null) ? (clientOriginX - rect.left) : (rect.width / 2);
    const originY = (clientOriginY !== null) ? (clientOriginY - rect.top) : (rect.height / 2);

    // Zoom centered on origin point: (origin - newX) / newScale = (origin - oldX) / oldScale
    explorerGraphTransform.x = originX - (originX - explorerGraphTransform.x) * (newScale / oldScale);
    explorerGraphTransform.y = originY - (originY - explorerGraphTransform.y) * (newScale / oldScale);
    explorerGraphTransform.scale = newScale;
    explorerGraphHasUserTransform = true;

    applyGraphTransform();
}

function resetExplorerGraphView() {
    const svg = document.getElementById("explorer-graph-svg");
    const width = svg ? (svg.clientWidth || 800) : 800;
    const height = svg ? (svg.clientHeight || 560) : 560;

    explorerGraphTransform = { x: 0, y: 0, scale: 1 };
    explorerGraphHasUserTransform = false;
    applyGraphTransform();
}

function fitExplorerGraphView() {
    const svg = document.getElementById("explorer-graph-svg");
    if (!svg) return;

    const nodes = explorerGraphData.nodes || [];
    if (nodes.length === 0) {
        resetExplorerGraphView();
        return;
    }

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodes.forEach(n => {
        const p = explorerNodePositions[n.id];
        if (p) {
            minX = Math.min(minX, p.x - 30);
            maxX = Math.max(maxX, p.x + 30);
            minY = Math.min(minY, p.y - 30);
            maxY = Math.max(maxY, p.y + 30);
        }
    });

    if (minX === Infinity) {
        resetExplorerGraphView();
        return;
    }

    const bboxWidth = Math.max(100, maxX - minX);
    const bboxHeight = Math.max(100, maxY - minY);
    const svgWidth = svg.clientWidth || 800;
    const svgHeight = svg.clientHeight || 560;

    const scaleX = (svgWidth - 80) / bboxWidth;
    const scaleY = (svgHeight - 80) / bboxHeight;
    let targetScale = Math.min(scaleX, scaleY, 1.3);
    targetScale = Math.max(0.3, targetScale);

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    explorerGraphTransform.scale = targetScale;
    explorerGraphTransform.x = (svgWidth / 2) - (centerX * targetScale);
    explorerGraphTransform.y = (svgHeight / 2) - (centerY * targetScale);
    explorerGraphHasUserTransform = true;

    applyGraphTransform();
}

function showGraphTooltip(text, clientX, clientY) {
    const tooltip = document.getElementById("graph-tooltip");
    const viewport = document.getElementById("graph-viewport");
    if (!tooltip || !viewport) return;

    const rect = viewport.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;

    tooltip.textContent = text;
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
    tooltip.style.display = "block";
}

function hideGraphTooltip() {
    const tooltip = document.getElementById("graph-tooltip");
    if (tooltip) {
        tooltip.style.display = "none";
    }
}

function renderExplorerGraphSVG(data, focusId = null, preserveTransform = false) {
    const svg = document.getElementById("explorer-graph-svg");
    const nodesLayer = document.getElementById("graph-nodes-layer");
    const edgesLayer = document.getElementById("graph-edges-layer");
    const edgeLabelsLayer = document.getElementById("graph-edge-labels-layer");

    if (!svg || !nodesLayer || !edgesLayer) return;

    if (explorerSimAnimFrame) {
        cancelAnimationFrame(explorerSimAnimFrame);
        explorerSimAnimFrame = null;
    }

    nodesLayer.innerHTML = "";
    edgesLayer.innerHTML = "";
    if (edgeLabelsLayer) edgeLabelsLayer.innerHTML = "";

    const nodes = data.nodes || [];
    const edges = data.edges || [];

    if (nodes.length === 0) {
        nodesLayer.innerHTML = `
            <text x="50%" y="50%" text-anchor="middle" fill="#64748b" font-size="14">
                No graph entities found for the current filter.
            </text>
        `;
        return;
    }

    const width = svg.clientWidth || 800;
    const height = svg.clientHeight || 560;
    const centerX = width / 2;
    const centerY = height / 2;

    // Preserve positions of existing nodes, initialize new ones with jitter
    const currentPositions = {};
    const nodeDegree = {};
    nodes.forEach(n => { nodeDegree[n.id] = 0; });
    edges.forEach(e => {
        if (nodeDegree[e.source] !== undefined) nodeDegree[e.source]++;
        if (nodeDegree[e.target] !== undefined) nodeDegree[e.target]++;
    });

    nodes.forEach((node, idx) => {
        if (explorerNodePositions[node.id]) {
            currentPositions[node.id] = {
                x: explorerNodePositions[node.id].x,
                y: explorerNodePositions[node.id].y,
                vx: 0,
                vy: 0,
            };
        } else {
            const angle = (idx / nodes.length) * 2 * Math.PI;
            const dist = 120 + (idx % 4) * 45;
            currentPositions[node.id] = {
                x: centerX + Math.cos(angle) * dist + (Math.random() - 0.5) * 20,
                y: centerY + Math.sin(angle) * dist + (Math.random() - 0.5) * 20,
                vx: 0,
                vy: 0,
            };
        }
    });

    // Run force-directed relaxation simulation synchronously
    const iterations = nodes.length > 30 ? 65 : 100;
    const kRepel = 7500;
    const kAttract = 0.045;
    const idealEdgeLen = 140;

    for (let step = 0; step < iterations; step++) {
        const cooling = 1 - (step / iterations);

        // Repulsion between all node pairs
        for (let i = 0; i < nodes.length; i++) {
            const p1 = currentPositions[nodes[i].id];
            for (let j = i + 1; j < nodes.length; j++) {
                const p2 = currentPositions[nodes[j].id];
                let dx = p1.x - p2.x;
                let dy = p1.y - p2.y;
                let dist = Math.hypot(dx, dy) || 1;
                if (dist < 260) {
                    const force = (kRepel / (dist * dist)) * cooling;
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    p1.vx += fx;
                    p1.vy += fy;
                    p2.vx -= fx;
                    p2.vy -= fy;
                }
            }
        }

        // Attraction along edges
        edges.forEach(edge => {
            const p1 = currentPositions[edge.source];
            const p2 = currentPositions[edge.target];
            if (!p1 || !p2) return;
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const dist = Math.hypot(dx, dy) || 1;
            const force = (dist - idealEdgeLen) * kAttract * cooling;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            p1.vx += fx;
            p1.vy += fy;
            p2.vx -= fx;
            p2.vy -= fy;
        });

        // Center gravity pull
        nodes.forEach(node => {
            const p = currentPositions[node.id];
            p.vx += (centerX - p.x) * 0.015 * cooling;
            p.vy += (centerY - p.y) * 0.015 * cooling;

            // Apply velocity with damping
            p.x += Math.max(-25, Math.min(25, p.vx * 0.85));
            p.y += Math.max(-25, Math.min(25, p.vy * 0.85));
            p.vx = 0;
            p.vy = 0;
        });
    }

    explorerNodePositions = currentPositions;

    // Parallel edge grouping for offsets
    const pairGroups = {};
    edges.forEach(edge => {
        const key = edge.source < edge.target ? `${edge.source}#${edge.target}` : `${edge.target}#${edge.source}`;
        if (!pairGroups[key]) pairGroups[key] = [];
        pairGroups[key].push(edge);
    });

    const edgeOffsets = new Map();
    Object.values(pairGroups).forEach(group => {
        const count = group.length;
        group.forEach((edge, idx) => {
            let offset = 0;
            if (count > 1) {
                const step = 22;
                offset = (idx - (count - 1) / 2) * step;
                if (edge.source > edge.target) {
                    offset = -offset;
                }
            }
            edgeOffsets.set(edge, offset);
        });
    });

    // Render Edges
    edges.forEach(edge => {
        const src = explorerNodePositions[edge.source];
        const tgt = explorerNodePositions[edge.target];
        if (!src || !tgt) return;

        const isSourceActive = (edge.source === explorerSelectedNodeId || edge.source === explorerHoveredNodeId);
        const isTargetActive = (edge.target === explorerSelectedNodeId || edge.target === explorerHoveredNodeId);
        const isEdgeHovered = (explorerHoveredEdgeId === edge.id);
        const isHighlighted = isEdgeHovered || (isSourceActive && isTargetActive);
        const isConnected = isSourceActive || isTargetActive;

        let strokeColor = "#94a3b8";
        let strokeWidth = 1.6;
        let marker = "url(#arrowhead)";

        if (isHighlighted) {
            strokeColor = "#0284c7";
            strokeWidth = 2.8;
            marker = "url(#arrowhead-highlight)";
        } else if (isConnected) {
            strokeColor = "#173b35";
            strokeWidth = 2.2;
            marker = "url(#arrowhead-active)";
        }

        const offset = edgeOffsets.get(edge) || 0;
        const dx = tgt.x - src.x;
        const dy = tgt.y - src.y;
        const dist = Math.hypot(dx, dy) || 1;
        const ux = dx / dist;
        const uy = dy / dist;
        const nx = -uy;
        const ny = ux;

        const targetRadius = (edge.target === explorerSelectedNodeId || edge.target === focusId) ? 22 : 18;
        const sourceRadius = (edge.source === explorerSelectedNodeId || edge.source === focusId) ? 22 : 18;

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "graph-edge");
        path.setAttribute("stroke", strokeColor);
        path.setAttribute("stroke-width", strokeWidth);
        path.setAttribute("fill", "none");
        path.setAttribute("marker-end", marker);

        let midX, midY;

        if (Math.abs(offset) > 0.001) {
            const ctrlX = ((src.x + tgt.x) / 2) + nx * offset * 1.5;
            const ctrlY = ((src.y + tgt.y) / 2) + ny * offset * 1.5;

            // Compute tangent vectors at ends
            const toCtrlX = ctrlX - src.x;
            const toCtrlY = ctrlY - src.y;
            const dSource = Math.hypot(toCtrlX, toCtrlY) || 1;
            const startX = src.x + (toCtrlX / dSource) * sourceRadius;
            const startY = src.y + (toCtrlY / dSource) * sourceRadius;

            const fromCtrlX = tgt.x - ctrlX;
            const fromCtrlY = tgt.y - ctrlY;
            const dTarget = Math.hypot(fromCtrlX, fromCtrlY) || 1;
            const endX = tgt.x - (fromCtrlX / dTarget) * targetRadius;
            const endY = tgt.y - (fromCtrlY / dTarget) * targetRadius;

            path.setAttribute("d", `M ${startX} ${startY} Q ${ctrlX} ${ctrlY} ${endX} ${endY}`);
            midX = 0.25 * startX + 0.5 * ctrlX + 0.25 * endX;
            midY = 0.25 * startY + 0.5 * ctrlY + 0.25 * endY;
        } else {
            const startX = src.x + ux * sourceRadius;
            const startY = src.y + uy * sourceRadius;
            const endX = tgt.x - ux * targetRadius;
            const endY = tgt.y - uy * targetRadius;

            path.setAttribute("d", `M ${startX} ${startY} L ${endX} ${endY}`);
            midX = (startX + endX) / 2;
            midY = (startY + endY) / 2;
        }

        path.addEventListener("mouseenter", (e) => {
            explorerHoveredEdgeId = edge.id;
            showGraphTooltip(`${edge.source} —[${edge.type}]→ ${edge.target}`, e.clientX, e.clientY);
            renderExplorerGraphSVG(explorerGraphData, focusId, true);
        });
        path.addEventListener("mouseleave", () => {
            explorerHoveredEdgeId = null;
            hideGraphTooltip();
            renderExplorerGraphSVG(explorerGraphData, focusId, true);
        });

        edgesLayer.appendChild(path);

        // Edge label (show if highlighted/connected, or if graph is small <= 15 edges)
        const showLabel = isHighlighted || isConnected || edges.length <= 14;
        if (showLabel && edgeLabelsLayer) {
            const textGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
            const labelBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");

            text.setAttribute("class", "graph-edge-label");
            text.setAttribute("x", midX);
            text.setAttribute("y", midY - 3);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("fill", isHighlighted ? "#0284c7" : "#475569");
            text.textContent = edge.type;

            const labelWidth = edge.type.length * 6 + 6;
            labelBg.setAttribute("x", midX - labelWidth / 2);
            labelBg.setAttribute("y", midY - 12);
            labelBg.setAttribute("width", labelWidth);
            labelBg.setAttribute("height", 12);
            labelBg.setAttribute("fill", "#ffffff");
            labelBg.setAttribute("fill-opacity", "0.85");
            labelBg.setAttribute("rx", "2");

            textGroup.appendChild(labelBg);
            textGroup.appendChild(text);
            edgeLabelsLayer.appendChild(textGroup);
        }
    });

    // Render Nodes
    nodes.forEach(node => {
        const pos = explorerNodePositions[node.id];
        if (!pos) return;

        const isFocus = (node.id === focusId || node.id === explorerSelectedNodeId);
        const isHovered = (node.id === explorerHoveredNodeId);
        const nodeColor = getNodeColor(node.label);
        const radius = isFocus ? 22 : 18;

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("class", "graph-node");
        g.setAttribute("transform", `translate(${pos.x}, ${pos.y})`);

        // Node drag handling
        g.addEventListener("mousedown", (e) => {
            e.stopPropagation();
            explorerDragNode = node.id;
            explorerDragStart = { x: e.clientX, y: e.clientY };
        });

        g.addEventListener("mouseenter", (e) => {
            explorerHoveredNodeId = node.id;
            const fullTitle = `${node.name || node.id} (${node.label})`;
            showGraphTooltip(fullTitle, e.clientX, e.clientY);
        });

        g.addEventListener("mouseleave", () => {
            explorerHoveredNodeId = null;
            hideGraphTooltip();
        });

        g.addEventListener("click", (e) => {
            e.stopPropagation();
            explorerSelectedNodeId = node.id;
            inspectExplorerEntity(node.label, node.id);
            renderExplorerGraphSVG(explorerGraphData, node.id, true);
        });

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", 0);
        circle.setAttribute("cy", 0);
        circle.setAttribute("r", radius);
        circle.setAttribute("fill", nodeColor);
        circle.setAttribute("stroke", isFocus ? "#0f172a" : (isHovered ? "#38bdf8" : "#ffffff"));
        circle.setAttribute("stroke-width", isFocus ? 3.5 : (isHovered ? 3 : 2));
        g.appendChild(circle);

        // Node ID label (short & crisp)
        const textId = document.createElementNS("http://www.w3.org/2000/svg", "text");
        textId.setAttribute("x", 0);
        textId.setAttribute("y", 4);
        textId.setAttribute("text-anchor", "middle");
        textId.setAttribute("fill", "#ffffff");
        textId.setAttribute("font-size", "10");
        textId.setAttribute("font-weight", "bold");
        textId.setAttribute("pointer-events", "none");
        textId.textContent = node.id.length > 7 ? node.id.slice(0, 6) + "…" : node.id;
        g.appendChild(textId);

        // Node Title label below (always clear and legible)
        const textTitle = document.createElementNS("http://www.w3.org/2000/svg", "text");
        textTitle.setAttribute("x", 0);
        textTitle.setAttribute("y", radius + 14);
        textTitle.setAttribute("text-anchor", "middle");
        textTitle.setAttribute("fill", isFocus ? "#0f172a" : "#334155");
        textTitle.setAttribute("font-size", "10");
        textTitle.setAttribute("font-weight", isFocus ? "700" : "500");
        textTitle.setAttribute("pointer-events", "none");
        const displayName = node.name || node.id;
        textTitle.textContent = displayName.length > 15 ? displayName.slice(0, 14) + "…" : displayName;
        g.appendChild(textTitle);

        nodesLayer.appendChild(g);
    });

    if (!preserveTransform && !explorerGraphHasUserTransform) {
        fitExplorerGraphView();
    } else {
        applyGraphTransform();
    }
}

function switchExplorerTab(tab) {
    explorerActiveTab = tab;
    const tableBtn = document.getElementById("tab-btn-table");
    const graphBtn = document.getElementById("tab-btn-graph");
    const tableView = document.getElementById("explorer-table-view");
    const graphView = document.getElementById("explorer-graph-view");
    const relFilterContainer = document.getElementById("graph-rel-filter-container");
    const searchContainer = document.getElementById("table-search-container");

    if (tab === "table") {
        if (tableBtn) { tableBtn.className = "view-tab-btn active"; tableBtn.setAttribute("aria-selected", "true"); }
        if (graphBtn) { graphBtn.className = "view-tab-btn"; graphBtn.setAttribute("aria-selected", "false"); }
        if (tableView) tableView.style.display = "block";
        if (graphView) graphView.style.display = "none";
        if (relFilterContainer) relFilterContainer.style.display = "none";
        if (searchContainer) searchContainer.style.display = "block";
    } else {
        if (tableBtn) { tableBtn.className = "view-tab-btn"; tableBtn.setAttribute("aria-selected", "false"); }
        if (graphBtn) { graphBtn.className = "view-tab-btn active"; graphBtn.setAttribute("aria-selected", "true"); }
        if (tableView) tableView.style.display = "none";
        if (graphView) graphView.style.display = "block";
        if (relFilterContainer) relFilterContainer.style.display = "block";
        if (searchContainer) searchContainer.style.display = "none";
        loadExplorerGraph();
    }
}

function initializeExplorerPage() {
    loadExplorerInventory(1);

    // Tab buttons
    const tableBtn = document.getElementById("tab-btn-table");
    const graphBtn = document.getElementById("tab-btn-graph");
    if (tableBtn) tableBtn.addEventListener("click", () => switchExplorerTab("table"));
    if (graphBtn) graphBtn.addEventListener("click", () => switchExplorerTab("graph"));

    // Filter controls
    const filterBtn = document.getElementById("explorer-filter-btn");
    const clearBtn = document.getElementById("explorer-clear-btn");
    const refreshBtn = document.getElementById("explorer-refresh-btn");

    if (filterBtn) {
        filterBtn.addEventListener("click", () => {
            if (explorerActiveTab === "table") {
                loadExplorerInventory(1);
            } else {
                loadExplorerGraph();
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            const labelEl = document.getElementById("explorer-label-filter");
            const relEl = document.getElementById("explorer-rel-filter");
            const searchEl = document.getElementById("explorer-search-input");
            if (labelEl) labelEl.value = "";
            if (relEl) relEl.value = "";
            if (searchEl) searchEl.value = "";
            if (explorerActiveTab === "table") {
                loadExplorerInventory(1);
            } else {
                loadExplorerGraph();
            }
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            if (explorerActiveTab === "table") {
                loadExplorerInventory(explorerCurrentPage);
            } else {
                loadExplorerGraph(null, null, true);
            }
        });
    }

    // Graph Pan & Zoom Controls
    const zoomInBtn = document.getElementById("graph-zoom-in");
    const zoomOutBtn = document.getElementById("graph-zoom-out");
    const zoomResetBtn = document.getElementById("graph-zoom-reset");
    const fitViewBtn = document.getElementById("graph-fit-view");
    const svg = document.getElementById("explorer-graph-svg");

    if (zoomInBtn) zoomInBtn.addEventListener("click", () => zoomExplorerGraph(1.25));
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => zoomExplorerGraph(0.8));
    if (zoomResetBtn) zoomResetBtn.addEventListener("click", resetExplorerGraphView);
    if (fitViewBtn) fitViewBtn.addEventListener("click", fitExplorerGraphView);

    if (svg) {
        // Mousewheel zoom centered on cursor
        svg.addEventListener("wheel", (e) => {
            e.preventDefault();
            const delta = e.deltaY < 0 ? 1.15 : 0.87;
            zoomExplorerGraph(delta, e.clientX, e.clientY);
        }, { passive: false });

        // Pan on SVG background drag
        svg.addEventListener("mousedown", (e) => {
            if (e.target.closest(".graph-node")) return;
            explorerIsDragging = true;
            explorerDragStart = { x: e.clientX - explorerGraphTransform.x, y: e.clientY - explorerGraphTransform.y };
            svg.style.cursor = "grabbing";
        });

        window.addEventListener("mousemove", (e) => {
            if (explorerDragNode) {
                // Drag single node
                const nodePos = explorerNodePositions[explorerDragNode];
                if (nodePos) {
                    nodePos.x += e.movementX / explorerGraphTransform.scale;
                    nodePos.y += e.movementY / explorerGraphTransform.scale;
                    renderExplorerGraphSVG(explorerGraphData, explorerSelectedNodeId, true);
                }
            } else if (explorerIsDragging) {
                // Pan viewport
                explorerGraphTransform.x = e.clientX - explorerDragStart.x;
                explorerGraphTransform.y = e.clientY - explorerDragStart.y;
                explorerGraphHasUserTransform = true;
                applyGraphTransform();
            }
        });

        window.addEventListener("mouseup", () => {
            explorerIsDragging = false;
            explorerDragNode = null;
            if (svg) svg.style.cursor = "grab";
        });
    }

    // Search enter key
    const searchInput = document.getElementById("explorer-search-input");
    if (searchInput) {
        searchInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                loadExplorerInventory(1);
            }
        });
    }

    // Label filter change
    const labelFilter = document.getElementById("explorer-label-filter");
    if (labelFilter) {
        labelFilter.addEventListener("change", () => {
            if (explorerActiveTab === "table") {
                loadExplorerInventory(1);
            } else {
                loadExplorerGraph();
            }
        });
    }

    // Relationship filter change
    const relFilter = document.getElementById("explorer-rel-filter");
    if (relFilter) {
        relFilter.addEventListener("change", () => {
            if (explorerActiveTab === "graph") {
                loadExplorerGraph();
            }
        });
    }

    // Pagination buttons
    const prevBtn = document.getElementById("explorer-prev-page");
    const nextBtn = document.getElementById("explorer-next-page");
    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (explorerCurrentPage > 1) {
                loadExplorerInventory(explorerCurrentPage - 1);
            }
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            loadExplorerInventory(explorerCurrentPage + 1);
        });
    }

    // Delegate table clicks for "Inspect" button
    const tableBody = document.getElementById("explorer-table-body");
    if (tableBody) {
        tableBody.addEventListener("click", event => {
            const btn = event.target.closest("[data-inspect-label]");
            if (btn) {
                const label = btn.dataset.inspectLabel;
                const id = btn.dataset.inspectId;
                inspectExplorerEntity(label, id);
            }
        });
    }

    // Delegate inspector clicks for connected relationship inspect buttons
    const relsContainer = document.getElementById("inspector-relationships");
    if (relsContainer) {
        relsContainer.addEventListener("click", event => {
            const btn = event.target.closest("[data-inspect-label]");
            if (btn) {
                const label = btn.dataset.inspectLabel;
                const id = btn.dataset.inspectId;
                inspectExplorerEntity(label, id);
            }
        });
    }

    // 30-Second periodic polling while the page is visible
    if (explorerPollingTimer) clearInterval(explorerPollingTimer);
    explorerPollingTimer = setInterval(() => {
        if (document.visibilityState === "visible") {
            const syncStatus = document.getElementById("sync-status");
            if (syncStatus) syncStatus.textContent = "Auto-refreshing...";
            if (explorerActiveTab === "table") {
                loadExplorerInventory(explorerCurrentPage);
            } else {
                loadExplorerGraph(null, null, true);
            }
        }
    }, 30000);
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

    // 7. Database Explorer
    if (document.getElementById("explorer-table-view")) {
        initializeExplorerPage();
    }
});
