
const socket = new WebSocket("ws://" + window.location.host + "/ws/monitor/");
socket.onopen = () => {
    console.log("WEBSOCKET CONNECTED");
};
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("SERVER:", data);
    if (data.type === "active_counts") {
        const counts = data.counts || {};
        let total = 0;
        Object.entries(counts).forEach(([acId, count]) => {
            const number = Number(count) || 0;
            total += number;
            const acCount = document.getElementById(`ac-count-${acId}`);
            const panelCount = document.getElementById(`panel-count-${acId}`);
            if (acCount) acCount.textContent = number;
            if (panelCount) panelCount.textContent = `${number} users`;
        });
        const totalElement = document.getElementById("total-active-users");
        if (totalElement) totalElement.textContent = total;
        return;
    }
    if (!data.event) return;
    const username = data.username || "UNKNOWN";
    const mac = data.mac || "No MAC";
    const ac = data.ac;
    const eventType = data.event;
    const timestamp = data.timestamp;
    if (!ac) return;
    let logContainer = null;
    {% for item in ac_data %}
    if (ac === "{{ item.ac.name }}") {
        logContainer = document.getElementById("logs-{{ item.ac.id }}");
    }
    {% endfor %}
    if (!logContainer) {
        console.warn("AC panel not found:", ac);
        return;
    }
    let badgeClass = "bg-gray-100 text-gray-600";
    let badgeText = eventType;
    if (eventType === "LOGIN") {
        badgeClass = "bg-green-50 text-green-700";
        badgeText = "LOGIN";
    } else if (eventType === "LOGOUT") {
        badgeClass = "bg-red-50 text-red-700";
        badgeText = "LOGOUT";
    } else if (eventType === "AUTH_FAILURE") {
        badgeClass = "bg-orange-50 text-orange-700";
        badgeText = "AUTH FAIL";
    } else if (eventType === "CONNECTION") {
        badgeClass = "bg-blue-50 text-blue-700";
        badgeText = "CONNECTION";
    }
    let formattedTime = "";
    if (timestamp) {
        const date = new Date(timestamp);
        if (!isNaN(date)) {
            formattedTime = date.toLocaleString("en-US", {
                month: "short",
                day: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            });
        }
    }
    const logElement = document.createElement("div");

    logElement.className =
        "log-entry cursor-pointer border-b border-gray-100 px-4 py-2.5 hover:bg-gray-50";

    logElement.dataset.username = username;
    logElement.dataset.mac = mac;
    logElement.innerHTML = `
        <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
                <p class="truncate text-sm font-medium text-gray-900">${username}</p>
                <p class="mt-0.5 truncate text-[11px] text-gray-500">${mac}</p>
            </div>
            <div class="shrink-0 text-right">
                <span class="rounded-full ${badgeClass} px-2 py-0.5 text-[10px] font-medium">${badgeText}</span>
                <p class="mt-1 whitespace-nowrap text-[10px] text-gray-400">${formattedTime}</p>
            </div>
        </div>
    `;
    logContainer.prepend(logElement);
    while (logContainer.children.length > 50) {
        logContainer.removeChild(logContainer.lastElementChild);
    }
    logElement.classList.add("bg-blue-50");
    setTimeout(() => {
        logElement.classList.remove("bg-blue-50");
    }, 1500);
};
socket.onclose = (event) => {
    console.log("WEBSOCKET CLOSED", event.code, event.reason);
};
socket.onerror = (error) => {
    console.error("WEBSOCKET ERROR:", error);
};
const searchForm = document.querySelector('form[method="get"]');
const searchInput = searchForm ? searchForm.querySelector('input[name="q"]') : null;
const clientModal = document.getElementById("client-modal");
const closeClientModal = document.getElementById("close-client-modal");
const modalError = document.getElementById("client-modal-error");
function formatDateTime(value) {
    if (!value) {
        return "No record";
    }
    const date = new Date(value);
    if (isNaN(date)) {
        return "Unknown";
    }
    return date.toLocaleString("en-US", {
        month: "short",
        day: "2-digit",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit"
    });
}
function formatRelativeTime(value) {
    if (!value) {
        return "";
    }
    const date = new Date(value);
    if (isNaN(date)) {
        return "";
    }
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) {
        return `${seconds} second${seconds === 1 ? "" : "s"} ago`;
    }
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    }
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    }
    const days = Math.floor(hours / 24);
    return `${days} day${days === 1 ? "" : "s"} ago`;
}
function formatDuration(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined) {
        return "No duration available";
    }
    totalSeconds = Math.max(0, Number(totalSeconds));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours} hour${hours === 1 ? "" : "s"} ${minutes} minute${minutes === 1 ? "" : "s"} ${seconds} second${seconds === 1 ? "" : "s"}`;
}

function renderConnectionHistory(history) {

    const container =
        document.getElementById("modal-connection-history");

    if (!container) {
        console.error("Connection history container not found.");
        return;
    }

    if (!history || history.length === 0) {

        container.innerHTML = `
            <div class="py-6 text-center">
                <p class="text-sm text-gray-400">
                    No connection history in the last 24 hours.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML = "";

    history.forEach((item, index) => {

        const isActive = item.active;

        const eventLabel =
            isActive
                ? "CURRENTLY ACTIVE"
                : "UPTIME";

        const upTime =
            formatDateTime(item.up_time);

        const upDuration =
            formatDuration(item.duration_seconds);

        const upAc =
            item.up_ac || "Unknown AC";

        const upRow = document.createElement("div");

        upRow.className =
            "rounded-lg border border-gray-200 bg-white p-3";

        upRow.innerHTML = `
            <div class="flex items-center justify-between gap-3">

                <div>
                    <p class="text-[11px] font-semibold ${
                        isActive
                            ? "text-green-600"
                            : "text-blue-600"
                    }">
                        ${eventLabel}
                    </p>

                    <p class="mt-1 text-sm font-semibold text-gray-900">
                        ${upTime}
                    </p>
                </div>

                <div class="text-right">

                    <p class="text-[11px] font-medium text-gray-500">
                        AC
                    </p>

                    <p class="text-sm font-bold text-gray-900">
                        ${upAc}
                    </p>

                </div>

            </div>

            <p class="mt-2 text-xs text-gray-500">
                ${isActive ? "Currently connected for" : "Connected for"}
                <span class="font-semibold text-gray-700">
                    ${upDuration}
                </span>
            </p>
        `;

        container.appendChild(upRow);

        // -------------------------------------------------
        // DOWNTIME AFTER THIS UPTIME
        // -------------------------------------------------

        if (item.down_time) {

            const downRow = document.createElement("div");

            downRow.className =
                "rounded-lg border border-red-100 bg-red-50 p-3";

            const downDuration =
                getDurationBetween(
                    item.down_time,
                    history[index + 1]
                        ? history[index + 1].up_time
                        : null
                );

            downRow.innerHTML = `
                <div class="flex items-center justify-between gap-3">

                    <div>
                        <p class="text-[11px] font-semibold text-red-600">
                            DOWNTIME
                        </p>

                        <p class="mt-1 text-sm font-semibold text-gray-900">
                            ${formatDateTime(item.down_time)}
                        </p>
                    </div>

                    <div class="text-right">

                        <p class="text-[11px] font-medium text-gray-500">
                            AC
                        </p>

                        <p class="text-sm font-bold text-gray-900">
                            ${item.down_ac || "Unknown AC"}
                        </p>

                    </div>

                </div>

                ${
                    downDuration
                        ? `
                            <p class="mt-2 text-xs text-gray-500">
                                Down for
                                <span class="font-semibold text-gray-700">
                                    ${downDuration}
                                </span>
                            </p>
                          `
                        : ""
                }
            `;

            container.appendChild(downRow);
        }

        // Separator
        if (index < history.length - 1) {

            const separator =
                document.createElement("div");

            separator.className =
                "flex items-center justify-center py-1 text-gray-300";

            separator.innerHTML = "↓";

            container.appendChild(separator);
        }
    });
}

