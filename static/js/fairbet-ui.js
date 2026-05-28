/**
 * Utilidades de interfaz — pantalla cuenta (Integrante 1).
 */
(function (global) {
  const api = global.FairBetAPI;

  const STATUS_LABELS = {
    pendiente_verificacion: "Pendiente de verificación",
    verificado: "Verificado",
    bloqueado: "Bloqueado",
    autoexcluido: "Autoexcluido",
  };

  function labelStatus(code) {
    return STATUS_LABELS[code] || code;
  }

  function formatSoles(value) {
    const n = parseFloat(value);
    if (Number.isNaN(n)) return "S/ —";
    return (
      "S/ " +
      n.toLocaleString("es-PE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  function formatFichas(value) {
    return formatSoles(value);
  }

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString("es-PE", {
        dateStyle: "short",
        timeStyle: "short",
      });
    } catch {
      return iso;
    }
  }

  function showAlert(container, message, type) {
    if (!container) return;
    container.innerHTML =
      '<div class="alert alert-' +
      type +
      '" role="alert">' +
      escapeHtml(message) +
      "</div>";
  }

  function clearAlert(container) {
    if (container) container.innerHTML = "";
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function requireAuth(redirectTo) {
    if (!api.isLoggedIn()) {
      window.location.href =
        "/cuenta/?next=" + encodeURIComponent(redirectTo || window.location.pathname);
      return false;
    }
    return true;
  }

  function initHeader() {
    const logoutBtn = document.getElementById("btn-logout");
    const loginLink = document.getElementById("nav-login");
    const cuentaLink = document.getElementById("nav-cuenta");

    if (api.isLoggedIn()) {
      if (logoutBtn) logoutBtn.classList.remove("hidden");
      if (loginLink) loginLink.classList.add("hidden");
      if (cuentaLink) cuentaLink.classList.remove("hidden");
    } else {
      if (logoutBtn) logoutBtn.classList.add("hidden");
      if (loginLink) loginLink.classList.remove("hidden");
      if (cuentaLink) cuentaLink.classList.add("hidden");
    }

    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () {
        api.clearSession();
        window.location.href = "/";
      });
    }
  }

  function markActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll(".site-nav a").forEach(function (link) {
      const href = link.getAttribute("href");
      if (href === path || (href !== "/" && path.startsWith(href))) {
        link.classList.add("active");
      }
    });
  }

  global.FairBetUI = {
    labelStatus,
    formatSoles,
    formatFichas,
    formatDate,
    showAlert,
    clearAlert,
    requireAuth,
    initHeader,
    markActiveNav,
    escapeHtml,
  };

  document.addEventListener("DOMContentLoaded", function () {
    initHeader();
    markActiveNav();
  });
})(window);
