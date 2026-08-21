// const socket = new WebSocket(
//     "ws://" + window.location.host + "/ws/monitor/"
// );
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

const socket = new WebSocket(
    `${protocol}//${window.location.host}/ws/monitor/`
);

socket.onopen = () => {
    console.log("WEBSOCKET CONNECTED");
};

socket.onmessage = (event) => {

    const data = JSON.parse(event.data);

    console.log("SERVER:", data);

    // ==========================================
    // ACTIVE USER COUNTS
    // ==========================================

    if (data.type === "active_counts") {

        const counts = data.counts || {};

        let total = 0;

        Object.entries(counts).forEach(([acId, count]) => {

            const number = Number(count) || 0;

            total += number;

            const acCount =
                document.getElementById(`ac-count-${acId}`);

            const panelCount =
                document.getElementById(`panel-count-${acId}`);

            if (acCount) {
                acCount.textContent = number;
            }

            if (panelCount) {
                panelCount.textContent = `${number} users`;
            }
        });

        const totalElement =
            document.getElementById("total-active-users");

        if (totalElement) {
            totalElement.textContent = total;
        }

        return;
    }

    // ==========================================
    // REALTIME LOG EVENT
    // ==========================================

    if (!data.event) {
        return;
    }

    const username =
        data.username || "UNKNOWN";

    const mac =
        data.mac || "No MAC";

    const ac =
        data.ac;

    const eventType =
        data.event;

    const timestamp =
        data.timestamp;

    if (!ac) {
        return;
    }

    // ==========================================
    // FIND AC PANEL
    // ==========================================

    const acInfo =
        (window.MONITOR_ACS || []).find(
            item => item.name === ac
        );

    if (!acInfo) {

        console.warn(
            "AC panel not found:",
            ac
        );

        return;
    }

    const logContainer =
        document.getElementById(
            `logs-${acInfo.id}`
        );

    if (!logContainer) {

        console.warn(
            "Log container not found:",
            `logs-${acInfo.id}`
        );

        return;
    }

    // ==========================================
    // EVENT BADGE
    // ==========================================

    let badgeClass =
        "bg-gray-100 text-gray-600";

    let badgeText =
        eventType;

    if (eventType === "LOGIN") {

        badgeClass =
            "bg-green-50 text-green-700";

        badgeText =
            "LOGIN";

    } else if (eventType === "LOGOUT") {

        badgeClass =
            "bg-red-50 text-red-700";

        badgeText =
            "LOGOUT";

    } else if (eventType === "AUTH_FAILURE") {

        badgeClass =
            "bg-orange-50 text-orange-700";

        badgeText =
            "AUTH FAIL";

    } else if (eventType === "CONNECTION") {

        badgeClass =
            "bg-blue-50 text-blue-700";

        badgeText =
            "CONNECTION";
    }

    // ==========================================
    // FORMAT TIMESTAMP
    // ==========================================

    let formattedTime = "";

    if (timestamp) {

        const date =
            new Date(timestamp);

        if (!isNaN(date)) {

            formattedTime =
                date.toLocaleString(
                    "en-US",
                    {
                        month: "short",
                        day: "2-digit",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit"
                    }
                );
        }
    }

    // ==========================================
    // CREATE LOG ELEMENT
    // ==========================================

    const logElement =
        document.createElement("div");

    logElement.className =
        "log-entry cursor-pointer border-b border-gray-100 px-4 py-2.5 hover:bg-gray-50";

    logElement.dataset.username =
        username;

    logElement.dataset.mac =
        mac;

    logElement.innerHTML = `
        <div class="flex items-start justify-between gap-3">

            <div class="min-w-0">

                <p class="truncate text-sm font-medium text-gray-900">
                    ${username}
                </p>

                <p class="mt-0.5 truncate text-[11px] text-gray-500">
                    ${mac}
                </p>

            </div>

            <div class="shrink-0 text-right">

                <span class="rounded-full ${badgeClass} px-2 py-0.5 text-[10px] font-medium">
                    ${badgeText}
                </span>

                <p class="mt-1 whitespace-nowrap text-[10px] text-gray-400">
                    ${formattedTime}
                </p>

            </div>

        </div>
    `;

    logContainer.prepend(logElement);

    // ==========================================
    // LIMIT LOGS
    // ==========================================

    while (
        logContainer.children.length > 50
    ) {

        logContainer.removeChild(
            logContainer.lastElementChild
        );
    }

    // ==========================================
    // HIGHLIGHT NEW LOG
    // ==========================================

    logElement.classList.add(
        "bg-blue-50"
    );

    setTimeout(() => {

        logElement.classList.remove(
            "bg-blue-50"
        );

    }, 1500);
};

socket.onclose = (event) => {

    console.log(
        "WEBSOCKET CLOSED",
        event.code,
        event.reason
    );
};

socket.onerror = (error) => {

    console.error(
        "WEBSOCKET ERROR:",
        error
    );
};