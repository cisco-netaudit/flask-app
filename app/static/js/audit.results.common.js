/**
 * Handles device follow-up modal actions and audit run operations.
 */

$(document).ready(function () {
    const followUpModal = $("#modalOverlay");
    let followUpDevices = [];

    /**
     * Opens the follow-up modal and populates it based on selected devices.
     * @param {Array|string} devices - Device IDs to follow up.
     */
    function openFollowUpModal(devices) {
        followUpDevices = Array.isArray(devices) ? devices : [devices];

        if (followUpDevices.length === 1) {
            const deviceId = followUpDevices[0];
            const row = $(`.row-check[data-id="${deviceId}"]`).closest("tr");

            if (row.length) {
                const actionText = row.find("td:nth-child(4)").text().trim();
                const commentText = row.data("comments") || "";
                $("#userActionSelect").val(actionText);
                $("#userComment").val(commentText);
            } else {
                const actionText = $(".device-infotable tr:has(th:contains('Action Taken')) td").text().trim();
                const commentText = $(".device-infotable tr:has(th:contains('Comments')) td").text().trim();
                $("#userActionSelect").val(actionText);
                $("#userComment").val(commentText);
            }
        } else {
            $("#userActionSelect").val("");
            $("#userComment").val("");
        }

        followUpModal.css("display", "flex");
    }

    /**
     * Closes the follow-up modal and clears device-specific data.
     */
    function closeFollowUpModal() {
        followUpDevices = [];
        followUpModal.css("display", "none");
    }

    /**
     * Initiates the audit process for selected devices and view.
     * @param {Array} devices - Array of device identifiers.
     * @param {string} view - The current view context.
     */
    function runAudit(devices, view) {
        if (!devices.length) return;

        const runAuditBtn = $("#runAuditBtn");

        runAuditBtn.prop("disabled", true)
                   .html('<i class="fas fa-spinner fa-spin"></i> Running...');

        $.ajax({
            url: '/audit/results/run',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ devices, view }),
            success: () => location.reload(),
            error: () => alert("Audit run failed")
        });
    }

    // Expose functions to global scope
    window.openFollowUpModal = openFollowUpModal;
    window.closeFollowUpModal = closeFollowUpModal;
    window.runAudit = runAudit;

    // Modal button handlers
    $("#closeModalBtn, #cancelModalBtn").on("click", closeFollowUpModal);

    // Save Follow-Up
    $("#saveBtn").on("click", function () {
        const user_action = $("#userActionSelect").val();
        const user_comments = $("#userComment").val();

        if (!followUpDevices.length) return;

        $.ajax({
            url: '/data/results/followup',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ devices: followUpDevices, user_action, user_comments }),
            success: () => location.reload(),
            error: () => alert("Follow up save failed")
        });

        closeFollowUpModal();
    });
});