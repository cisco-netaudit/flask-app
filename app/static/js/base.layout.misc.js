/**
 * This script handles the theme toggle feature for a web application. It allows users 
 * to switch between light and dark themes and persists the choice on the server.
 */

document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  const themeToggleIcon = themeToggle ? themeToggle.querySelector('i') : null;
  const $modal = $("#userAccountModal");

  if (themeToggle && themeToggleIcon) {
    let currentTheme = themeToggle.dataset.theme;
    setTheme(currentTheme);

    themeToggle.addEventListener("click", () => {
      currentTheme = currentTheme === "light" ? "dark" : "light";
      setTheme(currentTheme);

      // Update server with new theme selection
      fetch("/set_theme", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme: currentTheme })
      }).catch(err => console.error("Failed to update theme:", err));

      document.dispatchEvent(new CustomEvent("themeChanged", { detail: currentTheme }));
    });
  }

  // User Account Modal
  $('#userAccount').on('click', function() {
    $modal.css("display", "flex");
  });

  $('#closeUserAccountModalBtn').on('click', function() {
    $modal.fadeOut(150);
  });

  $(document).on("click", function (e) {
    if ($modal.is(":visible") && $(e.target).is("#userAccountModal")) {
      $modal.fadeOut(150);
    }
  });

  // Sidebar navigation
  $(".user-account-sidebar-menu li").on("click", function () {
      $(".user-account-sidebar-menu li").removeClass("active");
      $(this).addClass("active")
      // Switch active content section
      const section = $(this).data("section");
      const title = $(this).data("title") || $(this).find(".menu-text").text();

      // Update header title
      $("#userAccountSectionTitle").text(title);

      // Switch visible section
      $(".user-account-main-section").removeClass("active");
      $("#section-" + section).addClass("active");
  });

  // Toggles the visibility of a password field linked to the clicked toggle button.
    $(document).off('click', '.toggle-password');

    // Delegate click event to document (works for dynamically added elements)
    $(document).on('click', '.toggle-password', function (e) {

        const $btn = $(this);
        const targetSelector = $btn.data('target');
        const $target = $(targetSelector);

        if ($target.length === 0) return; // Safety check

        // Toggle input type
        const isPassword = $target.attr('type') === 'password';
        $target.attr('type', isPassword ? 'text' : 'password');

        // Toggle icon
        $btn.find('i').toggleClass('fa-eye fa-eye-slash');
    });

  // Profile Save Operation
  $("#general-form").on("submit", function (e) {
      e.preventDefault()
      $.ajax({
          url: "/update_profile",
          method: "POST",
          data: $(this).serialize(),
          success: function (response) {
              $("#userAccountModal").fadeOut(150)
              location.reload()
          },
          error: function () {
              alert("Error updating profile. Please try again.");
          },
      });
  });

  $(".user-account-sidebar-menu li[data-section='reports']").on("click", function () {
    loadReportsTable();
  });

  function loadReportsTable() {
    if ($.fn.DataTable.isDataTable("#reportsTable")) {
      $("#reportsTable").DataTable().destroy();
    }

    $("#reportsTable").DataTable({
      ajax: {
        url: "/reports",
        dataSrc: ""
      },
      columns: [
        { data: "filename" },
        { data: "created" },
        {
          data: "filename",
          render: function (data, type, row) {
            return `
              <button class="btn-download" data-filename="${data}" title="Download">
                <i class="fa fa-download"></i>
              </button>
              <button class="btn-delete" data-filename="${data}" title="Delete">
                <i class="fa fa-trash"></i>
              </button>
            `;
          },
          orderable: false,
          searchable: false
        }
      ],
      order: [[1, "desc"]],
      responsive: true,
      scrollY: "60vh",
      scrollCollapse: true,
      paging: false,
      searching: false,
      info: false,
      language: {
        emptyTable: "No reports available"
      }
    });
  }

  // Handle download button click
  $(document).on("click", ".btn-download", function () {
    const filename = $(this).data("filename");
    window.location.href = `/reports/download/${encodeURIComponent(filename)}`;
  });

  // Handle delete button click
  $(document).on("click", ".btn-delete", function () {
    const filename = $(this).data("filename");

    fetch(`/reports/delete/${encodeURIComponent(filename)}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          loadReportsTable();
        } else {
          alert("Error: " + data.message);
        }
      })
      .catch(err => {
        console.error("Delete failed:", err);
        alert("Delete failed. Please check logs.");
      });
  });
});

/**
 * Sets the theme of the application by updating the stylesheet and icon.
 *
 * @param {string} theme - The current theme, either 'light' or 'dark'.
 */
function setTheme(theme) {
  const themeStylesheet = document.getElementById("theme-stylesheet");
  const themeToggle = document.getElementById("theme-toggle");

  if (theme === "light") {
    themeStylesheet.href = "/static/css/light.css";
    themeToggle.querySelector('i').classList.replace('fa-moon', 'fa-sun');
  } else {
    themeStylesheet.href = "/static/css/dark.css";
    themeToggle.querySelector('i').classList.replace('fa-sun', 'fa-moon');
  }
}