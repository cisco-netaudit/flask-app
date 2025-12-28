/**
 * Handles the functionality of a collapsible sidebar with submenu states.
 * - Restores the sidebar's collapsed/expanded state upon page reload.
 * - Restores the last open submenu state.
 * - Provides toggle functionality for sidebar and submenus.
 */

document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const toggleBtn = document.getElementById("toggleSidebar");

  // Restore the sidebar's collapsed state from localStorage
  if (localStorage.getItem("sidebar_collapsed") === "true") {
    sidebar.classList.add("collapsed");
    collapseAllSubmenus();
  }

  // Restore the open submenu state from localStorage
  const openTitle = localStorage.getItem("submenu_open");
  document.querySelectorAll(".submenu").forEach((submenuDiv) => {
    const header = submenuDiv.querySelector(".submenu-text");
    const submenu = submenuDiv.querySelector(".submenu-items");
    const arrow = header.querySelector(".arrow");
    const title = header.innerText.trim();

    if (title === openTitle) {
      submenu.classList.add("open");
      submenuDiv.classList.add("open");
      arrow.textContent = "▼";
    } else {
      arrow.textContent = "▶";
    }
  });

  // Add click listener to toggle the sidebar's collapsed state
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
    localStorage.setItem("sidebar_collapsed", sidebar.classList.contains("collapsed"));

    if (sidebar.classList.contains("collapsed")) {
      localStorage.removeItem("submenu_open");
      collapseAllSubmenus();
    }
  });

  // Add click listeners to submenu headers to toggle their open/closed state
  const userButton = document.getElementById('userPopupBtn');
  const userMenu = document.getElementById('userPopupMenu');

  userButton.addEventListener('click', (e) => {
      e.stopPropagation();
      userMenu.style.display = userMenu.style.display === 'block' ? 'none' : 'block';
  });

  window.addEventListener('click', () => {
      userMenu.style.display = 'none';
  });

  userMenu.addEventListener('click', (e) => e.stopPropagation());

});

/**
 * Collapses all submenus by removing the 'open' class and resetting arrow indicators.
 */
function collapseAllSubmenus() {
  document.querySelectorAll(".submenu").forEach((submenu) => {
    submenu.classList.remove("open");
    submenu.querySelector(".submenu-items").classList.remove("open");
    submenu.querySelector(".arrow").textContent = "▶";
  });
}

/**
 * Toggles the open/closed state of a submenu.
 * If the sidebar is collapsed, it is expanded before opening the submenu.
 *
 * @param {HTMLElement} header - The header element of the submenu to toggle.
 */
function toggleSubmenu(header) {
  const sidebar = document.getElementById("sidebar");
  const parent = header.parentElement;
  const submenu = header.nextElementSibling;
  const arrow = header.querySelector(".arrow");
  const title = header.innerText.trim();

  // Expand the sidebar if it is collapsed
  if (sidebar.classList.contains("collapsed")) {
    sidebar.classList.remove("collapsed");
    localStorage.setItem("sidebar_collapsed", "false");
  }

  // Toggle submenu open/close
  if (submenu.classList.contains("open")) {
    submenu.classList.remove("open");
    parent.classList.remove("open");
    arrow.textContent = "▶";
    localStorage.removeItem("submenu_open");
  } else {
    submenu.classList.add("open");
    parent.classList.add("open");
    arrow.textContent = "▼";
    localStorage.setItem("submenu_open", title);
  }
}