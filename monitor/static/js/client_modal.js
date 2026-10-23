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


function formatHistoryDate(value) {
    if (!value) return "Unknown date";

    const date = new Date(value);
    if (isNaN(date.getTime())) return "Unknown date";

    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);

    const isSameDay = (a, b) =>
        a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate();

    if (isSameDay(date, today)) return "Today";
    if (isSameDay(date, yesterday)) return "Yesterday";

    return date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric"
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
    if (totalSeconds === null || totalSeconds === undefined) {
        return "No duration available";
    }

    totalSeconds = Number(totalSeconds);

    if (!Number.isFinite(totalSeconds)) {
        return "No duration available";
    }

    totalSeconds = Math.max(0, Math.floor(totalSeconds));

    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    const parts = [];

    if (days > 0) {
        parts.push(`${days} day${days === 1 ? "" : "s"}`);
    }

    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    if (seconds > 0 || parts.length === 0) {
        parts.push(`${seconds}s`);
    }

    return parts.join(" ");
}

function getDurationBetween(startValue, endValue) {
    if (!startValue || !endValue) return null;
    const start = new Date(startValue);
    const end = new Date(endValue);
    if (isNaN(start) || isNaN(end)) return null;
    const seconds = Math.max(0, Math.floor((end - start) / 1000));
    return formatDuration(seconds);
}

