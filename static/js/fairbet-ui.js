/**
 * Utilidades compartidas del frontend — Integrante 5.
 * Formateo, cabecera, menú móvil y saldo en chip.
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

  /** Muestra montos como soles peruanos ficticios (S/). */
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

  /** Evita inyectar HTML no deseado al pintar textos del API. */
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  /** Redirige a login si no hay token guardado. */
  function requireAuth(redirectTo) {
    if (!api.isLoggedIn()) {
      window.location.href =
        "/cuenta/?next=" + encodeURIComponent(redirectTo || window.location.pathname);
      return false;
    }
    return true;
  }

  /** Muestra u oculta botones según haya sesión. */
  function initHeader() {
    const logoutBtn = document.getElementById("btn-logout");
    const loginLink = document.getElementById("nav-login");
    const cuentaLink = document.getElementById("nav-cuenta");

    if (api.isLoggedIn()) {
      if (logoutBtn) logoutBtn.classList.remove("hidden");
      if (loginLink) loginLink.classList.add("hidden");
      if (cuentaLink) cuentaLink.classList.remove("hidden");
      refreshHeaderSaldo();
    } else {
      if (logoutBtn) logoutBtn.classList.add("hidden");
      if (loginLink) loginLink.classList.remove("hidden");
      if (cuentaLink) cuentaLink.classList.add("hidden");
      updateSaldoChip(null);
    }

    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () {
        api.clearSession();
        window.location.href = "/";
      });
    }
  }

  /** Marca el enlace activo según la URL actual. */
  function markActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll(".site-nav a").forEach(function (link) {
      const href = link.getAttribute("href");
      if (href === path || (href !== "/" && path.startsWith(href))) {
        link.classList.add("active");
      }
    });
  }

  /** Pinta el saldo en la cabecera (chip verde). */
  function updateSaldoChip(saldo) {
    const chip = document.getElementById("header-saldo");
    if (!chip) return;

    if (saldo === null || saldo === undefined) {
      chip.textContent = "";
      chip.classList.add("empty");
      return;
    }

    chip.textContent = formatSoles(saldo);
    chip.classList.remove("empty");
  }

  /**
   * Pide saldo al API y actualiza la cabecera.
   * Lo llaman eventos, apuestas y cartera tras una operación.
   */
  async function refreshHeaderSaldo() {
    if (!api.isLoggedIn()) {
      updateSaldoChip(null);
      return;
    }

    try {
      const data = await api.get("/api/wallet/balance/");
      updateSaldoChip(data.saldo_fichas);
    } catch {
      // Si falla (ej. sin perfil), ocultamos el chip sin romper la página
      updateSaldoChip(null);
    }
  }

  /** Abre/cierra el menú en pantallas pequeñas. */
  function initMobileNav() {
    const toggle = document.getElementById("nav-toggle");
    const nav = document.getElementById("site-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      const abierto = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", abierto ? "true" : "false");
    });

    // Cierra el menú al elegir una opción (mejor UX en móvil)
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
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
    refreshHeaderSaldo,
    updateSaldoChip,
    escapeHtml,
  };

  document.addEventListener("DOMContentLoaded", function () {
    initHeader();
    markActiveNav();
    initMobileNav();
  });
})(window);
