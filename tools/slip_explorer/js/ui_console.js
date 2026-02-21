(function () {
  const app = window.SlipApp;

  app.log = function log(message) {
    const container = document.getElementById("debug-console");
    if (!container) {
      return;
    }
    const row = document.createElement("div");
    row.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
  };

  app.clearLog = function clearLog() {
    const container = document.getElementById("debug-console");
    if (container) {
      container.innerHTML = "";
    }
  };
})();
