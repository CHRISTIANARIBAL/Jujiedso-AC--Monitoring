
document.addEventListener("DOMContentLoaded", () => {
    const toggleButton = document.getElementById("toggle-location-cards");
    const INITIAL_LOCATION_LIMIT = 8;
    let showAllLocations = false;
    let locations = [];

    const cards = document.getElementById("location-cards");
    const message = document.getElementById("location-status-message");
    const search = document.getElementById("location-search");

    const modal = document.getElementById("location-clients-modal");
    const modalTitle = document.getElementById("location-clients-title");
    const modalSubtitle = document.getElementById("location-clients-subtitle");
    const clientList = document.getElementById("location-clients-list");
    const closeModal = document.getElementById("close-location-clients");

    if (!cards || !message || !search || !modal) return;

    
    const downButton = document.getElementById("location-down-button");

    const statusModal = document.getElementById("location-status-modal");
    const statusModalTitle = document.getElementById("location-status-modal-title");
    const statusModalSubtitle = document.getElementById("location-status-modal-subtitle");
    const statusModalList = document.getElementById("location-status-modal-list");
    const statusModalSearch = document.getElementById("location-status-modal-search");
    const closeStatusModal = document.getElementById("close-location-status-modal");

    let downClients = [];

    function openDownClientsModal() {
        if (!statusModal) return;

        // Collect Down clients from all detected locations.
        downClients = locations.flatMap((location) =>
            (location.clients || [])
                .filter((client) => client.status === "Down")
                .map((client) => ({
                    ...client,
                    location: location.name,
                }))
        );

        if (statusModalTitle) {
            statusModalTitle.textContent = "Down Clients";
        }

        if (statusModalSubtitle) {
            statusModalSubtitle.textContent =
                `${downClients.length} offline clients across all locations`;
        }

        if (statusModalSearch) {
            statusModalSearch.value = "";
        }

        renderDownClients();

        if (window.ModalNavigation) {
            window.ModalNavigation.open("location-status-modal");
        } else {
            statusModal.classList.remove("hidden");
            statusModal.classList.add("flex");
        }
    }

    function renderDownClients() {
        if (!statusModalList) return;

        const query = (statusModalSearch?.value || "").trim().toLowerCase();

        const filteredClients = downClients.filter((client) =>
            [
                client.username,
                client.mac,
                client.location,
                client.ac,
                client.nap,
            ].some((value) =>
                String(value || "").toLowerCase().includes(query)
            )
        );

        statusModalList.replaceChildren();

        if (filteredClients.length === 0) {
            const empty = document.createElement("p");
            empty.className = "py-8 text-center text-sm text-gray-500";
            empty.textContent = downClients.length
                ? "No matching Down clients found."
                : "There are currently no Down clients.";

            statusModalList.appendChild(empty);
            return;
        }

        filteredClients.forEach((client) => {
            const row = document.createElement("button");
            row.type = "button";
            row.className =
                "flex w-full flex-col gap-2 border-b border-gray-100 px-2 py-3 text-left transition hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between";

            const details = document.createElement("div");
            details.className = "min-w-0";

            const username = document.createElement("p");
            username.className =
                "break-all text-sm font-semibold text-gray-900";
            username.textContent = client.username || "Unknown username";

            const metadata = document.createElement("p");
            metadata.className = "mt-1 break-all text-xs text-gray-500";
            metadata.textContent =
                `${client.location} · MAC: ${client.mac || "N/A"} · AC: ${client.ac || "Unknown AC"} · NAP: ${client.nap || "N/A"}`;

            details.append(username, metadata);

            const action = document.createElement("span");
            action.className =
                "shrink-0 text-xs font-medium text-blue-600";
            action.textContent = "View client details →";

            row.append(details, action);

            row.addEventListener("click", () => {
                const clientId = Number(client.id);

                if (!Number.isInteger(clientId) || clientId <= 0) {
                    console.error("Invalid client ID:", client.id);
                    return;
                }

                if (typeof window.openClientInfoById === "function") {
                    // Let ModalNavigation preserve Down Clients in the history.
                    window.openClientInfoById(clientId);
                } else {
                    console.error("openClientInfoById is not available.");
                    alert("The client details modal could not be opened.");
                }
            });

            statusModalList.appendChild(row);
        });
    }

    function closeDownClientsModal() {
        if (window.ModalNavigation) {
            window.ModalNavigation.back();
            return;
        }

        if (!statusModal) return;

        statusModal.classList.add("hidden");
        statusModal.classList.remove("flex");
    }

    // Only the Down total opens this modal.
    if (downButton) {
        downButton.addEventListener("click", openDownClientsModal);
    }

    if (statusModalSearch) {
        statusModalSearch.addEventListener("input", renderDownClients);
    }

    if (closeStatusModal) {
        closeStatusModal.addEventListener("click", closeDownClientsModal);
    }

    if (statusModal) {
        statusModal.addEventListener("click", (event) => {
            if (event.target === statusModal) {
                closeDownClientsModal();
            }
        });
    }


    const escapeHTML = (value) =>
        String(value ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        })[char]);

    
    function updateLocationTotals() {
        const totalElement = document.getElementById("location-total");
        const onlineElement = document.getElementById("location-online-total");
        const downElement = document.getElementById("location-down-total");

        if (totalElement) {
            totalElement.textContent = locations.length;
        }

        if (onlineElement) {
            onlineElement.textContent = locations.reduce(
                (sum, item) => sum + Number(item.online || 0),
                0
            );
        }

        if (downElement) {
            downElement.textContent = locations.reduce(
                (sum, item) => sum + Number(item.down || 0),
                0
            );
        }
    }

    window.updateLocationSummary = function (updatedLocations) {
        locations = Array.isArray(updatedLocations) ? updatedLocations : [];
        updateLocationTotals();
        renderLocations();
    };


    function renderLocations() {
        const query = search.value.trim().toLowerCase();

        const filtered = locations.filter((location) =>
            location.name.toLowerCase().includes(query)
        );

        // window.updateLocationSummary = function (updatedLocations) {
        //     locations = updatedLocations || [];
        //     renderLocations();
        // };

        cards.replaceChildren();

        if (!filtered.length) {
            message.textContent = locations.length
                ? "No locations match your search."
                : "No locations were detected.";
            message.classList.remove("hidden");

            if (toggleButton) toggleButton.classList.add("hidden");
            return;
        }

        message.classList.add("hidden");

        // Show all matching results while searching.
        // Otherwise, limit the initial display to 8.
        const shouldShowAll = showAllLocations || query.length > 0;
        const visibleLocations = shouldShowAll
            ? filtered
            : filtered.slice(0, INITIAL_LOCATION_LIMIT);

        visibleLocations.forEach((location) => {
            const card = document.createElement("div");

            card.className =
                "rounded-xl border border-gray-200 bg-white p-4 transition hover:border-blue-300 hover:shadow-sm";

            card.innerHTML = `
                <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0">
                        <h3 class="truncate font-semibold capitalize text-gray-900">
                            ${escapeHTML(location.name)}
                        </h3>
                        <p class="mt-1 text-xs text-gray-500">
                            ${location.total} unique PPPoE usernames
                        </p>
                    </div>
                    <span class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                        ${location.total}
                    </span>
                </div>

                <div class="mt-4 grid grid-cols-2 gap-2">
                    <button
                        type="button"
                        data-location="${escapeHTML(location.name)}"
                        data-status="Online"
                        class="rounded-lg bg-green-50 p-3 text-left hover:bg-green-100"
                    >
                        <span class="block text-xs text-green-700">Online</span>
                        <span class="mt-1 block text-xl font-bold text-green-800">
                            ${location.online}
                        </span>
                    </button>

                    <button
                        type="button"
                        data-location="${escapeHTML(location.name)}"
                        data-status="Down"
                        class="rounded-lg bg-red-50 p-3 text-left hover:bg-red-100"
                    >
                        <span class="block text-xs text-red-700">Down</span>
                        <span class="mt-1 block text-xl font-bold text-red-800">
                            ${location.down}
                        </span>
                    </button>
                </div>
            `;

            cards.appendChild(card);
        });

        if (toggleButton) {
            const needsToggle = filtered.length > INITIAL_LOCATION_LIMIT;

            toggleButton.classList.toggle("hidden", !needsToggle);

            if (needsToggle) {
                toggleButton.textContent = showAllLocations
                    ? "Show Less Locations"
                    : `Show More Locations (${filtered.length - INITIAL_LOCATION_LIMIT} more)`;

                toggleButton.setAttribute(
                    "aria-expanded",
                    String(showAllLocations)
                );
            }
        }
        
    }

    const totalElement = document.getElementById("location-total");
    const onlineElement = document.getElementById("location-online-total");
    const downElement = document.getElementById("location-down-total");

    if (totalElement) {
        totalElement.textContent = locations.length;
    }
    if (onlineElement) {
        onlineElement.textContent = locations.reduce(
            (sum, item) => sum + Number(item.online || 0), 0
        );
    }
    if (downElement) {
        downElement.textContent = locations.reduce(
            (sum, item) => sum + Number(item.down || 0), 0
        );
    }

    if (toggleButton) {
            toggleButton.addEventListener("click", () => {
                showAllLocations = !showAllLocations;
                renderLocations();

                if (!showAllLocations) {
                    document.getElementById("location-search").scrollIntoView({
                        behavior: "smooth",
                        block: "nearest"
                    });
                }
            });
        }


    function openLocationClients(locationName, status) {
        const location = locations.find(
            (item) => item.name === locationName
        );

        if (!location) return;

        const clients = location.clients.filter(
            (client) => client.status === status
        );

        modalTitle.textContent =
            `${location.name} — ${status} Clients`;
        modalSubtitle.textContent =
            `${clients.length} matching PPPoE usernames`;

        clientList.replaceChildren();

        if (!clients.length) {
            clientList.innerHTML = `
                <p class="py-8 text-center text-sm text-gray-500">
                    No ${escapeHTML(status.toLowerCase())} clients found.
                </p>
            `;
        } else {
            clients.forEach((client) => {
                const row = document.createElement("div");
                row.className =
                    "flex flex-col gap-3 border-b border-gray-100 py-3 sm:flex-row sm:items-center sm:justify-between";

                row.innerHTML = `
                    <div class="min-w-0">
                        <p class="break-all text-sm font-medium text-gray-900">
                            ${escapeHTML(client.username)}
                        </p>
                        <p class="mt-1 text-xs text-gray-500">
                            MAC: ${escapeHTML(client.mac || "N/A")}
                        </p>
                        <p class="mt-1 text-xs text-gray-500">
                            AC: ${escapeHTML(client.ac || "Unknown AC")}
                            · NAP: ${escapeHTML(client.nap || "N/A")}
                        </p>
                    </div>

                    <button
                        type="button"
                        data-client-id="${Number(client.id)}"
                        class="shrink-0 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700"
                    >
                        View Details
                    </button>
                `;

                clientList.appendChild(row);
            });
        }

        if (window.ModalNavigation) {
            window.ModalNavigation.open("location-clients-modal");
        } else {
            modal.classList.remove("hidden");
            modal.classList.add("flex");
        }
    }

    
    function renderBarangayOutages() {
        const section = document.getElementById("barangay-outage-section");
        const list = document.getElementById("barangay-outage-list");
        const count = document.getElementById("barangay-outage-count");

        if (!section || !list || !count) return;

            const affected = locations
            .filter((location) => {
                const total = Number(location.total) || 0;
                const down = Number(location.down) || 0;

                return total > 0 && down >= 2 && down / total >= 0.25;
            })
            .sort((a, b) => {
                const downDifference =
                    Number(b.down || 0) - Number(a.down || 0);

                if (downDifference !== 0) return downDifference;

                return (
                    Number(b.down || 0) / Math.max(Number(b.total || 0), 1) -
                    Number(a.down || 0) / Math.max(Number(a.total || 0), 1)
                );
            });

        list.replaceChildren();

        if (affected.length === 0) {
            count.textContent = "0 affected";
            list.innerHTML = `
                <p class="col-span-full py-3 text-sm text-gray-500">
                    All barangays are below the outage alert threshold.
                </p>
            `;
            return;
        }

        count.textContent =
            `${affected.length} affected`;

        affected.forEach((location) => {
            const total = Number(location.total) || 0;
            const down = Number(location.down) || 0;
            const online = Number(location.online) || 0;
            const percentage = Math.round((down / total) * 100);

            const card = document.createElement("button");
            card.type = "button";
            card.dataset.location = location.name;
            card.dataset.status = "Down";
            card.className =
                "w-full rounded-lg border border-red-200 bg-red-50 " +
                "p-4 text-left transition hover:border-red-400 hover:bg-red-100";

            const heading = document.createElement("div");
            heading.className =
                "flex items-center justify-between gap-2";

            const name = document.createElement("span");
            name.className =
                "font-semibold text-gray-900 break-words";
            name.textContent = location.name;

            const badge = document.createElement("span");
            badge.className =
                "shrink-0 rounded-full bg-red-100 px-2 py-1 " +
                "text-xs font-semibold text-red-700";
            badge.textContent = `${percentage}% down`;

            heading.append(name, badge);

            const summary = document.createElement("p");
            summary.className = "mt-3 text-sm text-gray-600";
            summary.textContent = `${down} down of ${total} clients`;

            const bar = document.createElement("div");
            bar.className =
                "mt-3 h-2 overflow-hidden rounded-full bg-gray-200";

            const fill = document.createElement("div");
            fill.className = "h-full rounded-full bg-red-500";
            fill.style.width = `${percentage}%`;
            bar.appendChild(fill);

            const onlineText = document.createElement("p");
            onlineText.className = "mt-2 text-xs text-green-700";
            onlineText.textContent = `${online} clients online`;

            const hint = document.createElement("p");
            hint.className = "mt-3 text-xs font-medium text-red-700";
            hint.textContent = "Click to view down clients →";

            card.append(heading, summary, bar, onlineText, hint);
            list.appendChild(card);
        });

        // section.classList.remove("hidden");
    }

    async function loadLocations() {
        try {
            const response = await fetch("/api/location-summary/", {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin",
            });

            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }

            const data = await response.json();
            locations = Array.isArray(data.locations) ? data.locations : [];

            updateLocationTotals();
            renderLocations();
            renderBarangayOutages();

            document.getElementById("location-total").textContent =
                data.total_locations ?? locations.length;

            document.getElementById("location-online-total").textContent =
                data.total_online ?? 0;

            document.getElementById("location-down-total").textContent =
                data.total_down ?? 0;

            renderLocations();
        } catch (error) {
            console.error("Unable to load location summary:", error);
            cards.replaceChildren();
            message.textContent =
                "Unable to load location statistics. Check your login and API endpoint.";
            message.classList.remove("hidden");
        }
    }

    search.addEventListener("input", renderLocations);

    cards.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-location][data-status]");
        if (!button) return;

        openLocationClients(
            button.dataset.location,
            button.dataset.status
        );
    });

    clientList.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-client-id]");
        if (!button) return;

        const clientId = Number(button.dataset.clientId);
        if (!Number.isInteger(clientId) || clientId <= 0) return;

        if (typeof window.openClientInfoById === "function") {
            window.openClientInfoById(clientId);
        } else {
            console.error("openClientInfoById is not available.");
            alert("The client details modal could not be opened.");
        }
    });

    function hideModal() {
        if (window.ModalNavigation) {
            window.ModalNavigation.closeAll();
            return;
        }

        if (!modal) return;

        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }

    closeModal.addEventListener("click", hideModal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) hideModal();
    });

    loadLocations();

// Refresh barangay status and outage watchlist every 10 seconds.
    setInterval(loadLocations, 10000);

    
    const outageList = document.getElementById("barangay-outage-list");

    if (outageList) {
        outageList.addEventListener("click", (event) => {
            const button = event.target.closest(
                "button[data-location][data-status]"
            );

            if (!button) return;

            openLocationClients(
                button.dataset.location,
                button.dataset.status
            );
        });
    }

});
