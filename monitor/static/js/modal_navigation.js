
/**
 * Shared Modal Navigation
 * Supports nested modal history and preserves previous modal state.
 */
(() => {
    const MODAL_IDS = [
        "location-status-modal",
        "location-clients-modal",
        "client-modal",
        "traffic-modal",
    ];

    const history = [];
    let currentModalId = null;

    const getModal = (id) => document.getElementById(id);

    function isVisible(modal) {
        return !!modal && !modal.classList.contains("hidden");
    }

    function hide(id) {
        const modal = getModal(id);
        if (!modal) return;

        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
    function beforeClose(id) {
        const modal = getModal(id);
        if (!modal) return;

        modal.dispatchEvent(new CustomEvent("modal:before-close"));
    }

    function show(id) {
        const modal = getModal(id);
        if (!modal) return false;

        modal.classList.remove("hidden");
        modal.classList.add("flex");
        currentModalId = id;

        updateBackButtons();
        return true;
    }

    function updateBackButtons() {
        MODAL_IDS.forEach((id) => {
            const modal = getModal(id);
            if (!modal) return;

            const button = modal.querySelector("[data-modal-back]");
            if (button) {
                // Show Back only on the currently active modal.
                button.classList.toggle("hidden", id !== currentModalId);
            }
        });
    }

    function open(id) {
        const target = getModal(id);

        if (!target) {
            console.warn(`Modal not found: ${id}`);
            return;
        }

        if (currentModalId === id && isVisible(target)) {
            updateBackButtons();
            return;
        }

        // Recover a visible modal if another script opened it directly.
        if (!currentModalId) {
            const visibleId = MODAL_IDS.find(
                (otherId) => otherId !== id && isVisible(getModal(otherId))
            );

            if (visibleId) currentModalId = visibleId;
        }

        // Preserve the current modal in navigation history.
        if (currentModalId && currentModalId !== id) {
            const current = getModal(currentModalId);

            if (isVisible(current)) {
                history.push(currentModalId);
            }
        }

        // Only one registered modal should be visible at a time.
        MODAL_IDS.forEach((otherId) => {
            if (otherId !== id) hide(otherId);
        });

        show(id);
    }

    function back() {
        if (!currentModalId) {
            // Recover state if a modal was shown outside this manager.
            const visibleId = MODAL_IDS.find((id) =>
                isVisible(getModal(id))
            );

            if (!visibleId) return;

            currentModalId = visibleId;
        }

        const closingId = currentModalId;

// Allow the modal to clean up resources before it closes.
        beforeClose(closingId);

        hide(closingId);
        currentModalId = null;

        // Restore the most recent existing previous modal.
        while (history.length) {
            const previousId = history.pop();

            if (getModal(previousId)) {
                show(previousId);
                return;
            }
        }

        // No previous modal: close the current modal and return
        // to the dashboard.
        updateBackButtons();
    }

    function closeAll() {
        MODAL_IDS.forEach((id) => {
            if (isVisible(getModal(id))) {
                beforeClose(id);
            }

            hide(id);
        });

        history.length = 0;
        currentModalId = null;
        updateBackButtons();
    }

    function addBackButton(id) {
        const modal = getModal(id);
        if (!modal || modal.querySelector("[data-modal-back]")) return;

        const header = modal.querySelector(
            ".flex.items-center.justify-between"
        );

        if (!header) {
            console.warn(`Modal header not found for ${id}`);
            return;
        }

        const button = document.createElement("button");
        button.type = "button";
        button.dataset.modalBack = "";
        button.className =
            "hidden shrink-0 rounded-lg border border-gray-200 " +
            "px-3 py-2 text-sm font-medium text-gray-700 " +
            "transition hover:bg-gray-50";
        button.innerHTML = `
            <span aria-hidden="true">←</span>
            <span>Back</span>
        `;

        button.addEventListener("click", back);
        header.insertBefore(button, header.firstChild);
    }

    function init() {
        MODAL_IDS.forEach(addBackButton);

        // Escape uses the same history as the Back button.
        document.addEventListener(
            "keydown",
            (event) => {
                if (event.key !== "Escape") return;

                const hasOpenModal = MODAL_IDS.some((id) =>
                    isVisible(getModal(id))
                );

                if (!hasOpenModal) return;

                event.preventDefault();
                event.stopImmediatePropagation();
                back();
            },
            true
        );

        updateBackButtons();
    }

    window.ModalNavigation = {
        open,
        back,
        closeAll,
        updateBackButtons,
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
    } else {
        init();
    }
})();
