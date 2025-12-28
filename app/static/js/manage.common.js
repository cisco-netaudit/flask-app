/**
 * This script handles the initialization of a DataTable, row selection logic, and delete functionality,
 * including handling bulk and individual row deletion, as well as DOM updates for corresponding UI elements.
 */

$(document).ready(function () {
    // Initialize the DataTable with specified configuration and filters
    const table = $('#manage-datatable').DataTable({
        stateSave: true,
        orderCellsTop: true,
        fixedHeader: true,
        paging: true,
        searching: true,
        info: true,
        autoWidth: true,
        columnDefs: [{ width: '30px', targets: 0 }],
        initComplete: function () {
            const api = this.api();

            // Lock column widths to prevent layout shifts
            api.columns().every(function () {
                const th = $(this.header());
                th.css('width', th.width() + 'px');
            });

            // Bind filter inputs to their respective columns
            $('#manage-datatable thead tr:eq(1) th input.col-filter').each(function () {
                const colIndex = $(this).data('col') + 1;
                $(this).on('keyup change clear', function () {
                    if (table.column(colIndex).search() !== this.value) {
                        table.column(colIndex).search(this.value).draw();
                    }
                });
            });
        }
    });

    // Reference to bulk delete button and "select all" checkbox
    const deleteSelectedBtn = $("#deleteSelectedBtn")[0];
    const selectAll = $("#selectAll")[0];

    /**
     * Toggles the visibility of the bulk delete button based on the number of checked rows.
     */
    function toggleDeleteBtn() {
        const checkedCount = $(".row-check:checked").length;
        deleteSelectedBtn.style.display = checkedCount > 0 ? "inline-flex" : "none";
    }

    // Monitor changes to individual row checkboxes and adjust the bulk delete button
    $(document).on("change", ".row-check", toggleDeleteBtn);

    // Handle "select all" functionality, checking/unchecking all rows
    selectAll.addEventListener("change", () => {
        $(".row-check").prop('checked', selectAll.checked);
        toggleDeleteBtn();
    });

    // Manages the delete modal visibility and items to delete
    let itemsToDelete = [];

    /**
     * Opens the delete confirmation modal and sets the items to delete.
     * @param {Array} items - List of item IDs to delete.
     */
    function openDeleteModal(items) {
        itemsToDelete = items;
        $("#deleteConfirmModal").css("display", "flex");
    }

    /**
     * Closes the delete confirmation modal.
     */
    function closeDeleteModal() {
        $("#deleteConfirmModal").css("display", "none");
    }

    // Close modal buttons
    $("#cancelDeleteBtn, #closeDeleteModalBtn").on("click", closeDeleteModal);

    // Handle bulk delete button action
    $('#deleteSelectedBtn').on('click', function () {
        const selectedIds = Array.from(document.querySelectorAll(".row-check:checked"))
            .map(cb => cb.dataset.id);
        if (selectedIds.length) openDeleteModal(selectedIds);
    });

    // Handle individual row delete button action
    $(document).on("click", ".delete-btn", function () {
        const id = $(this).closest("tr").find(".row-check").data("id");
        openDeleteModal([id]);
    });

    /**
     * Confirms the deletion of the selected items via an AJAX request.
     */
    $('#confirmDeleteBtn').on('click', function () {
        if (!window.datasetName) {
            alert("Dataset name is not defined.");
            return;
        }
        if (itemsToDelete.length === 0) return;

        $.ajax({
            url: '/data/store/delete/' + window.datasetName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ keys: itemsToDelete }),
            success: function () {
                location.reload();
            },
            error: function () {
                alert("Delete operation failed.");
            }
        });
    });
});