/**
 * Handles the interactive table functionality for the results view,
 * including column filtering, bulk actions (follow-up and audit),
 * and UI interactions for checkboxes/buttons.
 */
$(document).ready(function () {
    // Ensure the script only executes when the results-viewtable is present
    if (!$("#results-viewtable").length) return;

    // Initialize the DataTable with custom configurations
    const table = $('#results-viewtable').DataTable({
        orderCellsTop: true,
        fixedHeader: true,
        paging: true,
        searching: true,
        info: true,
        autoWidth: true,
        columnDefs: [{ width: '30px', targets: 0 }],
        initComplete: function () {
            const api = this.api();

            // Adjust column header width dynamically
            api.columns().every(function () {
                const th = $(this.header());
                th.css('width', th.width() + 'px');
            });

            // Set up individual column filters
            $('#results-viewtable thead tr:eq(1) th input.col-filter').each(function () {
                const colIndex = $(this).data('col') + 1;
                $(this).on('keyup change clear', function () {
                    const currentSearch = table.column(colIndex).search();
                    if (currentSearch !== this.value) {
                        table.column(colIndex).search(this.value).draw();
                    }
                });
            });
        }
    });

    // Reference elements for bulk actions
    const followupBtn = $("#followupBtn")[0];
    const runAuditBtn = $("#runAuditBtn")[0];
    const selectAll = $("#selectAll")[0];

    /**
     * Toggles the visibility of action buttons based on row selection
     */
    function toggleActionBtns() {
        const checked = $(".row-check:checked").length;
        if (followupBtn) followupBtn.style.display = checked > 0 ? "inline-flex" : "none";
        if (runAuditBtn) runAuditBtn.style.display = checked > 0 ? "inline-flex" : "none";
    }

    // Attach change event to individual checkboxes to toggle action buttons
    $(document).on("change", ".row-check", toggleActionBtns);

    // Handle select-all functionality
    if (selectAll) {
        selectAll.addEventListener("change", () => {
            $(".row-check").prop('checked', selectAll.checked);
            toggleActionBtns();
        });
    }

    // Column filter input
    $('#colNameFilter').on('keyup change', function () {
        const filterText = $(this).val().toLowerCase();

        table.columns().every(function (index) {
            if (index < 4) {
                table.column(this).visible(true);
                return;
            }
            const headerText = $(this.header()).text().toLowerCase();
            table.column(this).visible(headerText.includes(filterText));
        });
    });

    // Bulk Follow-Up Action
    $('#followupBtn').on('click', function () {
        const selected = $(".row-check:checked").map(function () {
            return $(this).data('id');
        }).get();

        if (selected.length) {
            window.openFollowUpModal(selected);
        }
    });

    // Bulk Run Audit Action
    $('#runAuditBtn').on('click', function () {
        const selected = $(".row-check:checked").map(function () {
            return $(this).data('id');
        }).get();

        const view = $("#results-viewtable").data('id');

        if (selected.length) {
            window.runAudit(selected, view);
        }
    });
});