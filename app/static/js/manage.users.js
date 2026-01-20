/**
 * This file provides the frontend logic for managing modal actions, 
 * password toggle functionality, and form submissions for admin users.
 */

$(document).ready(function () {
    // Dataset name used for API requests
    window.datasetName = "users";

    /**
     * Opens the modal to add a new admin user.
     * Resets the modal form and sets appropriate defaults.
     */
    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        $('#modalTitle').text('Add Admin');
        $('#userName').prop('disabled', false);
        $("#modalOverlay").css("display", "flex");
    });

    /**
     * Closes the modal when the cancel or close buttons are clicked.
     */
    $('#cancelModalBtn, #closeModalBtn').on('click', function () {
        $("#modalOverlay").css("display", "none");
    });

    /**
     * Handles form submission for adding or updating an admin user.
     * Gathers user input and sends it to the server via AJAX request.
     */
    $('#modalForm').on('submit', function (e) {
        e.preventDefault();

        const $keyInput = $('#userName');
        const key = $keyInput.val().trim();

        if (!$keyInput.prop('disabled') && window.itemExists(key)) {
            $keyInput[0].setCustomValidity('User already exists');
            $keyInput[0].reportValidity();
            return;
        } else {
            $keyInput[0].setCustomValidity('');
        }

        const isNew = !$('#userName').prop('disabled');

        const selectedRole = $('input[name="userRole"]:checked').val() || 'admin';

        const data = {
            firstname: $('#userFirstname').val().trim(),
            lastname: $('#userLastname').val().trim(),
            password: $('#userPassword').val(),
            email: $('#userEmail').val(),
            role: selectedRole,
            last_login: null
        };

        if (isNew) {
            data.created_at = getLocalISOTime();
        }

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

/**
 * Returns the current local time in ISO 8601 format truncated to seconds.
 * Accounts for timezone offsets.
 * @returns {string} ISO 8601 formatted timestamp
 */
function getLocalISOTime() {
    const now = new Date();
    const tzOffset = now.getTimezoneOffset() * 60000;
    return new Date(now - tzOffset).toISOString().slice(0, 19);
}