let allConnectionHistory = [];
function renderConnectionHistory(history, saveHistory = true) {
    if (saveHistory) {
        allConnectionHistory = history || [];
        populateHistoryDateFilter();
    }
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
                <p class="text-sm text-gray-400">No connection history in the last 7 days.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = "";
    let previousDateKey = null;

    history.forEach((item, index) => {
        const dateValue = item.up_time || item.down_time;
        const date = dateValue ? new Date(dateValue) : null;

        const dateKey =
            date && !isNaN(date.getTime())
                ? `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
                : "unknown";

        // Add a date header when the calendar date changes.
        if (dateKey !== previousDateKey) {
            const dateBlock = document.createElement("div");
            dateBlock.className = "flex items-center gap-3 py-3";

            let dateLabel = "Unknown date";

            if (date && !isNaN(date.getTime())) {
                const today = new Date();
                const yesterday = new Date();
                yesterday.setDate(today.getDate() - 1);

                const isSameDay = (a, b) =>
                    a.getFullYear() === b.getFullYear() &&
                    a.getMonth() === b.getMonth() &&
                    a.getDate() === b.getDate();

                if (isSameDay(date, today)) {
                    dateLabel = "Today";
                } else if (isSameDay(date, yesterday)) {
                    dateLabel = "Yesterday";
                } else {
                    dateLabel = date.toLocaleDateString("en-US", {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                        year: "numeric"
                    });
                }
            }

            dateBlock.innerHTML = `
                <div class="h-px flex-1 bg-gray-200"></div>
                <div class="rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-xs font-bold text-gray-600">
                    ${dateLabel}
                </div>
                <div class="h-px flex-1 bg-gray-200"></div>
            `;

            container.appendChild(dateBlock);
            previousDateKey = dateKey;
        }

        const isActive = item.active;

        const historyRow = document.createElement("div");
        historyRow.className = "grid grid-cols-1 sm:grid-cols-2 gap-2";

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
                Connected for
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
    updateTrafficButton(false);
    setModalText("modal-username", "Loading...");
    setModalText("modal-mac", "-");
    setModalText("modal-ip", "-");
    setModalText("modal-status", "Loading...");
    setModalText("modal-plan", "Loading...");
    setModalText("modal-active-ac", "-");
    setModalText("modal-olt", "-");
    setModalText("modal-olt-interface", "-");
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
    if (window.ModalNavigation) {
        window.ModalNavigation.open("client-modal");
        return;
    }

    if (!clientModal) return;
    clientModal.classList.remove("hidden");
    clientModal.classList.add("flex");
}

function closeModal() {
    if (window.ModalNavigation) {
        window.ModalNavigation.back();
        return;
    }

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
        const connectionType = data.connection_type;
        const connectionName = data.connection_name;
        const connectionInterface = data.connection_interface;
        const isActive = !!data.active_ac;
        updateTrafficButton(isActive);
        setModalText("modal-username", data.username || "UNKNOWN");
        setModalText("modal-mac", data.mac || "No MAC");
        setModalText("modal-ip", data.ip || "No IP");
        setModalText("modal-status", isActive ? "ACTIVE" : "OFFLINE");
        const planLabel = data.bandwidth_mbps ? `${data.plan} — ${data.bandwidth_mbps} Mbps` : (data.plan || "Unknown plan");
        setModalText("modal-plan", planLabel);
        setModalText("modal-active-ac", data.active_ac || "Currently offline");
        setModalText(
            "modal-olt",
            connectionType && connectionName
                ? `${connectionType}: ${connectionName}`
                : data.olt_name || "Unknown connection"
        );

        setModalText(
            "modal-olt-interface",
            connectionInterface || data.olt_interface || "Unknown interface"
        );
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


async function openClientInfoById(clientId, options = {}) {
    if (!clientId) {
        console.warn("No client ID supplied.");
        return;
    }

    // clientModalReturnToDown = options.fromDownList === true;

    // const backButton = document.getElementById(
    //     "back-to-down-clients"
    // );

    // if (backButton) {
    //     backButton.classList.toggle(
    //         "hidden",
    //         !clientModalReturnToDown
    //     );
    // }

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

window.openClientInfoFromLog = openClientInfoFromLog;
window.openClientInfoById = openClientInfoById;
window.openClientModal = openClientModal;
window.closeModal = closeModal;
window.formatDateTime = formatDateTime;
window.formatRelativeTime = formatRelativeTime;
window.formatDuration = formatDuration;
window.renderConnectionHistory = renderConnectionHistory;


function getHistoryDateKey(value) {
    if (!value) return null;

    const date = new Date(value);
    if (isNaN(date.getTime())) return null;

    return [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, "0"),
        String(date.getDate()).padStart(2, "0")
    ].join("-");
}

function formatHistoryDateLabel(dateKey) {
    if (!dateKey) return "Unknown date";

    const [year, month, day] = dateKey.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);

    const sameDay = (a, b) =>
        a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate();

    if (sameDay(date, today)) return "Today";
    if (sameDay(date, yesterday)) return "Yesterday";

    return date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric"
    });
}

function initializeHistoryFilters() {
    const dateFilter = document.getElementById("history-date-filter");

    if (!dateFilter) return;

    if (dateFilter.dataset.initialized !== "true") {
        dateFilter.dataset.initialized = "true";

        dateFilter.addEventListener("change", () => {
            applyHistoryDateFilter();
        });
    }

    populateHistoryDateFilter();
}

function populateHistoryDateFilter() {
    const dateFilter = document.getElementById("history-date-filter");
    if (!dateFilter) return;

    const previousValue = dateFilter.value || "all";
    const dates = new Set();

    allConnectionHistory.forEach(item => {
        const upDate = getHistoryDateKey(item.up_time);
        const downDate = getHistoryDateKey(item.down_time);

        if (upDate) dates.add(upDate);
        if (downDate) dates.add(downDate);
    });

    dateFilter.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "all";
    allOption.textContent = "All available dates";
    dateFilter.appendChild(allOption);

    [...dates].sort().reverse().forEach(dateKey => {
        const option = document.createElement("option");
        option.value = dateKey;
        option.textContent = formatHistoryDateLabel(dateKey);
        dateFilter.appendChild(option);
    });

    dateFilter.value = dates.has(previousValue) || previousValue === "all"
        ? previousValue
        : "all";
}

function applyHistoryDateFilter() {
    const dateFilter = document.getElementById("history-date-filter");
    if (!dateFilter) return;

    const selectedDate = dateFilter.value;

    const filteredHistory = allConnectionHistory.filter(item => {
        if (selectedDate === "all") return true;

        return (
            getHistoryDateKey(item.up_time) === selectedDate ||
            getHistoryDateKey(item.down_time) === selectedDate
        );
    });

    renderConnectionHistory(filteredHistory, false);
}

initializeHistoryFilters();


// ============================================================
// PPPoE LIVE TRAFFIC
// ============================================================

const trafficModal = document.getElementById("traffic-modal");
const openTrafficButton = document.getElementById("open-client-traffic");
const closeTrafficButton = document.getElementById("close-traffic-modal");

const trafficUsername = document.getElementById("traffic-username");
const trafficInterface = document.getElementById("traffic-interface");
const trafficAC = document.getElementById("traffic-ac");

const trafficDownload = document.getElementById("traffic-download");
const trafficUpload = document.getElementById("traffic-upload");

const trafficRxPackets = document.getElementById("traffic-rx-packets");
const trafficTxPackets = document.getElementById("traffic-tx-packets");

const trafficStatus = document.getElementById("traffic-status");
const trafficLiveDot = document.getElementById("traffic-live-dot");
const trafficError = document.getElementById("traffic-error");

let trafficInterval = null;
let trafficHistoryInterval = null;
let currentTrafficUsername = null;
let trafficHistoryChart = null;
let currentTrafficRange = "1h";
let trafficHistoryLastTimestamp = null;
let trafficHistorySamples = [];

// ------------------------------------------------------------
// Format traffic speed
// ------------------------------------------------------------

function formatTraffic(bits) {

    bits = Number(bits) || 0;

    if (bits >= 1000000000) {
        return `${(bits / 1000000000).toFixed(2)} Gbps`;
    }

    if (bits >= 1000000) {
        return `${(bits / 1000000).toFixed(2)} Mbps`;
    }

    if (bits >= 1000) {
        return `${(bits / 1000).toFixed(2)} Kbps`;
    }

    return `${bits.toFixed(0)} bps`;
}




// ------------------------------------------------------------
// Format packets
// ------------------------------------------------------------

function formatPackets(value) {

    value = Number(value) || 0;

    return `${Math.round(value).toLocaleString()} / sec`;
}



// ------------------------------------------------------------
// Traffic history chart
// ------------------------------------------------------------

function calculateTrafficStats(samples, key) {
    const values = samples.map(item => Number(item[key]) || 0);

    if (!values.length) {
        return {
            current: 0,
            average: 0,
            maximum: 0,
            minimum: 0,
        };
    }

    const current = values[values.length - 1];
    const average = values.reduce((sum, value) => sum + value, 0) / values.length;
    const maximum = Math.max(...values);
    const minimum = Math.min(...values);

    return {
        current,
        average,
        maximum,
        minimum,
    };
}

function updateTrafficStats(samples) {
    const rx = calculateTrafficStats(samples, "rx");
    const tx = calculateTrafficStats(samples, "tx");

    const elements = {
        "traffic-rx-current": formatTraffic(rx.current),
        "traffic-rx-average": formatTraffic(rx.average),
        "traffic-rx-maximum": formatTraffic(rx.maximum),
        "traffic-rx-minimum": formatTraffic(rx.minimum),
        "traffic-tx-current": formatTraffic(tx.current),
        "traffic-tx-average": formatTraffic(tx.average),
        "traffic-tx-maximum": formatTraffic(tx.maximum),
        "traffic-tx-minimum": formatTraffic(tx.minimum),
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

function renderTrafficHistory(samples, forceReload = false) {
    const chartElement = document.getElementById("traffic-history-chart");

    if (!chartElement || typeof ApexCharts === "undefined") {
        return;
    }

    const rxData = samples.map(item => [
        new Date(item.timestamp).getTime(),
        Number(item.rx) || 0,
    ]);

    const txData = samples.map(item => [
        new Date(item.timestamp).getTime(),
        Number(item.tx) || 0,
    ]);

    // First load or range change: create the chart
    if (!trafficHistoryChart || forceReload) {

const options = {
    chart: {
        type: "area",
        height: 300,
        background: "#ffffff",
        foreColor: "#64748b",
        toolbar: {
            show: false,
        },
        zoom: {
            enabled: false,
        },
        animations: {
            enabled: true,
            dynamicAnimation: {
                enabled: true,
                speed: 300,
            },
        },
        parentHeightOffset: 0,
    },

    series: [
        {
            name: "Download (RX)",
            data: rxData,
        },
        {
            name: "Upload (TX)",
            data: txData,
        },
    ],

    colors: ["#3b82f6", "#22c55e"],

    stroke: {
        curve: "straight",
        width: [1.5, 1.5],
        lineCap: "round",
    },

    fill: {
        type: "solid",
        opacity: [0.25, 0.12],
    },

    dataLabels: {
        enabled: false,
    },

    markers: {
        size: 0,
        hover: {
            size: 4,
        },
    },

    xaxis: {
        type: "datetime",
        tickAmount: 8,
        axisBorder: {
            show: true,
            color: "#e2e8f0",
        },
        axisTicks: {
            show: false,
        },
        labels: {
            datetimeUTC: false,
            style: {
                colors: "#64748b",
                fontSize: "11px",
            },
        },
    },

    yaxis: {
        min: 0,
        forceNiceScale: true,
        labels: {
            formatter: function (value) {
                return formatTraffic(value);
            },
            style: {
                colors: "#64748b",
                fontSize: "11px",
            },
        },
    },


tooltip: {
    enabled: true,
    theme: "light",
    shared: true,
    intersect: false,
    followCursor: true,
    x: {
        formatter: function (value) {
            return new Date(value).toLocaleTimeString("en-PH", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
            });
        },
    },
    y: {
        formatter: function (value) {
            return formatTraffic(value);
        },
    },
},


    legend: {
        show: true,
        position: "top",
        horizontalAlign: "left",
        fontSize: "11px",
        markers: {
            size: 4,
        },
    },

    grid: {
        borderColor: "#e2e8f0",
        strokeDashArray: 0,
        padding: {
            left: 8,
            right: 8,
        },
    },

    noData: {
        text: "No traffic history available",
        align: "center",
        verticalAlign: "middle",
        style: {
            color: "#64748b",
            fontSize: "13px",
        },
    },
};


        trafficHistoryChart = new ApexCharts(chartElement, options);
        trafficHistoryChart.render();
        return;
    }

    // Existing chart: update the existing series
    trafficHistoryChart.updateSeries([
        {
            name: "Download (RX)",
            data: rxData,
        },
        {
            name: "Upload (TX)",
            data: txData,
        },
    ], true);
}

async function loadTrafficHistory(forceReload = false) {
    if (!currentTrafficUsername) {
        return;
    }

    try {
        let url =
            `/client-traffic-history/?username=${encodeURIComponent(currentTrafficUsername)}` +
            `&range=${encodeURIComponent(currentTrafficRange)}`;

        if (!forceReload && trafficHistoryLastTimestamp) {
            url += `&since=${encodeURIComponent(trafficHistoryLastTimestamp)}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data.found) {
            trafficHistorySamples = [];
            trafficHistoryLastTimestamp = null;
            renderTrafficHistory([], forceReload);
            updateTrafficStats([]);
            return;
        }

        const newSamples = data.samples || [];

        if (forceReload || !trafficHistorySamples.length) {
            trafficHistorySamples = newSamples;
        } else if (newSamples.length) {
            trafficHistorySamples = [
                ...trafficHistorySamples,
                ...newSamples,
            ];
        }

        if (trafficHistorySamples.length) {
            trafficHistoryLastTimestamp =
                trafficHistorySamples[
                    trafficHistorySamples.length - 1
                ].timestamp;
        }

        renderTrafficHistory(
            trafficHistorySamples,
            forceReload
        );

        updateTrafficStats(trafficHistorySamples);

        const rangeLabels = {
            "1h": "Last 1 hour",
            "6h": "Last 6 hours",
            "12h": "Last 12 hours",
            "24h": "Last 24 hours",
            "7d": "Last 7 days",
            "15d": "Last 15 days",
        };

        const rangeLabel = document.getElementById(
            "traffic-history-range-label"
        );

        if (rangeLabel) {
            rangeLabel.textContent =
                rangeLabels[currentTrafficRange] ||
                "Traffic History";
        }

    } catch (error) {
        console.error("TRAFFIC HISTORY ERROR:", error);

        if (forceReload) {
            trafficHistorySamples = [];
            trafficHistoryLastTimestamp = null;
            renderTrafficHistory([], true);
            updateTrafficStats([]);
        }
    }
}

