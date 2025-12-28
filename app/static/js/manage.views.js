/**
 * Handles the modal functionality and interactions for managing views and checks.
 */
$(document).ready(function () {
    
    // Initialize variables
    window.datasetName = "views";
    let checksData = {};
    const $available = $('#availableChecks');
    const $selected = $('#selectedChecks');

    /**
     * Opens the modal with a given title.
     * @param {string} title - The title to display in the modal.
     */
    function openModal(title) {
        $('#modalTitle').text(title);
        $('#modalOverlay').css('display', 'flex');
    }

    /**
     * Closes the modal.
     */
    function closeModal() {
        $('#modalOverlay').css('display', 'none');
    }

    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        $available.empty();
        $selected.empty();
        $('#viewName').prop('disabled', false);

        // Fetch latest checks before opening the modal
        fetchChecks().then(() => openModal('Add View'));
    });

    $('#cancelModalBtn, #closeModalBtn').on('click', closeModal);

    // Dual Listbox: Move Options
    $('#moveRight').click(function () {
        $available.find('option:selected').appendTo($selected);
    });

    $('#moveLeft').click(function () {
        $selected.find('option:selected').appendTo($available);
    });

    /**
     * Fetches available checks from the server.
     * @returns {Promise} A promise that resolves when checks are fetched.
     */
    function fetchChecks() {
        return $.getJSON('/data/store/get/checks').then(function (data) {
            checksData = data;
            $available.empty();
            $.each(data, (filename, check) => {
                $available.append(`<option value="${filename}">${check.name}</option>`);
            });
        });
    }

    document.querySelectorAll('.icon-btn').forEach(button => {
        button.addEventListener('click', () => {
            const iconInput = document.getElementById('viewIcon');
            iconInput.value = button.dataset.icon;
        });
    });

    // Edit Existing View
    $(document).on('click', '.edit-btn', function () {
        const viewName = $(this).data('id');
        $('#modalForm')[0].reset();
        $('#viewName').val(viewName).prop('disabled', true);
        $available.empty();
        $selected.empty();

        fetchChecks().then(() => {
            $.getJSON('/data/store/get/views', function (data) {
                const view = data[viewName];
                if (!view) return;
                $('#viewIcon').val(view.icon || '');
                view.checks.forEach(function (chk) {
                    const checkMeta = checksData[chk];

                    if (checkMeta) {
                        // Correct label from metadata
                        $selected.append(`<option value="${chk}">${checkMeta.name}</option>`);

                        // Remove from available if present
                        $available.find(`option[value="${CSS.escape(chk)}"]`).remove();

                    } else {
                        // If metadata missing, fallback to basename (NOT full path)
                        const baseName = chk.split(/[/\\]/).pop();
                        $selected.append(`<option value="${chk}">${baseName}</option>`);
                    }
                });

                openModal('Edit View');
            });
        });
    });

    // Save: Add / Update View
    $('#saveBtn').on('click', function () {
        const key = $('#viewName').val();
        let icon = $('#viewIcon').val().trim();
        const checks = $selected.find('option').map(function (_, opt) {
            return $(opt).val();
        }).get();

        if (!icon) {
            icon = 'fa fa-table-list';
        }

        $.ajax({
            url: '/data/store/save/' + window.datasetName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ key: key, data: { icon: icon, checks: checks } }),
            success: function () {
                location.reload();
            },
            error: function (err) {
                alert("Save failed: " + (err.responseJSON?.error || "Unknown error"));
            }
        });
    });

});