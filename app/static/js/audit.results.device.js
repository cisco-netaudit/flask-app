/**
 * JavaScript for handling device result table functionality, follow-up modal triggering,
 * and audit execution on individual devices.
 */

$(document).ready(function () {
    // Initialize the DataTable for device result table if it exists
    if ($("#device-resulttable").length) {
        $('#device-resulttable').DataTable({
            orderCellsTop: true,
            fixedHeader: true,
            paging: false,
            searching: false,
            info: false,
            autoWidth: true,
            columnDefs: [{ width: '300px', targets: 0 }],
        });
    }

    /**
    * Opens logs modal for a specific device when the Raw Logs button is clicked.
    */
    $(document).on("click", "#logsBtn", function () {
        const deviceId = $(this).data("id");
        if (deviceId) {
            $("#logsModalOverlay").css("display", "flex");
        }
    });

    $(document).on("click", "#closeLogsModalBtn", function () {
        $("#logsModalOverlay").css("display", "none");
    });

    /**
     * Opens the Follow-Up modal for a single device when the Follow-Up button is clicked.
     */
    $(document).on("click", "#followupBtn", function () {
        const deviceId = $(this).data("id");
        if (deviceId) {
            window.openFollowUpModal(deviceId);
        }
    });

    /**
     * Disables the Run Audit button, shows a loading indicator, and initiates
     * an audit process for a single device when the Run Audit button is clicked.
     */
    $(document).on("click", "#runAuditBtn", function () {
        const btn = $(this);
        const deviceId = btn.data("id");
        const view = btn.data("view");

        if (deviceId) {
            btn.prop("disabled", true).html('<i class="fas fa-spinner fa-spin"></i> Running...');
            window.runAudit([deviceId], view);
        }
    });
});