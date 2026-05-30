document.addEventListener("DOMContentLoaded", function () {
  const api = FairBetAPI;
  const ui = FairBetUI;
  const alerts = document.getElementById("cartera-alerts");

  if (!ui.requireAuth("/cartera/")) return;

  const saldoEl = document.getElementById("saldo-display");
  const bonusStatusEl = document.getElementById("bonus-status");
  const bonusBtn = document.getElementById("btn-bonus-claim");

  cargarSaldo();
  cargarBonus();

  bonusBtn.addEventListener("click", async function () {
    ui.clearAlert(alerts);
    try {
      const data = await api.bonusWelcomeClaim();
      ui.showAlert(
        alerts,
        data.mensaje +
          " Rollover pendiente: " +
          ui.formatSoles(data.rollover_pendiente) +
          ".",
        "success"
      );
      await cargarSaldo();
      await cargarBonus();
      ui.refreshHeaderSaldo();
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  });

  document.getElementById("form-retiro").addEventListener("submit", async function (e) {
    e.preventDefault();
    ui.clearAlert(alerts);
    const monto = document.getElementById("monto-retiro").value;
    try {
      const data = await api.withdraw(monto);
      ui.showAlert(
        alerts,
        data.mensaje + " Saldo: " + ui.formatSoles(data.saldo_fichas) + ".",
        "success"
      );
      saldoEl.textContent = ui.formatSoles(data.saldo_fichas);
      ui.refreshHeaderSaldo();
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  });

  document.getElementById("form-deposito").addEventListener("submit", async function (e) {
    e.preventDefault();
    ui.clearAlert(alerts);
    const monto = document.getElementById("monto-deposito").value;
    try {
      const data = await api.deposit(monto);
      ui.showAlert(
        alerts,
        data.mensaje +
          " Nuevo saldo: " +
          ui.formatSoles(data.saldo_fichas) +
          ". Ya puedes ir a Eventos.",
        "success"
      );
      saldoEl.textContent = ui.formatSoles(data.saldo_fichas);
      ui.refreshHeaderSaldo();
      document.getElementById("monto-deposito").value = "100.00";
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  });

  document.getElementById("form-transferencia").addEventListener("submit", async function (e) {
    e.preventDefault();
    ui.clearAlert(alerts);
    const destino = document.getElementById("transfer-destino").value.trim();
    const monto = document.getElementById("transfer-monto").value;
    try {
      const data = await api.transfer(destino, monto);
      ui.showAlert(
        alerts,
        data.mensaje + " Tu saldo: " + ui.formatSoles(data.saldo_fichas) + ".",
        "success"
      );
      saldoEl.textContent = ui.formatSoles(data.saldo_fichas);
      ui.refreshHeaderSaldo();
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  });

  async function cargarSaldo() {
    try {
      const data = await api.balance();
      saldoEl.textContent = ui.formatSoles(data.saldo_fichas);
    } catch (err) {
      ui.showAlert(alerts, err.message, "error");
    }
  }

  async function cargarBonus() {
    try {
      const data = await api.bonusWelcomeStatus();
      if (Number(data.monto || "0") <= 0) {
        bonusStatusEl.textContent =
          "Aún no tienes bono asignado. Puedes activarlo una sola vez.";
        bonusBtn.disabled = false;
        return;
      }
      bonusStatusEl.textContent =
        "Bono: " +
        ui.formatSoles(data.monto) +
        " | Rollover: " +
        ui.formatSoles(data.rollover_acumulado) +
        " / " +
        ui.formatSoles(data.rollover_objetivo) +
        " | Pendiente: " +
        ui.formatSoles(data.rollover_pendiente);
      bonusBtn.disabled = true;
    } catch (err) {
      bonusStatusEl.textContent = "No se pudo cargar el estado del bono.";
    }
  }
});
