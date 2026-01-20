/**
 * manage_devices.js
 * Handles the functionality for the Devices management page, including modals, date selection,
 * and save/update actions.
 */

$(document).ready(function () {

    /**
     * Global configuration for the dataset name, used for AJAX save/delete endpoints.
     */
    window.datasetName = "devices";

    /**
     * Handles the opening of the 'Add Device' modal and sets default values.
     */
    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        setSelectedViews([]);
        $('#deviceHostnames').prop('disabled', false);
        $('#modalTitle').text('Add Device(s)');
        $('#modalOverlay').css('display', 'flex');
    });

    /**
     * Closes the modal when 'Cancel' or 'Close' buttons are clicked.
     */
    $('#cancelModalBtn, #closeModalBtn').on('click', function () {
        $('#modalOverlay').css('display', 'none');
    });

    /* Open / close dropdown */
    $('#viewDropdownToggle').on('click', function (e) {
        e.stopPropagation();
        $('#viewDropdownMenu').toggle();
    });

    /* Prevent dropdown from closing when clicking inside */
    $('#viewDropdownMenu').on('click', function (e) {
        e.stopPropagation();
    });

    /* Close when clicking outside */
    $(document).on('click', function () {
        $('#viewDropdownMenu').hide();
    });

    function setSelectedViews(views = []) {
        // Clear previous selection
        $('#viewDropdownMenu input[type="checkbox"]').prop('checked', false);

        // Select matching views
        views.forEach(view => {
            $('#viewDropdownMenu input[type="checkbox"][value="' + view + '"]')
                .prop('checked', true);
        });

        // Update visible text
        $('#selectedViewsText').text(
            views.length ? views.join(', ') : 'Select view(s)'
        );
    }

    /* Update selected text when checkbox changes */
    $('#viewDropdownMenu').on('change', 'input[type="checkbox"]', function () {
        const selectedViews = $('#viewDropdownMenu input:checked')
            .map(function () { return this.value; })
            .get();

        $('#selectedViewsText').text(
            selectedViews.length ? selectedViews.join(', ') : 'Select view(s)'
        );
    });

    /**
     * Handles the opening of the 'Edit Device' modal and populates the fields with
     * existing device data retrieved from the server.
     */
    $(document).on('click', '.edit-btn', function () {
        const row = $(this).closest('tr');
        const key = row.find('td:eq(1)').text().trim();

        $.getJSON('/data/store/get/devices', function (data) {
            const device = data[key];
            if (!device) return;

            $('#deviceHostnames').val(key).prop('disabled', true);
            setSelectedViews(device.view || []);
            $('#deviceSession').val(device.session || '');
            $('#modalTitle').text('Edit Device');
            $('#modalOverlay').css('display', 'flex');
        });
    });

    /**
     * Submits the form to add or update a device by sending the data to the server.
     */

    function anyDeviceExists(input) {
        const hostnames = input
            .split(',')
            .map(h => h.trim())
            .filter(Boolean);

        return hostnames.some(h => window.itemExists(h));
    }

    $('#modalForm').on('submit', function (e) {
        e.preventDefault();

        const $keyInput = $('#deviceHostnames');
        const key = $keyInput.val().trim();

        if (!$keyInput.prop('disabled') && anyDeviceExists(key)) {
            $keyInput[0].setCustomValidity('One or more devices already exist');
            $keyInput[0].reportValidity();
            return;
        } else {
            $keyInput[0].setCustomValidity('');
        }

        const data = {
            view: $('#viewDropdownMenu input:checked')
                .map(function () { return this.value; })
                .get(),
            session: $('#deviceSession').val(),
        };

        $.ajax({
            url: '/data/store/save/' + window.datasetName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ key: key, data: data }),
            success: () => location.reload(),
            error: err => alert("Save failed: " + (err.responseJSON?.error || "Unknown error"))
        });
    });

});