function getDurationBetween(startValue, endValue) {

    if (!startValue || !endValue) {
        return null;
    }

    const start = new Date(startValue);
    const end = new Date(endValue);

    if (isNaN(start) || isNaN(end)) {
        return null;
    }

    const seconds =
        Math.max(
            0,
            Math.floor(
                (end.getTime() - start.getTime()) / 1000
            )
        );

    return formatDuration(seconds);
}

async function openClientInfoFromLog(username, mac) {

    modalError.classList.add("hidden");
    modalError.textContent = "";

    document.getElementById("modal-username").textContent = "Loading...";
    document.getElementById("modal-mac").textContent = "-";
    document.getElementById("modal-connection-history").innerHTML = `
    <div class="py-4 text-center text-sm text-gray-400">
        Loading connection history...
    </div>
`;
    //document.getElementById("modal-up-time").textContent = "-";
   //document.getElementById("modal-down-time").textContent = "-";
    document.getElementById("modal-duration").textContent = "-";
    document.getElementById("modal-active-ac").textContent = "-";

    openClientModal();

    try {

        const searchValue =
            mac && mac !== "No MAC"
                ? mac
                : username;

        const response = await fetch(
            `/client-info/?q=${encodeURIComponent(searchValue)}`
        );

        const data = await response.json();

        if (!data.found) {

            modalError.textContent =
                data.message || "Client not found.";

            modalError.classList.remove("hidden");

            document.getElementById("modal-username").textContent =
                "Not found";

            renderConnectionHistory(
                data.connection_history || []
            );

            return;
        }

        document.getElementById("modal-username").textContent =
            data.username || username || "UNKNOWN";

        document.getElementById("modal-mac").textContent =
            data.mac || mac || "No MAC";

        if (data.up_time) {

            document.getElementById("modal-up-time").textContent =
                `${formatDateTime(data.up_time)} / ${formatRelativeTime(data.up_time)}`;

        } else {

            document.getElementById("modal-up-time").textContent =
                "No record";

        }

        if (data.last_down_time) {

            let downText =
                `${formatDateTime(data.last_down_time)} / ${formatRelativeTime(data.last_down_time)}`;

            if (data.last_down_ac) {
                downText += ` in ${data.last_down_ac}`;
            }

            document.getElementById("modal-down-time").textContent =
                downText;

        } else {

            document.getElementById("modal-down-time").textContent =
                "No logout record";

        }

        document.getElementById("modal-duration").textContent =
            formatDuration(data.duration_seconds);

        document.getElementById("modal-active-ac").textContent =
            data.active_ac || "Currently offline";

    } catch (error) {

        console.error("LOG CLIENT INFO ERROR:", error);

        modalError.textContent =
            "Unable to retrieve client information.";

        modalError.classList.remove("hidden");
    }
}
document.addEventListener("click", function(event) {

    const logEntry = event.target.closest(".log-entry");

    if (!logEntry) {
        return;
    }

    const username = logEntry.dataset.username || "";
    const mac = logEntry.dataset.mac || "";

    if (!username && !mac) {
        return;
    }

    openClientInfoFromLog(username, mac);
});
function openClientModal() {
    clientModal.classList.remove("hidden");
    clientModal.classList.add("flex");
}
function closeModal() {
    clientModal.classList.add("hidden");
    clientModal.classList.remove("flex");
}
if (searchForm) {
    searchForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const query = searchInput.value.trim();

        if (!query) {
            return;
        }

        const searchModal = document.getElementById("client-search-modal");
        const searchResultsList = document.getElementById("search-results-list");
        const searchResultsSubtitle = document.getElementById("search-results-subtitle");
        const closeSearchModal = document.getElementById("close-search-modal");

        if (!searchModal || !searchResultsList) {
            console.error("Search results modal not found.");
            return;
        }

        searchResultsList.innerHTML = `
            <div class="py-6 text-center">
                <p class="text-sm text-gray-500">Searching...</p>
            </div>
        `;

        searchResultsSubtitle.textContent = `Searching for "${query}"...`;

        searchModal.classList.remove("hidden");
        searchModal.classList.add("flex");

        try {
            const response = await fetch(
                `/client-search/?q=${encodeURIComponent(query)}`
            );

            const data = await response.json();

            if (!data.found || !data.results || data.results.length === 0) {

                searchResultsSubtitle.textContent = "No matching clients found.";

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

                return;
            }

            searchResultsSubtitle.textContent =
                `${data.results.length} matching client${data.results.length === 1 ? "" : "s"}`;

            searchResultsList.innerHTML = "";

            data.results.forEach(client => {

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

                    searchModal.classList.add("hidden");
                    searchModal.classList.remove("flex");

                    modalError.classList.add("hidden");
                    modalError.textContent = "";

                    document.getElementById("modal-username").textContent =
                        "Loading...";

                    document.getElementById("modal-mac").textContent = "-";
                    document.getElementById("modal-up-time").textContent = "-";
                    document.getElementById("modal-down-time").textContent = "-";
                    document.getElementById("modal-duration").textContent = "-";
                    document.getElementById("modal-active-ac").textContent = "-";

                    openClientModal();

                    try {

                        const response = await fetch(
                            `/client-info/?id=${client.id}`
                        );

                        const data = await response.json();

                        if (!data.found) {

                            modalError.textContent =
                                data.message || "Client not found.";

                            modalError.classList.remove("hidden");

                            document.getElementById("modal-username").textContent =
                                "Not found";

                            renderConnectionHistory(
                                data.connection_history || []
                            );

                            return;
                        }

                        document.getElementById("modal-username").textContent =
                            data.username || "UNKNOWN";

                        document.getElementById("modal-mac").textContent =
                            data.mac || "No MAC";

                        if (data.up_time) {

                            document.getElementById("modal-up-time").textContent =
                                `${formatDateTime(data.up_time)} / ${formatRelativeTime(data.up_time)}`;

                        } else {

                            document.getElementById("modal-up-time").textContent =
                                "No record";

                        }

                        if (data.last_down_time) {

                            let downText =
                                `${formatDateTime(data.last_down_time)} / ${formatRelativeTime(data.last_down_time)}`;

                            if (data.last_down_ac) {
                                downText += ` in ${data.last_down_ac}`;
                            }

                            document.getElementById("modal-down-time").textContent =
                                downText;

                        } else {

                            document.getElementById("modal-down-time").textContent =
                                "No logout record";

                        }

                        document.getElementById("modal-duration").textContent =
                            formatDuration(data.duration_seconds);

                        document.getElementById("modal-active-ac").textContent =
                            data.active_ac || "Currently offline";

                    } catch (error) {

                        console.error("CLIENT SEARCH ERROR:", error);

                        modalError.textContent =
                            "Unable to retrieve client information.";

                        modalError.classList.remove("hidden");
                    }
                });

                searchResultsList.appendChild(result);
            });

        } catch (error) {

            console.error("CLIENT SEARCH ERROR:", error);

            searchResultsSubtitle.textContent =
                "Unable to search for clients.";

            searchResultsList.innerHTML = `
                <div class="py-8 text-center">
                    <p class="text-sm text-red-600">
                        Unable to retrieve search results.
                    </p>
                </div>
            `;
        }
    });
}

const searchModal = document.getElementById("client-search-modal");
const closeSearchModal = document.getElementById("close-search-modal");

if (closeSearchModal && searchModal) {
    closeSearchModal.addEventListener("click", function() {
        searchModal.classList.add("hidden");
        searchModal.classList.remove("flex");
    });
}

if (searchModal) {
    searchModal.addEventListener("click", function(event) {
        if (event.target === searchModal) {
            searchModal.classList.add("hidden");
            searchModal.classList.remove("flex");
        }
    });
}
if (closeClientModal) {
    closeClientModal.addEventListener("click", closeModal);
}
if (clientModal) {
    clientModal.addEventListener("click", function(event) {
        if (event.target === clientModal) {
            closeModal();
        }
    });
}
document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeModal();
    }
});
