/**
 * This script contains the main functionality for managing and auditing 
 * devices. It includes features for filtering checks, running audits, 
 * viewing reports, exporting data, and toggling UI elements like passwords 
 * and tooltips.
 */

$(function () {

    /**
     * Filters the audit checks based on user input in the filter field.
     */
    $(document).on("input", ".check-filter", function () {
        const filter = this.value.toLowerCase();
        $(".check-item").each(function () {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(filter));
        });
    });

    /**
     * Initiates the audit process by collecting selected devices, checks, 
     * and session credentials, then calling the `runAudit` function.
     */
    $(document).on("click", "#runAuditBtn", function () {
        const devices = $("#device-list").val()
            .split("\n")
            .map(d => d.trim())
            .filter(Boolean);

        const checks = $(".checks-list input[type=checkbox]:checked")
            .map(function () {
                return $(this).val();
            })
            .get();

        const session = {
            jumphost_ip: $("#jumphostIp").val(),
            jumphost_username: $("#jumphostUsername").val(),
            jumphost_password: $("#jumphostPassword").val(),
            network_username: $("#networkUsername").val(),
            network_password: $("#networkPassword").val()
        };

        runAudit(devices, checks, session);
    });

    /**
     * Initializes the audit report table with specific configurations.
     */
    $("#auditReport").DataTable({
        orderCellsTop: true,
        fixedHeader: true,
        paging: false,
        searching: false,
        info: false,
        autoWidth: true,
    });

    /**
     * Fetches and displays the audit report in a modal window.
     */

    const checkList = {};
    $.getJSON("/data/store/get/checks", function (data) {
        Object.assign(checkList, data);
    });

    resultsLookup = {};

    // Render status badge
    function renderStatusBadge(statusCode, extraClass = "") {
        const status = statusCodes[String(statusCode)];
        const cssClass = status.label.toLowerCase().replace(/\s+/g, "");
        return `
            <span class="badge status-${cssClass} ${extraClass}" title="${status.description || ""}">
                <i class="fas ${status.icon}"></i>
                <span>${status.label}</span>
            </span>
        `;
    }

    // View Report
    $(document).on("click", "#viewReportBtn", function () {
        $.getJSON("/audit/quickaudit/report", function (results) {
            if (!results || $.isEmptyObject(results)) {
                alert("No report data available. Please run an audit first.");
                return;
            }

            const reportTableHeader = $("#auditReport thead tr");
            const reportTableBody = $("#auditReport tbody");
            reportTableHeader.empty();
            reportTableBody.empty();

            // Table headers
            let headerRow = "<th>Device</th><th>Login</th><th>Overall</th>";
            const firstDevice = Object.keys(results)[0];
            for (const checkName in results[firstDevice].checks) {
                headerRow += `<th>${checkList[checkName] ? checkList[checkName].name : checkName}</th>`;
            }
            reportTableHeader.append(headerRow);

            // Table rows
            for (const device in results) {
                const deviceResult = results[device];
                const displayName = deviceResult.hostname ?
                    `${device} (${deviceResult.hostname})` : device;

                let row = `<tr><td>${displayName}</td>`;

                // Login status
                const loginStatusBadge = deviceResult.login ?
                    `<span class="badge status-pass"><i class="fas fa-check-circle"></i> SUCCESS</span>` :
                    `<span class="badge status-fail"><i class="fas fa-times-circle"></i> FAILED</span>`;
                row += `<td class="text-center">${loginStatusBadge}</td>`;

                // Overall
                row += `<td class="text-center">${renderStatusBadge(deviceResult.status || 0)}</td>`;

                // Individual checks
                for (const checkName in deviceResult.checks) {
                    const checkResult = deviceResult.checks[checkName];
                    const cellId = device + "::" + checkName;

                    resultsLookup[cellId] = checkResult;

                    row += `
                        <td>
                            <span class="check-cell"
                                  data-cellid="${cellId}"
                                  data-status="${checkResult.status}">
                                ${renderStatusBadge(checkResult.status || 0, "check-badge")}
                            </span>
                        </td>
                    `;
                }
                row += "</tr>";
                reportTableBody.append(row);
            }
            $("#viewReportModal").css("display", "flex");
        });
    });

    /**
     * Closes the report modal when the close button is clicked.
     */
    $("#closeModalBtn").on("click", function () {
        $("#viewReportModal").css("display", "none");
    });

    /**
     * Displays detailed information about an audit check in a tooltip
     * when the user hovers over a check status cell.
     */

    let hideTimeout = null;

    $(document).on("mouseenter", ".check-cell", function () {
        clearTimeout(hideTimeout);

        const cellId = $(this).data("cellid");
        const check = resultsLookup[cellId] || {};

        const detailHtml = `
            <p><b>Observation:</b> ${check.observation || "Not Available"}</p>
            <p>${(check.comments && check.comments.length)
                ? check.comments.join("<br>")
                : "Not Available"}
            </p>
        `;

        const $tooltip = $("#checkDetailTooltip");
        $tooltip.html(detailHtml).show();

        const offset = $(this).offset();
        const tooltipWidth = $tooltip.outerWidth();
        const pageWidth = $(window).width();

        let left = offset.left;
        if (offset.left + tooltipWidth > pageWidth) {
            left = pageWidth - tooltipWidth - 10;
        }

        $tooltip.css({
            top: offset.top + $(this).outerHeight() + 5,
            left: left
        });
    });

    $(document).on("mouseleave", ".check-cell", function () {
        hideTimeout = setTimeout(() => {
            $("#checkDetailTooltip").hide();
        }, 200);
    });

    $("#checkDetailTooltip")
        .on("mouseenter", function () {
            clearTimeout(hideTimeout);
        })
        .on("mouseleave", function () {
            hideTimeout = setTimeout(() => {
                $(this).hide();
            }, 200);
        });


    /**
     * Exports the audit report data to an Excel file.
     */
    $(document).on("click", "#exportExcelBtn", function () {
        const exportData = {};

        $.getJSON("/audit/quickaudit/report", function (results) {
            for (const device in results) {
                const deviceResult = results[device];
                const row = {
                    displayName: deviceResult.hostname
                        ? `${device} (${deviceResult.hostname})`
                        : device,
                    login: deviceResult.login,
                    status: deviceResult.status || 0,
                    checks: {}
                };

                for (const check in deviceResult.checks) {
                    const checkResult = deviceResult.checks[check];
                    row.checks[check] = {
                        status: checkResult.status || 0,
                        observation: checkResult.observation,
                        comments: checkResult.comments,
                        checkName: checkList[check]
                            ? checkList[check].name
                            : check
                    };
                }
                exportData[device] = row;
            }

            // send to server
            fetch("/audit/quickaudit/export", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ data: exportData })
            })
            .then(resp =>
                resp.blob().then(blob => {
                    const disposition = resp.headers.get("Content-Disposition");
                    let filename = "Audit_Report.xlsx";

                    if (disposition && disposition.includes("filename=")) {
                        filename = disposition
                            .split("filename=")[1]
                            .replace(/"/g, "");
                    }

                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                })
            );
        });
    });

    /**
     * Executes the audit on the selected devices and checks.
     * 
     * @param {Array} devices - List of device names/addresses.
     * @param {Array} checks - List of checks to perform.
     * @param {Object} session - Session credentials for Jumphost and network.
     */
    function runAudit(devices, checks, session) {
        if (!devices.length || !checks.length) {
            alert("Please enter devices and select at least one check");
            return;
        }

        const runAuditBtn = $("#runAuditBtn");
        runAuditBtn.prop("disabled", true)
            .html('<i class="fas fa-spinner fa-spin"></i> Running...');

        $.ajax({
            url: "/audit/quickaudit/run",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ devices, checks, session }),
            success: (resp) => {
                if (resp.success) {
                    $("#viewReportBtn").trigger("click");
                } else {
                    alert(resp.message || "Audit run failed");
                }
            },
            error: () => {
                alert("Audit run failed");
            },
            complete: () => {
                runAuditBtn.prop("disabled", false)
                    .html('<i class="fas fa-bolt"></i> Run');
            }
        });
    }

    /**
     * Toggles all individual checkboxes when "Select All" is clicked.
     */
    $(document).on("change", "#selectAllChecks", function () {
        const checked = $(this).is(":checked");
        $(".checks-list .individual-check").prop("checked", checked);
    });

    /**
     * Updates the "Select All" checkbox state based on individual check states.
     */
    $(document).on("change", ".checks-list .individual-check", function () {
        const allChecked = $(".checks-list .individual-check").length ===
                           $(".checks-list .individual-check:checked").length;
        $("#selectAllChecks").prop("checked", allChecked);
    });

});