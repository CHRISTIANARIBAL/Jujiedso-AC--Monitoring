let selectedOLT = null;

const terminal = document.getElementById("terminal");
const selectedOLTLabel = document.getElementById("selectedOLT");
const terminalStatus = document.getElementById("terminalStatus");

const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const macInput = document.getElementById("mac");

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

    /*
        CLEAR EVERYTHING FROM
        THE PREVIOUS OLT
    */

    clearTerminal();

    /*
        Remove active state
        from all buttons
    */

    oltButtons.forEach(button => {

        button.classList.remove("active");

    });


    /*
        Activate selected button
    */

    const selectedButton =
        document.querySelector(
            `[data-olt="${oltName}"]`
        );

    if (selectedButton) {

        selectedButton.classList.add("active");

    }


    /*
        Update selected OLT display
    */

    selectedOLTLabel.textContent =
        oltName;


    /*
        New terminal session
    */

    writeTerminal(
        `==========================================`
    );

    writeTerminal(
        `OLT SELECTED: ${oltName}`
    );

    writeTerminal(
        `==========================================`
    );

    writeTerminal("");

    terminalStatus.textContent =
        "READY";


    /*
        Clear MAC input when
        switching OLT
    */

    macInput.value = "";
}


oltButtons.forEach(button => {

    button.addEventListener(
        "click",
        () => {

            const oltName =
                button.dataset.olt;

            selectOLT(oltName);

        }
    );

});


lookupButton.addEventListener(
    "click",
    async () => {

        if (!selectedOLT) {

            alert(
                "Please select an OLT first."
            );

            return;

        }


        const username =
            usernameInput.value.trim();

        const password =
            passwordInput.value;

        const mac =
            macInput.value.trim();


        if (!username) {

            alert(
                "Enter your username."
            );

            return;

        }


        if (!password) {

            alert(
                "Enter your password."
            );

            return;

        }


        if (!mac) {

            alert(
                "Enter a MAC address."
            );

            return;

        }


        lookupButton.disabled = true;

        terminalStatus.textContent =
            "CONNECTING";


        clearTerminal();


        writeTerminal(
            `OLT: ${selectedOLT}`
        );

        writeTerminal(
            `MAC: ${mac}`
        );

        writeTerminal("");

        writeTerminal(
            "Starting lookup..."
        );

        writeTerminal("");


        try {

            const response =
                await fetch(
                    "/api/lookup",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            olt: selectedOLT,

                            username: username,

                            password: password,

                            mac: mac

                        })
                    }
                );


            const data =
                await response.json();


            /*
                Display terminal output
            */

            if (data.terminal) {

                terminal.textContent =
                    data.terminal;

            }


            /*
                Display result
            */

            if (data.success) {

                terminalStatus.textContent =
                    "SUCCESS";

                displayResult(data);

            } else {

                terminalStatus.textContent =
                    "FAILED";

                writeTerminal("");

                writeTerminal(
                    `ERROR: ${data.error}`
                );

            }


        } catch (error) {

            terminalStatus.textContent =
                "ERROR";

            writeTerminal("");

            writeTerminal(
                `SERVER ERROR: ${error.message}`
            );

        }


        lookupButton.disabled = false;

    }
);


function displayResult(data) {

    const onu = data.onu || {};
    const optical = data.optical || {};

    resultContainer.innerHTML = `

        <h3>ONU INFORMATION</h3>

        <div class="result-grid">

            <div class="result-item">
                <div class="result-label">
                    MAC
                </div>

                <div class="result-value">
                    ${onu.mac || "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    ONU
                </div>

                <div class="result-value">
                    ${onu.onu || "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    INTERFACE
                </div>

                <div class="result-value">
                    ${onu.interface || "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    TEMPERATURE
                </div>

                <div class="result-value">
                    ${optical.Temperature ?? "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    VOLTAGE
                </div>

                <div class="result-value">
                    ${optical.Voltage ?? "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    TX BIAS
                </div>

                <div class="result-value">
                    ${optical.TX_Bias ?? "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    TX POWER
                </div>

                <div class="result-value">
                    ${optical.TX_Power ?? "-"}
                </div>
            </div>


            <div class="result-item">
                <div class="result-label">
                    RX POWER
                </div>

                <div class="result-value">
                    ${optical.RX_Power ?? "-"}
                </div>
            </div>

        </div>

    `;
}