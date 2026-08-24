const clientModal = document.getElementById("client-modal");
const closeClientModal = document.getElementById("close-client-modal");
const modalError = document.getElementById("client-modal-error");

function setModalText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}
function formatDateTime(value) {
    if (!value) return "No record";
    const date = new Date(value);
    if (isNaN(date)) return "Unknown";
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
    if (!value) return "";
    const date = new Date(value);
    if (isNaN(date)) return "";
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return `${seconds} second${seconds === 1 ? "" : "s"} ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days === 1 ? "" : "s"} ago`;
}
function formatDuration(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined) return "No duration available";
    totalSeconds = Math.max(0, Number(totalSeconds));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours} hour${hours === 1 ? "" : "s"} ${minutes} minute${minutes === 1 ? "" : "s"} ${seconds} second${seconds === 1 ? "" : "s"}`;
}
function getDurationBetween(startValue, endValue) {
    if (!startValue || !endValue) return null;
    const start = new Date(startValue);
    const end = new Date(endValue);
    if (isNaN(start) || isNaN(end)) return null;
    const seconds = Math.max(0, Math.floor((end - start) / 1000));
    return formatDuration(seconds);
}
function renderConnectionHistory(history) {
    const container = document.getElementById("modal-connection-history");
    const historyCount = document.getElementById("modal-history-count");

    if (!container) return;
    if (historyCount) {
        const count = history ? history.length : 0;
        historyCount.textContent = `${count} connection${count === 1 ? "" : "s"}`;
    }

    if (!history || history.length === 0) {
        container.innerHTML = `
            <div class="py-6 text-center">
                <p class="text-sm text-gray-400">No connection history in the last 24 hours.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = "";
    history.forEach((item, index) => {
        const isActive = item.active;
        const historyRow = document.createElement("div");
        historyRow.className = "grid grid-cols-2 gap-2";
        const upCard = document.createElement("div");
        upCard.className = "rounded-lg border border-blue-100 bg-blue-50 p-3";
        upCard.innerHTML = `
            <p class="text-[11px] font-semibold ${isActive ? "text-green-600" : "text-blue-600"}">
                ${isActive ? "CURRENTLY ACTIVE" : "UPTIME"}
            </p>
            <p class="mt-1 text-sm font-semibold text-gray-900">
                ${formatDateTime(item.up_time)}
            </p>
            <div class="mt-2">
                <p class="text-[10px] font-medium text-gray-500">AC</p>
                <p class="text-sm font-bold text-gray-900">
                    ${item.up_ac || "Unknown AC"}
                </p>
            </div>
            <p class="mt-2 text-xs text-gray-500">
                ${isActive ? "Connected for" : "Connected for"}
                <span class="font-semibold text-gray-700">
                    ${formatDuration(item.duration_seconds)}
                </span>
            </p>
        `;

        const downCard = document.createElement("div");
        if (item.down_time) {
            downCard.className = "rounded-lg border border-red-100 bg-red-50 p-3";

        const nextUpEntry = history.find(
                entry =>
                entry.up_time &&
                new Date(entry.up_time) > new Date(item.down_time)
        );
        const nextUpTime = nextUpEntry ? nextUpEntry.up_time : null;
        const downDuration = getDurationBetween(item.down_time, nextUpTime);
        
        downCard.innerHTML = `
                <p class="text-[11px] font-semibold text-red-600">
                    DOWNTIME
                </p>
                <p class="mt-1 text-sm font-semibold text-gray-900">
                    ${formatDateTime(item.down_time)}
                </p>
                <div class="mt-2">
                    <p class="text-[10px] font-medium text-gray-500">AC</p>
                    <p class="text-sm font-bold text-gray-900">
                        ${item.down_ac || "Unknown AC"}
                    </p>
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
                        : `
                            <p class="mt-2 text-xs text-gray-400">
                                Downtime duration unavailable
                            </p>
                        `
                }
            `;
        } else {
            downCard.className = "rounded-lg border border-gray-200 bg-gray-50 p-3";

            downCard.innerHTML = `
                <p class="text-[11px] font-semibold text-gray-400">
                    NO DOWNTIME YET
                </p>
                <p class="mt-1 text-sm font-semibold text-gray-500">
                    Session is still active
                </p>
                <div class="mt-2">
                    <p class="text-[10px] font-medium text-gray-400">
                        STATUS
                    </p>
                    <p class="text-sm font-bold text-green-600">
                        ONLINE
                    </p>
                </div>
                <p class="mt-2 text-xs text-gray-400">
                    Waiting for logout event
                </p>
            `;
        }

        historyRow.appendChild(upCard);
        historyRow.appendChild(downCard);
        container.appendChild(historyRow);
        if (index < history.length - 1) {
            const separator = document.createElement("div");
            separator.className =
                "flex items-center justify-center py-1 text-gray-300";
            separator.textContent = "↓";
            container.appendChild(separator);
        }
    });
}
function resetClientModal() {
    if (modalError) {
        modalError.classList.add("hidden");
        modalError.textContent = "";
    }
    setModalText("modal-username", "Loading...");
    setModalText("modal-mac", "-");
    setModalText("modal-ip", "-");
    setModalText("modal-status", "Loading...");
    setModalText("modal-active-ac", "-");
    setModalText("modal-duration", "-");
    const historyContainer = document.getElementById("modal-connection-history");
    if (historyContainer) {
        historyContainer.innerHTML = `
            <div class="py-4 text-center text-sm text-gray-400">
                Loading connection history...
            </div>
        `;
    }
    const historyCount = document.getElementById("modal-history-count");
    if (historyCount) {
        historyCount.textContent = "0 events";
    }
}
function openClientModal() {
    if (!clientModal) return;
    clientModal.classList.remove("hidden");
    clientModal.classList.add("flex");
}
function closeModal() {
    if (!clientModal) return;
    clientModal.classList.add("hidden");
    clientModal.classList.remove("flex");
}
function showModalError(message) {
    if (!modalError) return;
    modalError.textContent = message;
    modalError.classList.remove("hidden");
}
async function loadClientInfo(params) {
    resetClientModal();
    openClientModal();
    try {
        const query = new URLSearchParams(params).toString();
        const response = await fetch(`/client-info/?${query}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (!data.found) {
            showModalError(data.message || "Client not found.");
            setModalText("modal-username", "Not found");
            setModalText("modal-status", "Not found");
            renderConnectionHistory(data.connection_history || []);
            return;
        }
        const isActive = !!data.active_ac;
        setModalText("modal-username", data.username || "UNKNOWN");
        setModalText("modal-mac", data.mac || "No MAC");
        setModalText("modal-ip", data.ip || "No IP");
        setModalText("modal-status", isActive ? "ACTIVE" : "OFFLINE");
        setModalText("modal-active-ac", data.active_ac || "Currently offline");
        setModalText("modal-duration", formatDuration(data.duration_seconds));

        renderConnectionHistory(data.connection_history || []);
    } catch (error) {
        console.error("CLIENT INFO ERROR:", error);
        showModalError("Unable to retrieve client information.");
        setModalText("modal-status", "ERROR");
    }
}
async function openClientInfoFromLog(username, mac) {
    const searchValue = mac && mac !== "No MAC" ? mac : username;

    if (!searchValue) {
        console.warn("No username or MAC supplied.");
        return;
    }

    await loadClientInfo({ q: searchValue });
}
async function openClientInfoById(clientId) {
    if (!clientId) {
        console.warn("No client ID supplied.");
        return;
    }
    await loadClientInfo({ id: clientId });
}
document.addEventListener("click", function(event) {
    const logEntry = event.target.closest(".log-entry");
    if (!logEntry) return;
    const username = logEntry.dataset.username || "";
    const mac = logEntry.dataset.mac || "";
    if (!username && !mac) return;
    openClientInfoFromLog(username, mac);
});

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

window.openClientInfoFromLog = openClientInfoFromLog;
window.openClientInfoById = openClientInfoById;
window.openClientModal = openClientModal;
window.closeModal = closeModal;
window.formatDateTime = formatDateTime;
window.formatRelativeTime = formatRelativeTime;
window.formatDuration = formatDuration;
window.renderConnectionHistory = renderConnectionHistory;