function setTrafficRange(range) {
    currentTrafficRange = range;
    trafficHistoryLastTimestamp = null;
    trafficHistorySamples = [];

    document.querySelectorAll(".traffic-range-btn").forEach(button => {
        const active = button.dataset.trafficRange === range;

        if (active) {
            button.className =
                "traffic-range-btn rounded-md bg-gray-900 px-2 py-1 text-[10px] font-semibold text-white";
        } else {
            button.className =
                "traffic-range-btn rounded-md bg-gray-100 px-2 py-1 text-[10px] font-semibold text-gray-600";
        }
    });

    loadTrafficHistory(true);
}

document.addEventListener("click", function(event) {
    const button = event.target.closest(".traffic-range-btn");

    if (!button) {
        return;
    }

    const range = button.dataset.trafficRange;

    if (!range) {
        return;
    }

    setTrafficRange(range);
});
// ------------------------------------------------------------
// Reset traffic display
// ------------------------------------------------------------

function resetTrafficDisplay() {

    if (trafficDownload) {
        trafficDownload.textContent = "0 Mbps";
    }

    if (trafficUpload) {
        trafficUpload.textContent = "0 Mbps";
    }

    if (trafficRxPackets) {
        trafficRxPackets.textContent = "0 / sec";
    }

    if (trafficTxPackets) {
        trafficTxPackets.textContent = "0 / sec";
    }

    if (trafficError) {
        trafficError.classList.add("hidden");
        trafficError.textContent = "";
    }

    if (trafficStatus) {
        trafficStatus.textContent = "CONNECTING...";
        trafficStatus.className =
            "text-xs font-semibold text-yellow-600";
    }

    if (trafficLiveDot) {
        trafficLiveDot.className =
            "h-2.5 w-2.5 rounded-full bg-yellow-500";
    }
}


