
// ============================================================
// CLIENT SEARCH
// ============================================================

const searchForm = document.querySelector('form[method="get"]');
const searchInput = searchForm
    ? searchForm.querySelector('input[name="q"]')
    : null;
const searchModal = document.getElementById("client-search-modal");
const searchResultsList = document.getElementById("search-results-list");
const searchResultsSubtitle = document.getElementById("search-results-subtitle");
const closeSearchModal = document.getElementById("close-search-modal");

function openSearchModal() {
    if (!searchModal) {
        console.error("Search modal not found.");
        return;
    }
    searchModal.classList.remove("hidden");
    searchModal.classList.add("flex");
}

function closeSearchResultsModal() {
    if (!searchModal) {
        return;
    }
    searchModal.classList.add("hidden");
    searchModal.classList.remove("flex");
}

function showSearchLoading(query) {
    if (searchResultsSubtitle) {
        searchResultsSubtitle.textContent = `Searching for "${query}"...`;
    }
    if (searchResultsList) {
        searchResultsList.innerHTML = `
            <div class="py-6 text-center">
                <p class="text-sm text-gray-500">
                    Searching...
                </p>
            </div>
        `;
    }
}

function showNoSearchResults(query) {
    if (searchResultsSubtitle) {
        searchResultsSubtitle.textContent = "No matching clients found.";
    }
    if (searchResultsList) {
        searchResultsList.innerHTML = `
            <div class="py-8 text-center">
                <p class="text-sm text-gray-500">
                    No clients found matching
                    <span class="font-semibold text-gray-700">
                        "${query}"
                    </span>
                </p>
            </div>
        `;
    }
}

function renderSearchResult(client) {
    const result = document.createElement("button");
    result.type = "button";
    result.className =
        "w-full rounded-lg border border-gray-200 bg-white px-4 py-3 text-left " +
        "transition hover:border-blue-300 hover:bg-blue-50 hover:shadow-sm mb-2";
    result.innerHTML = `
        <div class="flex items-center justify-between gap-3">
            <div class="min-w-0">
                <p class="truncate text-sm font-semibold text-gray-900">
                    ${client.username || "UNKNOWN"}
                </p>
                <p class="mt-1 truncate text-[11px] text-gray-500">
                    ${client.mac || "No MAC"}
                </p>
            </div>
            <div class="shrink-0 text-right">
                ${
                    client.active
                        ? `
                            <p class="flex items-center justify-end gap-1.5 text-[11px] font-semibold text-green-600">
                                <span class="h-2 w-2 rounded-full bg-green-500"></span>
                                ACTIVE
                            </p>
                            <p class="mt-1 text-[11px] font-medium text-blue-600">
                                ${client.ac || "Unknown AC"}
                            </p>
                        `
                        : `
                            <p class="text-[11px] font-medium text-blue-600">
                                ${client.ac || "Unknown AC"}
                            </p>
                        `
                }
                <p class="mt-1 text-[10px] text-gray-400">
                    View details →
                </p>
            </div>
        </div>
    `;

    result.addEventListener("click", async function() {
        closeSearchResultsModal();
        if (typeof window.openClientInfoFromLog !== "function") {
            console.error("openClientInfoFromLog() is not available.");
            return;
        }
        await window.openClientInfoFromLog(client.username, client.mac);
    });
    return result;
}
async function performClientSearch(query) {
    showSearchLoading(query);
    openSearchModal();
    try {
        const response = await fetch(`/client-search/?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (!data.found || !data.results || data.results.length === 0) {
            showNoSearchResults(query);
            return;
        }
        if (searchResultsSubtitle) {
            searchResultsSubtitle.textContent = `${data.results.length} matching client${data.results.length === 1 ? "" : "s"}`;
        }
        if (searchResultsList) {
            searchResultsList.innerHTML = "";
            data.results.forEach(client => {
                const result = renderSearchResult(client);
                searchResultsList.appendChild(result);
            });
        }
    } catch (error) {
        console.error("CLIENT SEARCH ERROR:", error);
        if (searchResultsSubtitle) {
            searchResultsSubtitle.textContent = "Unable to search for clients.";
        }
        if (searchResultsList) {
            searchResultsList.innerHTML = `
                <div class="py-8 text-center">
                    <p class="text-sm text-red-600">
                        Unable to retrieve search results.
                    </p>
                </div>
            `;
        }
    }
}
if (searchForm) {
    searchForm.addEventListener("submit", function(event) {
        event.preventDefault();
        if (!searchInput) {
            console.error("Search input not found.");
            return;
        }
        const query = searchInput.value.trim();
        if (!query) {
            return;
        }
        performClientSearch(query);
    });
}
if (closeSearchModal) {
    closeSearchModal.addEventListener("click", closeSearchResultsModal);
}
if (searchModal) {
    searchModal.addEventListener("click", function(event) {
        if (event.target === searchModal) {
            closeSearchResultsModal();
        }
    });
}

window.performClientSearch =
    performClientSearch;