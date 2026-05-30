/**
 * Cliente API — módulo usuarios (Integrante 1).
 * Token en localStorage (demo educativa).
 */
(function (global) {
  const TOKEN_KEY = "fairbet_token";
  const USER_KEY = "fairbet_username";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token, username) {
    localStorage.setItem(TOKEN_KEY, token);
    if (username) localStorage.setItem(USER_KEY, username);
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function getUsername() {
    return localStorage.getItem(USER_KEY) || "";
  }

  function isLoggedIn() {
    return Boolean(getToken());
  }

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  async function request(method, path, body) {
    const headers = { Accept: "application/json" };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    const token = getToken();
    if (token) {
      headers.Authorization = "Token " + token;
    }
    if (method !== "GET" && method !== "HEAD") {
      const csrf = getCsrfToken();
      if (csrf) headers["X-CSRFToken"] = csrf;
    }

    const options = { method, headers, credentials: "same-origin" };
    if (body !== undefined) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(path, options);
    let data = null;
    const text = await response.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text };
      }
    }

    if (!response.ok) {
      const message = formatError(data, response.status);
      const err = new Error(message);
      err.status = response.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function formatError(data, status) {
    if (!data) return "Error " + status;
    if (typeof data === "string") return data;
    if (data.error) return data.error;
    if (data.detail) return data.detail;
    if (Array.isArray(data)) return data.join(", ");
    const parts = [];
    for (const [key, val] of Object.entries(data)) {
      if (Array.isArray(val)) parts.push(key + ": " + val.join(", "));
      else if (typeof val === "object") parts.push(key + ": " + JSON.stringify(val));
      else parts.push(key + ": " + val);
    }
    return parts.length ? parts.join(" | ") : "Error " + status;
  }

  const api = {
    getToken,
    setToken,
    clearSession,
    getUsername,
    isLoggedIn,
    request,
    get: (path) => request("GET", path),
    post: (path, body) => request("POST", path, body),

   register: (payload) => request("POST", "/api/users/register/", payload),
    login: (username, password) =>
      request("POST", "/api/users/login/", { username, password }),
    me: () => request("GET", "/api/users/me/"),
    verifyKyc: () => request("POST", "/api/users/verify-kyc/", {}),

    balance: () => request("GET", "/api/wallet/balance/"),
    deposit: (monto) => request("POST", "/api/wallet/deposit/", { monto }),
    withdraw: (monto) => request("POST", "/api/wallet/withdraw/", { monto }),
    transfer: (destino_username, monto) =>
      request("POST", "/api/wallet/transfer/", { destino_username, monto }),
    bonusWelcomeStatus: () => request("GET", "/api/wallet/bonus/welcome/"),
    bonusWelcomeClaim: () =>
      request("POST", "/api/wallet/bonus/welcome/", { aceptar_terminos: true }),

    selfExclude: (payload) => request("POST", "/api/users/self-exclude/", payload),
    updateDailyLimit: (limite) =>
      request("POST", "/api/users/limits/daily/", { limite_deposito_diario: limite }),
    updateLimits: (payload) => request("POST", "/api/users/limits/daily/", payload),

    events: () => request("GET", "/api/events/"),
    placeBet: (payload) => request("POST", "/api/bets/", payload),
    placeCombined: (payload) => request("POST", "/api/bets/combined/", payload),
    cashout: (apuestaId) => request("POST", "/api/bets/" + apuestaId + "/cashout/", {}),
    myBets: () => request("GET", "/api/bets/mine/"),

    operadorDashboard: () => request("GET", "/api/operador/dashboard/"),
    verificarAuditoria: () => request("GET", "/api/operador/auditoria/verificar/"),
    alertasFraude: () => request("GET", "/api/operador/alertas/"),
    reporteMinceturUrl: function (anio, mes) {
      return "/api/operador/reporte-mincetur/?anio=" + anio + "&mes=" + mes;
    },
  };

  global.FairBetAPI = api;
})(window);
