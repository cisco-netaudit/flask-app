/**
 * manage_checks.js
 * Handles the Checks management functionality: CodeMirror editor setup, Add/Edit modal operations,
 * file browsing, and form submission for saving and generating checks.
 */

$(document).ready(function () {
    // Global Configuration
    window.datasetName = "checks";

    // Initialize CodeMirror Editor for Check Code
    const themeToggle = document.getElementById("theme-toggle");
    const currentTheme = themeToggle.dataset.theme;
    const codeEditorTheme = currentTheme === "dark" ? "darcula" : "default";

    const codeEditor = CodeMirror.fromTextArea(document.getElementById('checkCode'), {
        mode: 'python',
        theme: codeEditorTheme,
        indentUnit: 4,
        tabSize: 4,
        lineNumbers: true,
    });
    codeEditor.setSize(null, "600px");

    // Update CodeMirror theme upon theme change
    document.addEventListener("themeChanged", (e) => {
        const theme = e.detail;
        codeEditor.setOption("theme", theme === "dark" ? "darcula" : "default");
        codeEditor.refresh();
    });

    // Export button
    const exportSeletecBtn = $("#exportSeletecBtn")[0];
    const selectAll = $("#selectAll")[0];

    function toggleExportBtn() {
        const checkedCount = $(".row-check:checked").length;
        exportSeletecBtn.style.display = checkedCount > 0 ? "inline-flex" : "none";
    }
    $(document).on("change", ".row-check", toggleExportBtn);

    selectAll.addEventListener("change", () => {
        $(".row-check").prop('checked', selectAll.checked);
        toggleExportBtn();
    });

    // Handle Export button action
    $('#exportSeletecBtn').on('click', function () {
        const selectedIds = Array.from(document.querySelectorAll(".row-check:checked"))
            .map(cb => cb.dataset.id);
        if (selectedIds.length) ExportChecks(selectedIds);
    });

    function ExportChecks(items) {
        $.ajax({
            url: '/data/export_checks',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ checks: items }),
            xhrFields: {
                responseType: 'blob'
            },
            success: function (data, status, xhr) {
                const blob = new Blob([data], { type: 'application/zip' });
                const downloadUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = 'exported_checks.zip';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(downloadUrl);
            },
            error: function (err) {
                alert("Export failed: " + (err.responseJSON?.error || "Unknown error"));
            }
        });
    }

    /**
     * Opens the modal dialog with the given title.
     * @param {string} title - The modal title to display.
     */
    function openModal(title) {
        $('#modalTitle').text(title);
        $('#modalOverlay').css('display', 'flex');
        codeEditor.refresh();
        resetTestDock();
    }

    /**
     * Closes the currently open modal dialog.
     */
    function closeModal() {
        $('#modalOverlay').css('display', 'none');
    }

    // Event handler to open "Add Check" modal
    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        $('#checkFilename').val('').prop('disabled', false);
        codeEditor.setValue('');
        openModal('Add Check');
    });

    // Event handlers to close modal dialog
    $('#cancelModalBtn, #closeModalBtn').on('click', closeModal);

    /**
     * Triggers file browsing and loads the selected file's content into CodeMirror.
     */
    $('#browseFileBtn').on('click', function () {
        const fileInput = $('<input type="file" accept=".py">');

        fileInput.on('change', function (e) {
            const file = e.target.files[0];
            if (!file) return;

            $('#checkFilename').val(file.name);
            const reader = new FileReader();
            reader.onload = (ev) => codeEditor.setValue(ev.target.result);
            reader.readAsText(file);
        });

        fileInput.trigger('click');
    });

    // Fetch and Edit Check Code
    let checksData = null;

    /**
     * Fetches the code for a given filename.
     * @param {string} filename - The filename of the check.
     * @returns {Promise<string|null>} - Resolves to the check code or null if not found.
     */
    function getCheckCode(filename) {
        if (checksData) {
            return Promise.resolve(checksData[filename]?.code || null);
        }

        return $.getJSON('/data/store/get/checks').then(data => {
            checksData = data;
            return data[filename]?.code || null;
        });
    }

    // Event handler to open the "Edit Check" modal
    $(document).on('click', '.edit-btn', function () {
        const row = $(this).closest('tr');
        const key = row.find('td:eq(1)').text().trim();

        $('#modalForm')[0].reset();
        $('#checkFilename').val(key).prop('disabled', true);

        getCheckCode(key).then(code => {
            if (code) {
                codeEditor.setValue(code);
                openModal('Edit Check');
            } else {
                alert("Code not found for this check");
            }
        });
    });

    // Save Check Functionality
    $('#saveBtn').on('click', function () {
        const filename = $('#checkFilename').val().trim();
        const code = codeEditor.getValue();

        $.ajax({
            url: '/data/store/save/' + window.datasetName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ key: filename, data: code }),
            success: function () {
                if (!testDock.classList.contains('open')) {
                    closeModal();
                    location.reload();
                }
                else {
                    resetTestDock();
                }
            },
            error: function (err) {
                alert("Save failed: " + (err.responseJSON?.error || "Unknown error"));
            }
        });
    });

    // Generate Check Modal Handlers
    /**
     * Opens the "Generate Check" modal.
     */
    function openGcModal() {
        $('#gcModalOverlay').css('display', 'flex');
    }

    /**
     * Closes the "Generate Check" modal.
     */
    function closeGcModal() {
        $('#gcModalOverlay').css('display', 'none');
    }

    // Event handler to open the "Generate Check" modal
    $('#openGcModalBtn').on('click', function () {
        const gcForm = $('#gcForm');
        if (gcForm.length) gcForm[0].reset();
        openGcModal();
    });

    // Event handlers to close "Generate Check" modal
    $('#cancelGcModalBtn, #closeGcModalBtn').on('click', closeGcModal);

    // Submit "Generate Check" form
    $('#saveGcBtn').on('click', function () {
        const description = $('#gcDescription').val().trim();
        const sampleOutput = $('#gcSampleOutput').val().trim();

        if (!description) {
            alert("Description is required.");
            return;
        }

        $('#gcModal').prop("disabled", true).text("Generating...");

        $.ajax({
            url: '/data/generate_check',
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ description, sampleOutput }),
            success: function (res) {
                codeEditor.setValue(res.code);
                $('#modalOverlay').css('display', 'flex');
                closeGcModal();
            },
            error: function (err) {
                alert("Generation failed: " + (err.responseJSON?.error || "Unknown error"));
            },
            complete: function () {
                $('#openGcModalBtn').prop("disabled", false);
            }
        });
    });

    // -------------------- Test Dock --------------------
    const testDock = document.getElementById('test-dock');
    const toggleBtn = document.getElementById('test-dock-toggle');
    const statusBox = document.getElementById('testStatus');

    // Helper to show status messages
    function setTestStatus(message, type = "info") {
        if (!statusBox) return;
        statusBox.textContent = message;
        statusBox.className = `badge ${type}`;
    }

    // Open Test Dock
    const openDock = async () => {
        if (!testDock.dataset.loaded) {
            const code = codeEditor.getValue();
            const filename = $('#checkFilename').val().trim();
            if (!code) {
                alert("Paste or generate a check first.");
                return;
            }

            setTestStatus("🔄 Preparing test environment...", "debug");

            try {
                const res = await fetch("/check/prepare_test", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename, code })
                });
                const data = await res.json();

                if (data.error) {
                    setTestStatus("❌ " + data.error, "error");
                    alert(data.error);
                    return;
                }

                // Display command + results
                document.getElementById('reqCommand').textContent = data.requests.command || "";
                document.getElementById('testSampleOutput').value = "";

                initResults = {"status": 0, "observation": "No results yet.", "comments": ["Run the check to see results."]};
                renderTestResults(initResults);

                setTestStatus("✅ Check loaded successfully. Enter sample output and click 'Validate'.", "info");

                testDock.dataset.loaded = "true";
                testDock.dataset.sessionId = data.session_id;
            } catch (err) {
                setTestStatus("❌ Failed to load check: " + err.message, "error");
                alert("Error: " + err.message);
                return;
            }
        }

        testDock.classList.add('open');
        toggleBtn.innerHTML = '<i class="fas fa-angle-right"></i>Validator';
    };

    // ✅ Close Test Dock
    const closeDock = () => {
        testDock.classList.remove('open');
        toggleBtn.innerHTML = '<i class="fas fa-angle-left"></i>Validator';

        delete testDock.dataset.loaded;
        delete testDock.dataset.sessionId;
    };

    // ✅ Toggle click
    toggleBtn.addEventListener('click', () => {
        if (testDock.classList.contains('open')) closeDock();
        else openDock();
    });

    // -------------------- Run Handler --------------------
    document.getElementById('runHandlerBtn').addEventListener('click', async () => {
        const code = codeEditor.getValue();
        const sampleOutput = document.getElementById('testSampleOutput').value;

        setTestStatus("🧪 Running handler...", "debug");

        try {
            const res = await fetch("/check/run_handler", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code,
                    sample_output: sampleOutput,
                    session_id: testDock.dataset.sessionId
                })
            });
            const data = await res.json();

            if (data.error) {
                 setTestStatus("❌ " + data.error, "error");
                 alert("Error:\n" + data.error);
            } else {
                const requests = data.requests || {};

                // Update displayed command and results
                document.getElementById('reqCommand').textContent = requests.command || "";

                // Render results
                renderTestResults(data.results);

                // Clear sample output textarea
                document.getElementById('testSampleOutput').value = "";

                // Decide next action
                if (requests.command) {
                    setTestStatus(`➡️ Enter output for next command: "${requests.command}"`, "debug");
                } else {
                    setTestStatus("✅ Test complete !", "info");
                    const code = codeEditor.getValue();
                    const filename = $('#checkFilename').val().trim();
                    const res = await fetch("/check/prepare_test", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ filename, code })
                    });
                    const resetData  = await res.json();
                    testDock.dataset.sessionId = resetData .session_id;
                    const resetRequests = resetData.requests || {};
                    document.getElementById('reqCommand').textContent = resetRequests.command || "";
                }
            }
        } catch (err) {
            setTestStatus("❌ Failed: " + err.message, "error");
            alert("Failed: " + err.message);
        }
    });

    // ✅ Function to reset Test Dock
    function resetTestDock() {
        testDock.dataset.loaded = "";
        testDock.classList.remove('open');
        toggleBtn.innerHTML = '<i class="fas fa-angle-left"></i>Validator';

        document.getElementById('testSampleOutput').value = "";

        const box = document.getElementById('testResultsBox');
        if (box) {
            box.hidden = true;
            document.getElementById("testStatusLabel").textContent = "";
            document.getElementById("testObservation").textContent = "";
            document.getElementById("testComments").innerHTML = "";
        }
    }

    function renderTestResults(results) {
        const statusInfo = statusCodes[String(results.status)];
        const box = document.getElementById("testResultsBox");
        box.hidden = false;

        // ----- Status badge -----
        const badge = document.getElementById("testStatusBadge");
        const icon = document.getElementById("testStatusIcon");
        const label = document.getElementById("testStatusLabel");

        // Reset previous status-* classes
        badge.className = "badge";

        if (statusInfo) {
            badge.classList.add(
                `status-${statusInfo.label.toLowerCase().replace(/\s+/g, '')}`
            );
            badge.title = statusInfo.description || "";
            icon.className = `fas ${statusInfo.icon}`;
            label.textContent = statusInfo.label;
        } else {
            icon.className = "fas fa-question-circle";
            label.textContent = "Unknown";
            badge.title = "Unknown status";
        }

        // ----- Observation -----
        document.getElementById("testObservation").textContent =
            results.observation || "No observation";

        // ----- Comments -----
        const commentsEl = document.getElementById("testComments");
        commentsEl.innerHTML = "";

        if (results.comments && results.comments.length) {
            results.comments.forEach(comment => {
                const li = document.createElement("li");
                li.textContent = comment;
                commentsEl.appendChild(li);
            });
        } else {
            const li = document.createElement("li");
            li.innerHTML = "<em>No comments</em>";
            commentsEl.appendChild(li);
        }
    }

    // --------------------- Git Repo Management ---------------------

    // Helper: sanitize repo path so it can be used as a valid HTML id
    function safeId(path) {
        return path.replace(/[^\w\-]+/g, "_");
    }

    // Open Git Modal
    $("#openGitModalBtn").on("click", function () {
        loadGitRepos();
        $("#gitModalOverlay").css("display", "flex");
    });

    // Close Git Modal
    $("#closeGitModalBtn, #closeGitModalBtn2").on("click", function () {
        $("#gitModalOverlay").css("display", "none");
    });

    // Auto-fill local repo name when user types URL
    document.getElementById("gitUrlInput").addEventListener("input", function () {
        const url = this.value.trim();

        if (!url) {
            document.getElementById("localNameInput").value = "";
            return;
        }

        try {
            // Extract repo name from URL
            const parts = url.split("/");
            let name = parts[parts.length - 1];

            if (name.endsWith(".git")) {
                name = name.slice(0, -4);
            }

            // Set local repo name (only if user hasn’t manually edited it)
            const localInput = document.getElementById("localNameInput");

            // Auto-fill only if the user hasn’t modified the field manually
            if (!localInput.dataset.userEdited) {
                localInput.value = name;
            }
        } catch (e) {
            console.warn("Invalid URL");
        }
    });

    /**
     * Load Git Repositories into table
     */
    function loadGitRepos() {
        $.getJSON("/manage/checks/scan_repos", function (repos) {
            const body = $("#gitReposBody");
            body.empty();

            if (!repos.length) {
                body.append(`
                    <tr>
                        <td colspan="3" class="text-center text-muted">
                            No Git repositories found.
                        </td>
                    </tr>
                `);
                return;
            }

            repos.forEach(repo => {
                const safe = safeId(repo.local_path);

                const row = `
                    <tr>
                        <!-- Repo URL Column -->
                        <td>
                            <div style="display: flex; flex-direction: column; gap: 5px;">
                                <!-- Repo Name -->
                                <div style="font-size: 14px; font-weight: 500; margin-bottom: 5px; text-transform: uppercase;">
                                    ${repo.local_path.split(/[/\\]/).pop()}
                                </div>

                                <!-- Remote URL -->
                                <div style="display: flex; align-items: center; font-weight: 300; font-style: italic; gap: 5px;">
                                    <i class="fas fa-code-branch"></i>
                                    <a href="${repo.remote_url}" target="_blank" style="overflow-wrap: anywhere;">
                                        ${repo.remote_url}
                                    </a>
                                </div>

                                <!-- Local Path -->
                                <div style="display: flex; align-items: center; font-weight: 300; gap: 5px;">
                                    <i class="fas fa-folder"></i>
                                    <span>
                                        ~ ${repo.local_path.split(/[/\\]/).slice(3).join(' > ')}
                                    </span>
                                </div>
                            </div>
                        </td>

                        <!-- Status Column -->
                        <td>
                            <span id="status-${safe}">
                                Checking...
                            </span>
                        </td>

                        <!-- Actions Column -->
                        <td>
                            <button class="sync-repo-btn" data-path="${repo.local_path}">
                                <i class="fas fa-sync"></i> Sync
                            </button>
                            <button class="delete-repo-btn" data-path="${repo.local_path}">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </td>
                    </tr>
                `;

                body.append(row);

                // Auto-check update status
                checkRepoUpdateStatus(repo.local_path);
            });
        });
    }

    /**
     * Check if repo has update available
     */
    function checkRepoUpdateStatus(repoPath) {
        const id = safeId(repoPath);
        const badge = $(`#status-${id}`);

        badge.text("Checking...");

        $.ajax({
            url: "/manage/checks/check_repo_status",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ local_path: repoPath }),

            success: function (res) {
                if (res.update_available) {
                    badge.text("Update Available");
                } else {
                    badge.text("Up To Date");
                }
            },

            error: function () {
                badge.text("Error");
            }
        });
    }

    /**
     * Clone New Repo
     */
    $("#gitAddBtn").on("click", function () {
        const url = $("#gitUrlInput").val().trim();
        const localName = $("#localNameInput").val().trim();
        if (!url) {
            alert("Enter a valid Git repository URL.");
            return;
        }

        $("#gitAddBtn").prop("disabled", true).text("Cloning...");

        $.ajax({
            url: "/manage/checks/clone_repo",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ remote_url: url, local_repo_name: localName }),

            success: function () {
                alert("Repository cloned successfully.");
                $("#gitUrlInput").val("");
                loadGitRepos();
                location.reload();
            },

            error: function (err) {
                alert("Clone failed: " + (err.responseJSON?.error || "Unknown error"));
            },

            complete: function () {
                $("#gitAddBtn").prop("disabled", false)
                    .html(`<i class="fas fa-plus-circle me-2"></i>Clone`);
            }
        });
    });


    /**
     * Pull Repo
     */
    $(document).on("click", ".sync-repo-btn", function () {
        const path = $(this).data("path");
        const id = safeId(path);
        const badge = $(`#status-${id}`);

        badge.text("Syncing...");

        $.ajax({
            url: "/manage/checks/sync_repo",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ local_path: path }),

            success: function () {
                badge.text("Up To Date");
                location.reload();
            },

            error: function (err) {
                badge.text("Sync Failed");
                alert("Sync failed: " + (err.responseJSON?.error || "Unknown error"));
            },

            complete: function () {
                // After pull, check update again
                checkRepoUpdateStatus(path);
            }
        });
    });

    /**
     * Delete Repo
     */
    $(document).on("click", ".delete-repo-btn", function () {
        const local_path = $(this).data("path");

        if (!confirm("Delete this repository folder permanently?")) return;

        $.ajax({
            url: "/manage/checks/delete_repo",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ local_path }),

            success: function () {
                alert("Repository deleted.");
                loadGitRepos();
                location.reload();
            },

            error: function (err) {
                alert("Delete failed: " + (err.responseJSON?.error || "Unknown error"));
            }
        });
    });
});