// ------------------------------------------------------------
// Load traffic
// ------------------------------------------------------------
let trafficRefreshInterval = null;
async function loadClientTraffic() {

    if (!currentTrafficUsername) {
        return;
    }

    try {

        const response = await fetch(
            `/client-traffic/?username=${encodeURIComponent(currentTrafficUsername)}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data.found) {

            if (trafficStatus) {
                trafficStatus.textContent = "OFFLINE";
                trafficStatus.className =
                    "text-xs font-semibold text-red-600";
            }

            if (trafficLiveDot) {
                trafficLiveDot.className =
                    "h-2.5 w-2.5 rounded-full bg-red-500";
            }

            if (trafficError) {
                trafficError.textContent =
                    data.message || "Unable to retrieve traffic.";
                trafficError.classList.remove("hidden");
            }

            return;
        }

        // Basic information
        if (trafficUsername) {
            trafficUsername.textContent = data.username || "-";
        }

        if (trafficInterface) {
            trafficInterface.textContent =
                data.interface || "-";
        }

        if (trafficAC) {
            trafficAC.textContent =
                data.ac || "-";
        }

        // Traffic
        if (trafficDownload) {
            trafficDownload.textContent =
                formatTraffic(data.rx_bits_per_second);
        }

        if (trafficUpload) {
            trafficUpload.textContent =
                formatTraffic(data.tx_bits_per_second);
        }

        // Packets
        if (trafficRxPackets) {
            trafficRxPackets.textContent =
                formatPackets(data.rx_packets_per_second);
        }

        if (trafficTxPackets) {
            trafficTxPackets.textContent =
                formatPackets(data.tx_packets_per_second);
        }

        // LIVE status
        if (trafficStatus) {
            trafficStatus.textContent = "LIVE";
            trafficStatus.className =
                "text-xs font-semibold text-green-600";
        }

        if (trafficLiveDot) {
            trafficLiveDot.className =
                "h-2.5 w-2.5 rounded-full bg-green-500";
        }

        if (trafficError) {
            trafficError.classList.add("hidden");
            trafficError.textContent = "";
        }

    } catch (error) {

        console.error("TRAFFIC ERROR:", error);

        if (trafficStatus) {
            trafficStatus.textContent = "ERROR";
            trafficStatus.className =
                "text-xs font-semibold text-red-600";
        }

        if (trafficLiveDot) {
            trafficLiveDot.className =
                "h-2.5 w-2.5 rounded-full bg-red-500";
        }

        if (trafficError) {
            trafficError.textContent =
                "Unable to retrieve traffic data.";
            trafficError.classList.remove("hidden");
        }
    }
}


// ------------------------------------------------------------
// Open traffic modal
// ------------------------------------------------------------

function openTrafficModal(username) {
    if (!trafficModal || !username) {
        return;
    }

    currentTrafficUsername = username;
    currentTrafficRange = "1h";
    trafficHistoryLastTimestamp = null;
    trafficHistorySamples = [];

    resetTrafficDisplay();

    if (trafficUsername) {
        trafficUsername.textContent = username;
    }

    if (window.ModalNavigation) {
        window.ModalNavigation.open("traffic-modal");
    } else {
        trafficModal.classList.remove("hidden");
        trafficModal.classList.add("flex");
    }

    // Stop previous polling
    if (trafficInterval) {
        clearInterval(trafficInterval);
    }

    if (trafficHistoryInterval) {
        clearInterval(trafficHistoryInterval);
    }

    // First requests immediately
    loadClientTraffic();
    loadTrafficHistory();

    // Start polling
    trafficInterval = setInterval(loadClientTraffic, 2000);
    trafficHistoryInterval = setInterval(loadTrafficHistory, 5000);
}


// ------------------------------------------------------------
// Traffic modal cleanup
// Runs when closed by Back, Escape, or closeAll()
// ------------------------------------------------------------

if (trafficModal) {
    trafficModal.addEventListener("modal:before-close", () => {
        if (trafficInterval) {
            clearInterval(trafficInterval);
            trafficInterval = null;
        }

        if (trafficHistoryInterval) {
            clearInterval(trafficHistoryInterval);
            trafficHistoryInterval = null;
        }

        currentTrafficUsername = null;
    });
}

// ------------------------------------------------------------
// Close traffic modal
// ------------------------------------------------------------

function closeTrafficModal() {

    if (trafficInterval) {
        clearInterval(trafficInterval);
        trafficInterval = null;
    }
    if (trafficHistoryInterval) {
        clearInterval(trafficHistoryInterval);
        trafficHistoryInterval = null;
    }

    currentTrafficUsername = null;

    if (window.ModalNavigation) {
        window.ModalNavigation.back();
    } else if (trafficModal) {
        trafficModal.classList.add("hidden");
        trafficModal.classList.remove("flex");
    }
}


// ------------------------------------------------------------
// Traffic button
// ------------------------------------------------------------

if (openTrafficButton) {

    openTrafficButton.addEventListener("click", function() {

        const usernameElement =
            document.getElementById("modal-username");

        if (!usernameElement) {
            return;
        }

        const username =
            usernameElement.textContent.trim();

        if (
            !username ||
            username === "-" ||
            username === "Loading..." ||
            username === "Not found"
        ) {
            return;
        }

        openTrafficModal(username);
    });
}


// ------------------------------------------------------------
// Close button
// ------------------------------------------------------------

if (closeTrafficButton) {

    closeTrafficButton.addEventListener(
        "click",
        closeTrafficModal
    );
}


// ------------------------------------------------------------
// Click outside traffic modal
// ------------------------------------------------------------

if (trafficModal) {

    trafficModal.addEventListener(
        "click",
        function(event) {

            if (event.target === trafficModal) {
                closeTrafficModal();
            }

        }
    );
}

// ------------------------------------------------------------
// Enable / disable traffic button based on client status
// ------------------------------------------------------------

function updateTrafficButton(active) {

    if (!openTrafficButton) {
        return;
    }

    openTrafficButton.disabled = !active;

    if (active) {

        openTrafficButton.classList.remove(
            "bg-gray-400",
            "cursor-not-allowed"
        );

        openTrafficButton.classList.add(
            "bg-gray-900"
        );

    } else {

        openTrafficButton.classList.remove(
            "bg-gray-900"
        );

        openTrafficButton.classList.add(
            "bg-gray-400",
            "cursor-not-allowed"
        );

    }
}