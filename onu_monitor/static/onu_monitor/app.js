let selectedOLT = null;

const terminal = document.getElementById("terminal");
const selectedOLTLabel = document.getElementById("selectedOLT");
const terminalStatus = document.getElementById("terminalStatus");

const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const lookupMode = document.getElementById("lookupMode");
const lookupValue = document.getElementById("lookupValue");

const lookupButton = document.getElementById("lookupButton");
const resultContainer = document.getElementById("result");

const oltButtons = document.querySelectorAll(".olt-button");

function writeTerminal(text) {
    terminal.textContent += text + "\n";
    terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
    terminal.textContent = "";
    resultContainer.innerHTML = "";
}

function selectOLT(oltName) {
    selectedOLT = oltName;
    clearTerminal();

    oltButtons.forEach(button => {
        button.classList.remove("active");
    });

    const selectedButton = document.querySelector(`[data-olt="${oltName}"]`);

    if (selectedButton) {
        selectedButton.classList.add("active");
    }

    selectedOLTLabel.textContent = oltName;

    writeTerminal("==========================================");
    writeTerminal(`OLT SELECTED: ${oltName}`);
    writeTerminal("==========================================");
    writeTerminal("");

    terminalStatus.textContent = "READY";
    lookupValue.value = "";
}

oltButtons.forEach(button => {
    button.addEventListener("click", () => {
        selectOLT(button.dataset.olt);
    });
});

lookupMode.addEventListener("change", () => {
    lookupValue.value = "";

    if (lookupMode.value === "onu") {
        lookupValue.placeholder = "ONU / PON (e.g. gpon0/2:27)";
    } else {
        lookupValue.placeholder = "MAC Address";
    }
});

lookupButton.addEventListener("click", async () => {
    if (!selectedOLT) {
        alert("Please select an OLT first.");
        return;
    }

    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    const mode = lookupMode.value;
    const value = lookupValue.value.trim();

    if (!username) {
        alert("Enter the username.");
        return;
    }

    if (!password) {
        alert("Enter the password.");
        return;
    }

    if (!value) {
        alert(
            mode === "onu"
                ? "Enter an ONU / PON."
                : "Enter a MAC address."
        );
        return;
    }

    lookupButton.disabled = true;
    terminalStatus.textContent = "CONNECTING";

    clearTerminal();

    writeTerminal(`OLT: ${selectedOLT}`);
    // writeTerminal(`USERNAME: ${username}`);

    if (mode === "onu") {
        writeTerminal(`ONU: ${value}`);
    } else {
        writeTerminal(`MAC: ${value}`);
    }

    writeTerminal("");
    writeTerminal("Starting lookup...");
    writeTerminal("");

    try {
        const csrfToken = document.cookie
            .split("; ")
            .find((cookie) => cookie.startsWith("csrftoken="))
            ?.split("=")
            .slice(1)
            .join("=");

        if (!csrfToken) {
            throw new Error("CSRF token missing. Refresh the page and try again.");
        }

        const response = await fetch("/onu/api/lookup/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": decodeURIComponent(csrfToken)
            },
            body: JSON.stringify({
                olt: selectedOLT,
                username: username,
                password: password,
                mode: mode,
                value: value
            })
        });

        const data = await response.json();

        if (data.terminal) {
            terminal.textContent = data.terminal;
            terminal.scrollTop = terminal.scrollHeight;
        }

        if (data.success) {
            terminalStatus.textContent = "SUCCESS";
            displayResult(data);
        } else {
            terminalStatus.textContent = "FAILED";
            writeTerminal("");
            writeTerminal(`ERROR: ${data.error}`);
        }

    } catch (error) {
        terminalStatus.textContent = "ERROR";
        writeTerminal("");
        writeTerminal(`SERVER ERROR: ${error.message}`);
    }

    lookupButton.disabled = false;
});

function displayResult(data) {
    const onu = data.onu || {};
    const optical = data.optical || {};
    const pppoeClients = data.pppoe_clients || [];

    if (data.lookup_mode === "onu") {
        let pppoeHtml = "";

        if (pppoeClients.length === 0) {
            pppoeHtml = `
                <h3>PPPoE CLIENT</h3>

                <div class="result-item">
                    <div class="result-label">STATUS</div>
                    <div class="result-value">NO MATCHING PPPoE CLIENT</div>
                </div>
            `;
        } else {
            pppoeHtml = `
                <h3>PPPoE CLIENT${pppoeClients.length > 1 ? "S" : ""}</h3>

                <div class="result-grid">
                    ${pppoeClients.map(client => `
                        <div class="result-item">
                            <div class="result-label">USERNAME</div>
                            <div class="result-value">${client.username || "-"}</div>
                        </div>

                        <div class="result-item">
                            <div class="result-label">MAC</div>
                            <div class="result-value">${client.mac || "-"}</div>
                        </div>

                        <div class="result-item">
                            <div class="result-label">AC</div>
                            <div class="result-value">${client.ac || "-"}</div>
                        </div>

                        <div class="result-item">
                            <div class="result-label">OLT</div>
                            <div class="result-value">${client.olt_name || client.connection_name || "-"}</div>
                        </div>

                        <div class="result-item">
                            <div class="result-label">OLT INTERFACE</div>
                            <div class="result-value">${client.connection_interface || client.olt_interface || "-"}</div>
                        </div>

                        <div class="result-item">
                            <div class="result-label">CONNECTION TYPE</div>
                            <div class="result-value">${client.connection_type || "-"}</div>
                        </div>

                        <div class="result-item">
                            <div class="result-label">LAST SEEN</div>
                            <div class="result-value">${client.last_seen || "-"}</div>
                        </div>
                    `).join("")}
                </div>
            `;
        }

        resultContainer.innerHTML = `
            <h3>ONU INFORMATION</h3>

            <div class="result-grid">

                <div class="result-item">
                    <div class="result-label">MAC</div>
                    <div class="result-value">${onu.mac || "-"}</div>
                </div>

                <div class="result-item">
                    <div class="result-label">ONU</div>
                    <div class="result-value">${onu.onu || "-"}</div>
                </div>

                <div class="result-item">
                    <div class="result-label">INTERFACE</div>
                    <div class="result-value">${onu.interface || "-"}</div>
                </div>

            </div>

            ${pppoeHtml}
        `;

        return;
    }

    resultContainer.innerHTML = `
        <h3>ONU INFORMATION</h3>

        <div class="result-grid">

            <div class="result-item">
                <div class="result-label">MAC</div>
                <div class="result-value">${onu.mac || "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">ONU</div>
                <div class="result-value">${onu.onu || "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">INTERFACE</div>
                <div class="result-value">${onu.interface || "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">TEMPERATURE</div>
                <div class="result-value">${optical.Temperature ?? "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">VOLTAGE</div>
                <div class="result-value">${optical.Voltage ?? "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">TX BIAS</div>
                <div class="result-value">${optical.TX_Bias ?? "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">TX POWER</div>
                <div class="result-value">${optical.TX_Power ?? "-"}</div>
            </div>

            <div class="result-item">
                <div class="result-label">RX POWER</div>
                <div class="result-value">${optical.RX_Power ?? "-"}</div>
            </div>

        </div>
    `;
}