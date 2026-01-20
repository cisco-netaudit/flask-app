/**
 * manage_sessions.js
 * Handles the Sessions management page, including modal interactions, 
 * password visibility toggle, and session save/update functionalities.
 */

$(document).ready(function () {

    // Set global dataset name for the sessions.
    window.datasetName = "sessions";

    /**
     * Opens the "Add Session" modal by resetting the form and enabling the session name field.
     */
    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        $('#modalTitle').text('Add Session');
        $('#sessionName').prop('disabled', false);
        $("#modalOverlay").css("display", "flex");
    });

    /**
     * Closes the modal via cancel or close button.
     */
    $('#cancelModalBtn, #closeModalBtn').on('click', function () {
        $("#modalOverlay").css("display", "none");
    });

    /**
     * Opens the "Edit Session" modal, populating fields with session details
     * fetched from the server based on the session key.
     */
    $(document).on('click', '.edit-btn', function () {
        const row = $(this).closest('tr');
        const key = row.find('td:eq(1)').text().trim();

        $.getJSON('/data/store/get/sessions', function (data) {
            const session = data[key];
            if (!session) return;

            $('#sessionName').val(key).prop('disabled', true);
            $('#sessionJumphostIp').val(session.jumphost_ip || '');
            $('#sessionJumphostUser').val(session.jumphost_username || '');
            $('#sessionJumphostPassword').val(session.jumphost_password || '');
            $('#sessionNetUser').val(session.network_username || '');
            $('#sessionNetPassword').val(session.network_password || '');

            $('#modalTitle').text('Edit Session');
            $("#modalOverlay").css("display", "flex");
        });
    });

    /**
     * Saves or updates a session based on the form input. Sends the data
     * to the server and reloads the page on success, or alerts the user on failure.
     */
    $('#modalForm').on('submit', function (e) {
        e.preventDefault();

        const $keyInput = $('#sessionName');
        const key = $keyInput.val().trim();

        if (!$keyInput.prop('disabled') && window.itemExists(key)) {
            $keyInput[0].setCustomValidity('Session already exists');
            $keyInput[0].reportValidity();
            return;
        } else {
            $keyInput[0].setCustomValidity('');
        }

        const data = {
            jumphost_ip: $('#sessionJumphostIp').val(),
            jumphost_username: $('#sessionJumphostUser').val(),
            jumphost_password: $('#sessionJumphostPassword').val(),
            network_username: $('#sessionNetUser').val(),
            network_password: $('#sessionNetPassword').val()
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