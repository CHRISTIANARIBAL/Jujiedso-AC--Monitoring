
document.addEventListener("DOMContentLoaded", function () {
    console.log("Dashboard JS loaded.");

    if (!Array.isArray(window.MONITOR_ACS)) {
        console.warn("MONITOR_ACS is not defined.");
        return;
    }

    window.MONITOR_ACS.forEach(function (ac) {
        const logContainer = document.getElementById(`logs-${ac.id}`);
        const countElement = document.getElementById(`ac-count-${ac.id}`);
        const panelCountElement = document.getElementById(`panel-count-${ac.id}`);

        if (!logContainer) console.warn(`Missing log container for ${ac.name}`);
        if (!countElement) console.warn(`Missing count element for ${ac.name}`);
        if (!panelCountElement) console.warn(`Missing panel count for ${ac.name}`);
    });
});