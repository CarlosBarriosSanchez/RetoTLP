document.addEventListener("DOMContentLoaded", function () {
  const api = FairBetAPI;
  const ui = FairBetUI;
  const alerts = document.getElementById("operador-alerts");
  const panel = document.getElementById("operador-panel");
  const denied = document.getElementById("operador-denied");

  if (!api.isLoggedIn()) {
    denied.classList.remove("hidden");
    denied.innerHTML =
      'Debes <a href="/cuenta/?next=/operador/">iniciar sesión</a> con usuario staff.';
    return;
  }

  init();

  async function init() {
    try {
      const perfil = await api.me();
      if (!perfil.es_staff) {
        denied.classList.remove("hidden");
        return;
      }
      panel.classList.remove("hidden");
      await cargarDashboard();
      await cargarAlertas();
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }

  document.getElementById("btn-verificar-audit").addEventListener("click", verificarAudit);
  document.getElementById("form-reporte").addEventListener("submit", function (e) {
    e.preventDefault();
    descargarCsv(
      document.getElementById("reporte-anio").value,
      document.getElementById("reporte-mes").value
    );
  });

  async function descargarCsv(anio, mes) {
    try {
      const resp = await fetch(api.reporteMinceturUrl(anio, mes), {
        headers: { Authorization: "Token " + api.getToken() },
      });
      if (!resp.ok) throw new Error("No se pudo generar el reporte.");
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "fairbet_mincetur_" + anio + "_" + mes + ".csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }

  async function cargarDashboard() {
    const data = await api.operadorDashboard();
    document.getElementById("metric-ggr").textContent = ui.formatSoles(data.ggr);
    document.getElementById("metric-resumen").innerHTML =
      li("Apuestas en periodo", data.volumen_apuestas) +
      li("Total apostado", ui.formatSoles(data.stakes_total)) +
      li("Total pagado", ui.formatSoles(data.payouts_total)) +
      li("Usuarios activos", data.usuarios_activos) +
      li("Alertas fraude pendientes", data.alertas_fraude_pendientes);

    const expEl = document.getElementById("exposure-list");
    if (!data.exposure_por_evento || !data.exposure_por_evento.length) {
      expEl.innerHTML = '<p class="form-hint">Sin exposición (no hay apuestas aceptadas).</p>';
      return;
    }
    expEl.innerHTML = data.exposure_por_evento
      .map(function (ev) {
        const filas = ev.selecciones
          .map(function (s) {
            return (
              "<tr><td>" +
              ui.escapeHtml(s.seleccion) +
              "</td><td>" +
              ui.formatSoles(s.exposure) +
              "</td></tr>"
            );
          })
          .join("");
        return (
          '<div class="exposure-block"><strong>' +
          ui.escapeHtml(ev.evento) +
          '</strong><table class="data-table"><tbody>' +
          filas +
          "</tbody></table></div>"
        );
      })
      .join("");
  }

  function li(label, value) {
    return "<li><span>" + label + "</span> <strong>" + value + "</strong></li>";
  }

  async function cargarAlertas() {
    const data = await api.alertasFraude();
    const ul = document.getElementById("alertas-list");
    if (!data.alertas || !data.alertas.length) {
      ul.innerHTML = '<li class="form-hint">Sin alertas pendientes.</li>';
      return;
    }
    ul.innerHTML = data.alertas
      .map(function (a) {
        return (
          "<li><strong>" +
          ui.escapeHtml(a.tipo) +
          "</strong> (" +
          a.severidad +
          ")<br><small>" +
          ui.escapeHtml(a.descripcion) +
          "</small></li>"
        );
      })
      .join("");
  }

  async function verificarAudit() {
    const el = document.getElementById("audit-status");
    try {
      const data = await api.verificarAuditoria();
      if (data.valida) {
        el.textContent =
          "Cadena válida — " + data.registros + " registros auditados.";
        el.className = "alert alert-success";
      } else {
        el.textContent =
          "Cadena inválida en #" + data.fallo_en_secuencia + ": " + data.motivo;
        el.className = "alert alert-error";
      }
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }
});
