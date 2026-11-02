document.addEventListener("DOMContentLoaded", () => {

    const outageList = document.getElementById(
        "barangay-outage-list"
    );

    const outageCount = document.getElementById(
        "barangay-outage-count"
    );

    const loading = document.getElementById(
        "barangay-loading"
    );

    const modal = document.getElementById(
        "barangay-clients-modal"
    );

    const modalTitle = document.getElementById(
        "barangay-clients-title"
    );

    const modalSubtitle = document.getElementById(
        "barangay-clients-subtitle"
    );

    const clientList = document.getElementById(
        "barangay-clients-list"
    );

    const clientSearch = document.getElementById(
        "barangay-client-search"
    );

    const closeModal = document.getElementById(
        "close-barangay-clients"
    );

    if (
        !outageList ||
        !outageCount ||
        !modal ||
        !clientList
    ) {
        return;
    }

    let locations = [];
    let selectedClients = [];
    let soundEnabled = false;
    let audioContext = null;
    let previousAffectedBarangays = null;

    const escapeHTML = (value) =>
        String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        })[char]);

    
    // =====================================
    // BARANGAY ALERT SOUND
    // =====================================
    const soundToggle = document.getElementById("barangay-sound-toggle");
    const soundIcon = document.getElementById("barangay-sound-icon");
    const soundLabel = document.getElementById("barangay-sound-label");

    function updateSoundButton() {
        if (!soundToggle) return;
        soundToggle.setAttribute("aria-pressed", String(soundEnabled));
        soundIcon.textContent = soundEnabled ? "🔊" : "🔇";
        soundLabel.textContent = soundEnabled ? "Sound ON" : "Enable Sound";
        soundToggle.classList.toggle("bg-green-50", soundEnabled);
        soundToggle.classList.toggle("border-green-300", soundEnabled);
        soundToggle.classList.toggle("text-green-700", soundEnabled);
    }
    function playBarangayAlert() {
        if (!soundEnabled) return;

        const alertAudio = document.getElementById("barangay-alert-audio");
        if (!alertAudio) return;

        alertAudio.pause();
        alertAudio.currentTime = 0;

        alertAudio.play().catch(error => {
            console.warn("Barangay alert playback failed:", error);
        });
    }

    if (soundToggle) {
        soundToggle.addEventListener("click", async () => {
            if (soundEnabled) {
                soundEnabled = false;
                updateSoundButton();
                return;
            }

            try {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (!AudioContextClass) throw new Error("Web Audio is not supported by this browser.");

                audioContext ??= new AudioContextClass();
                await audioContext.resume();

                soundEnabled = true;
                updateSoundButton();
                playBarangayAlert();
            } catch (error) {
                console.error("Unable to enable alert sound:", error);
                alert("Unable to enable alert sound. Please check your browser settings.");
            }
        });
    }



    // =====================================
    // RENDER BARANGAY OUTAGE CARDS
    // =====================================

    function renderBarangayOutages() {

        const affected = locations
            .filter(location => {

                const total = Number(location.total) || 0;
                const down = Number(location.down) || 0;

                return (
                    total > 0 &&
                    down >= 2 &&
                    down / total >= 0.25
                );
            })
            .sort((a, b) => {

                const downDifference =
                    Number(b.down) - Number(a.down);

                if (downDifference !== 0) {
                    return downDifference;
                }

                return (
                    Number(b.down) / Math.max(Number(b.total), 1) -
                    Number(a.down) / Math.max(Number(a.total), 1)
                );
            });

        
        // DETECT NEWLY AFFECTED BARANGAYS
        const currentAffectedBarangays = new Set(
            affected.map(location => location.name)
        );

        if (previousAffectedBarangays !== null) {
            const newlyAffected = affected.filter(
                location => !previousAffectedBarangays.has(location.name)
            );

            if (newlyAffected.length > 0) {
                console.warn(
                    "New barangay outage detected:",
                    newlyAffected.map(location => location.name)
                );
                playBarangayAlert();
            }
        }

        previousAffectedBarangays = currentAffectedBarangays;

        outageList.replaceChildren();
        outageCount.textContent = `${affected.length} affected`;


        if (!affected.length) {

            const empty = document.createElement("p");

            empty.className =
                "col-span-full py-6 text-center text-sm text-gray-500";

            empty.textContent =
                "All barangays are below the outage alert threshold.";

            outageList.appendChild(empty);

            return;
        }

        affected.forEach(location => {

            const total = Number(location.total) || 0;
            const down = Number(location.down) || 0;
            const online = Number(location.online) || 0;

            const percentage = Math.round(
                (down / total) * 100
            );

            const card = document.createElement("button");

            card.type = "button";
            card.dataset.location = location.name;

            card.className =
                "w-full rounded-lg border border-red-200 " +
                "bg-red-50 p-4 text-left transition " +
                "hover:border-red-400 hover:bg-red-100";

            card.innerHTML = `

                <div class="flex items-center justify-between gap-2">

                    <span class="break-words font-semibold text-gray-900">
                        ${escapeHTML(location.name)}
                    </span>

                    <span class="shrink-0 rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-red-700">
                        ${percentage}% down
                    </span>

                </div>

                <p class="mt-3 text-sm text-gray-600">
                    ${down} down of ${total} clients
                </p>

                <div class="mt-3 h-2 overflow-hidden rounded-full bg-gray-200">

                    <div
                        class="h-full rounded-full bg-red-500"
                        style="width: ${percentage}%">
                    </div>

                </div>

                <p class="mt-2 text-xs text-green-700">
                    ${online} clients online
                </p>

                <p class="mt-3 text-xs font-medium text-red-700">
                    Click to view down clients →
                </p>

            `;

            outageList.appendChild(card);

        });

    }


    // =====================================
    // OPEN DOWN CLIENTS MODAL
    // =====================================

    function openClients(locationName) {

        const location = locations.find(
            item => item.name === locationName
        );

        if (!location) return;

        selectedClients = (location.clients || [])
            .filter(client => client.status === "Down");

        modalTitle.textContent =
            `${location.name} — Down Clients`;

        modalSubtitle.textContent =
            `${selectedClients.length} disconnected clients`;

        clientSearch.value = "";

        renderClients();

        modal.classList.remove("hidden");
        modal.classList.add("flex");

    }


    // =====================================
    // RENDER DOWN CLIENTS
    // =====================================

    function renderClients() {

        const query = clientSearch.value
            .trim()
            .toLowerCase();

        const filtered = selectedClients.filter(client => {

            return [
                client.username,
                client.mac,
                client.ac,
                client.nap
            ].some(value =>
                String(value || "")
                    .toLowerCase()
                    .includes(query)
            );

        });

        clientList.replaceChildren();

        if (!filtered.length) {

            const empty = document.createElement("p");

            empty.className =
                "py-8 text-center text-sm text-gray-500";

            empty.textContent =
                "No matching disconnected clients found.";

            clientList.appendChild(empty);

            return;
        }

        filtered.forEach(client => {

            const row = document.createElement("div");

            row.className =
                "flex flex-col gap-3 border-b border-gray-100 py-3 " +
                "sm:flex-row sm:items-center sm:justify-between";

            row.innerHTML = `

                <div class="min-w-0">

                    <p class="break-all text-sm font-semibold text-gray-900">
                        ${escapeHTML(client.username)}
                    </p>

                    <p class="mt-1 break-all text-xs text-gray-500">
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
                    class="shrink-0 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700">

                    View Details

                </button>

            `;

            clientList.appendChild(row);

        });

    }


    // =====================================
    // EVENT LISTENERS
    // =====================================

    outageList.addEventListener("click", event => {

        const card = event.target.closest(
            "button[data-location]"
        );

        if (!card) return;

        openClients(card.dataset.location);

    });


    clientList.addEventListener("click", event => {

        const button = event.target.closest(
            "button[data-client-id]"
        );

        if (!button) return;

        const clientId = Number(button.dataset.clientId);

        if (
            !Number.isInteger(clientId) ||
            clientId <= 0
        ) {
            return;
        }

        if (typeof window.openClientInfoById === "function") {

            window.openClientInfoById(clientId);

        } else {

            console.error(
                "openClientInfoById is not available."
            );

            alert("Unable to open client details.");

        }

    });


    clientSearch.addEventListener(
        "input",
        renderClients
    );


    function hideModal() {

        modal.classList.add("hidden");
        modal.classList.remove("flex");

    }


    closeModal.addEventListener("click", hideModal);


    modal.addEventListener("click", event => {

        if (event.target === modal) {
            hideModal();
        }

    });


    document.addEventListener("keydown", event => {

        if (event.key === "Escape") {
            hideModal();
        }

    });


    // =====================================
    // FETCH BARANGAY DATA
    // =====================================

    async function loadLocations() {

        try {

            const response = await fetch(
                "/api/location-summary/",
                {
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    credentials: "same-origin"
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Request failed: ${response.status}`
                );
            }

            const data = await response.json();

            locations = Array.isArray(data.locations)
                ? data.locations
                : [];

            renderBarangayOutages();

            loading.classList.add("hidden");

        } catch (error) {

            console.error(
                "Unable to load barangay statistics:",
                error
            );

            outageCount.textContent = "Unavailable";

            loading.textContent =
                "Unable to load barangay statistics. Please check your connection.";

            loading.classList.remove("hidden");

        }

    }


    // Initial load
    loadLocations();

    // Refresh every 10 seconds
    setInterval(loadLocations, 10000);

});