// remove comments in front of all loadAssets() functions and remove the temp data and calling that from
/*  
    // Temporary frontend test data
        cachedAssets = mockAssets;
        displayAssets(mockAssets);
*/

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


let cachedAssets = [];

async function loadAssets() {
    const tbody = document.getElementById("assets-table-body");

    if (tbody) {
        tbody.innerHTML =
            '<tr><td colspan="6">Loading assets...</td></tr>';
    }

    try {
        const result = await apiRequest("/assets");

        // Adjust this only after confirming the API response shape.
        const assets = Array.isArray(result) ? result : result.assets;

        if (!Array.isArray(assets)) {
            throw new Error("Unexpected assets response format");
        }

        cachedAssets = assets;
        displayAssets(assets);
        populateAssetSelectors(assets);

        const searchInput = document.getElementById("asset-search");

        if (searchInput) {
            filterAssets(searchInput.value);
        }
    } catch (error) {
        showMessage(
            "assets-message",
            error.message || "Unable to load assets",
            "error"
        );

        if (tbody) {
            tbody.innerHTML =
                '<tr><td colspan="6">Unable to load assets.</td></tr>';
        }
    }
}

function displayAssets(assets) {
    const tbody = document.getElementById("assets-table-body");

    if (!tbody) return;

    if (assets.length === 0) {
        tbody.innerHTML =
            '<tr><td colspan="6">No assets found.</td></tr>';
        return;
    }

    tbody.innerHTML = assets.map(asset => `
        <tr>
            <td>${escapeHTML(asset.asset_id)}</td>
            <td>${escapeHTML(asset.name)}</td>
            <td>${escapeHTML(asset.location)}</td>
            <td>${escapeHTML(asset.period)}</td>
            <td>
                <span class="status">
                    ${escapeHTML(asset.preservation_status)}
                </span>
            </td>
            <td>
                <button type="button"
                    data-view-asset="${escapeHTML(asset.asset_id)}">
                    View
                </button>
                <button type="button"
                    data-edit-asset="${escapeHTML(asset.asset_id)}">
                    Update Status
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
        String(asset.asset_id ?? "").toLowerCase().includes(query)
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

        showMessage(
            "assets-message",
            "Heritage asset added successfully.",
            "success"
        );

        // await loadAssets();
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

            const query = document.getElementById("asset-search").value;

            // Local search works without a search API.
            filterAssets(query);
        });
    }

    const clearButton = document.getElementById("clear-asset-search");

    if (clearButton) {
        clearButton.addEventListener("click", () => {
            document.getElementById("asset-search").value = "";
            displayAssets(cachedAssets);
        });
    }

    const searchInput = document.getElementById("asset-search");

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            filterAssets(searchInput.value);
        });
    }

    // loadAssets();
}



document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("asset-form")) {
        initializeAssetsPage();
    }

    // Add the other page initializers here as you implement them.
    
    // Temporary frontend test data
        cachedAssets = mockAssets;
        displayAssets(mockAssets);
});


const mockAssets = [
    {
        asset_id: "HA001",
        name: "Example Heritage Monument",
        location: "Chennai",
        period: "Medieval",
        preservation_status: "Good",
        description: "Temporary sample record for UI testing."
    },
    {
        asset_id: "HA002",
        name: "Example Historic Structure",
        location: "Madurai",
        period: "Ancient",
        preservation_status: "Needs Attention",
        description: "Another temporary sample record."
    }
];


const assetsTableBody = document.getElementById("assets-table-body");

if (assetsTableBody) {
    assetsTableBody.addEventListener("click", async event => {
        const viewButton = event.target.closest("[data-view-asset]");
        const updateButton = event.target.closest("[data-edit-asset]");

        if (viewButton) {
            const assetId = viewButton.dataset.viewAsset;
            const asset = cachedAssets.find(
                item => String(item.asset_id) === assetId
            );

            if (!asset) return;

            const details = document.getElementById("asset-details");
            const content = document.getElementById(
                "asset-details-content"
            );

            content.textContent = [
                `Asset ID: ${asset.asset_id}`,
                `Name: ${asset.name}`,
                `Location: ${asset.location}`,
                `Period: ${asset.period ?? "Not specified"}`,
                `Preservation status: ${asset.preservation_status}`,
                `Description: ${asset.description ?? "Not specified"}`
            ].join("\n");

            content.style.whiteSpace = "pre-line";
            details.hidden = false;
        }

        if (updateButton) {
            const assetId = updateButton.dataset.editAsset;
            const asset = cachedAssets.find(
                item => String(item.asset_id) === assetId
            );

            if (!asset) return;

            const newStatus = window.prompt(
                "Enter the new preservation status:",
                asset.preservation_status
            );

            if (newStatus === null || !newStatus.trim()) return;

            try {
                await apiRequest(
                    `/assets/${encodeURIComponent(assetId)}`,
                    {
                        method: "PUT",
                        body: JSON.stringify({
                            preservation_status: newStatus.trim()
                        })
                    }
                );

                showMessage(
                    "assets-message",
                    "Asset updated successfully.",
                    "success"
                );

                // await loadAssets();
            } catch (error) {
                showMessage("assets-message", error.message, "error");
            }
        }
    });
}



