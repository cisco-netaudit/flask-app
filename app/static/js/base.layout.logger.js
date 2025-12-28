/**
 * logger.js
 * Handles the logger dock UI, log fetching, level filtering, and state persistence.
 */

document.addEventListener("DOMContentLoaded", initLogger);

/**
 * Initializes the logger dock and its associated functionality.
 */
function initLogger() {
    const loggerOutput = document.querySelector('#logger-table tbody');
    const loggerToggle = document.getElementById("logger-toggle");
    const loggerDock = document.getElementById("logger-dock");
    const levelCheckboxes = document.querySelectorAll('.logger-filters .filter');

    if (!loggerOutput) return;

    restoreDockState();
    restoreSelectedLogLevels();
    setupDockToggle();
    setupLogLevelCheckboxes();
    startSSE();

    /**
     * Restores the dock visibility state from localStorage.
     */
    function restoreDockState() {
        const savedDockState = localStorage.getItem("loggerDockOpen");
        if (savedDockState === "true") {
            loggerDock.classList.add("open");
            loggerToggle.innerHTML = '<i class="fa fa-angle-down"></i>Logger';
        } else {
            loggerDock.classList.remove("open");
            loggerToggle.innerHTML = '<i class="fa fa-angle-up"></i>Logger';
        }
    }

    /**
     * Restores the selected log levels filter state from localStorage.
     */
    function restoreSelectedLogLevels() {
        const savedLevels = JSON.parse(localStorage.getItem("loggerSelectedLevels") || '[]');
        if (savedLevels.length) {
            levelCheckboxes.forEach(cb => {
                cb.checked = savedLevels.includes(cb.value);
            });
        }
    }


    /**
        * Starts a Server-Sent Events (SSE) connection to receive real-time log updates.
    */
    function startSSE() {
        const eventSource = new EventSource('/activity');
        eventSource.onmessage = function(event) {
            const log = JSON.parse(event.data);
            const selectedLevels = getSelectedLevels();
            if (selectedLevels.includes(log.levelname)) {
                renderLogRow(log);
                autoScrollToBottom();
            }
        };
    }

    /**
     * Retrieves the currently selected log levels.
     * @returns {Array} - An array of selected log levels.
     */
    function getSelectedLevels() {
        return Array.from(levelCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    }

    /**
     * Renders an individual log entry as a table row.
     * @param {Object} log - The log entry to render.
     */
    function renderLogRow(log) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="timestamp">${log.asctime}</td>
            <td>
                <span class="badge ${log.levelname.toLowerCase()}">
                    <i class="fa ${
                        log.levelname === 'ERROR' ? 'fa-exclamation-circle' :
                        log.levelname === 'WARNING' ? 'fa-exclamation-triangle' :
                        log.levelname === 'INFO' ? 'fa-info-circle' :
                        log.levelname === 'CRITICAL' ? 'fa-biohazard' :
                        log.levelname === 'DEBUG' ? 'fa-bug' : ''
                    }"></i> ${log.levelname}
                </span>
            </td>
            <td class="module">${log.module || ''}</td>
            <td class="message">${log.message}</td>
        `;
        loggerOutput.appendChild(row);
    }

    /**
     * Auto-scrolls the logger table to the bottom.
     */
    function autoScrollToBottom() {
        const wrapper = loggerDock.querySelector('.table-wrapper');
        wrapper.scrollTop = wrapper.scrollHeight;
    }

    /**
     * Sets up the event listener for toggling the dock visibility.
     */
    function setupDockToggle() {
        loggerToggle.addEventListener("click", () => {
            loggerDock.classList.toggle("open");
            const isOpen = loggerDock.classList.contains("open");
            localStorage.setItem("loggerDockOpen", isOpen);
            loggerToggle.innerHTML = isOpen
                ? '<i class="fa fa-angle-down"></i>Logger'
                : '<i class="fa fa-angle-up"></i>Logger';
        });
    }

    /**
     * Sets up event listeners for log level checkboxes.
     * Updates the selected log levels in localStorage and fetches logs on change.
     */
    function setupLogLevelCheckboxes() {
        levelCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                localStorage.setItem("loggerSelectedLevels", JSON.stringify(getSelectedLevels()));
                applyFilters();
            });
        });
    }


    /**
    * Apply filters to existing log rows based on selected log levels.
    */
    function applyFilters() {
        const selectedLevels = getSelectedLevels();
        const rows = loggerOutput.querySelectorAll('tr');
        rows.forEach(row => {
            const level = row.querySelector('.badge').textContent.trim();
            row.style.display = selectedLevels.includes(level) ? '' : 'none';
        });
    }
}