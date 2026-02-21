(function () {
  const app = window.SlipApp;

  const SAMPLE_TEXT = [
    "<f1r.P.1;H>      fachys.ykal.ar.ataiin.shol.shory.cthres.y.kor.sholdy",
    "<f1r.P.2;H>      kair.chear.cthy.ykor.shodaiin",
    "<f1r.P.3;H>      shol.qokedy.qokeedy.daiin",
    "<f1r.P.4;H>      ol.daiin.chol.chodaiin",
    "<f1r.P.5;H>      qokaiin.shol.chey.qokedy",
    "<f1r.P.6;H>      ykeedy.cheol.sheol.ol",
    "<f1r.P.7;H>      qotedy.qokeey.dal.chol",
    "<f1r.P.8;H>      chedy.shedy.qokedy.daiin",
    "<f1r.P.9;H>      shory.qokedy.cheor.dal",
  ].join("\n");

  function renderLineDiagnostics(report) {
    const container = document.getElementById("validator-lines");
    if (!report.diagnostics.length) {
      container.textContent = "No non-empty lines processed.";
      return;
    }

    const rows = report.diagnostics.map(function mapRow(line) {
      if (line.status === "error") {
        return `<div class='err'>Line ${line.lineNumber}: ${line.message}</div>`;
      }
      return `<div class='ok'>Line ${line.lineNumber}: ${line.lineType}, tokens=${line.tokenCount}, sanitized=${line.sanitizedCount}</div>`;
    });

    container.innerHTML = rows.join("");
  }

  function renderMachine(report) {
    const machineBox = document.getElementById("validator-machine");
    if (report.mode !== "lattice") {
      machineBox.className = "report-box muted";
      machineBox.textContent = "Machine metrics available only in lattice mode.";
      return;
    }

    if (!report.machine || !report.machine.ready) {
      machineBox.className = "report-box warn";
      machineBox.textContent = report.machine ? report.machine.message : "Machine metrics unavailable.";
      return;
    }

    machineBox.className = "report-box";
    machineBox.innerHTML = [
      `<div><strong>Total tokens:</strong> ${report.machine.total}</div>`,
      `<div><strong>Coverage:</strong> ${(report.machine.coverageRate * 100).toFixed(2)}%</div>`,
      `<div><strong>Strict admissibility:</strong> ${(report.machine.strictRate * 100).toFixed(2)}% (chance ${(report.machine.strictChance * 100).toFixed(2)}%)</div>`,
      `<div><strong>Drift admissibility:</strong> ${(report.machine.driftRate * 100).toFixed(2)}% (chance ${(report.machine.driftChance * 100).toFixed(2)}%)</div>`,
    ].join("");
  }

  function renderSummary(report) {
    const summary = document.getElementById("validator-summary");
    const normalized = document.getElementById("validator-normalized");

    const cls = report.valid ? "ok" : "err";
    const status = report.valid ? "VALID" : "INVALID";

    summary.className = "report-box";
    summary.innerHTML = [
      `<div class='${cls}'><strong>${status}</strong></div>`,
      `<div>Mode: ${report.mode}</div>`,
      `<div>Canonical policy: ${report.strictCanonical ? "strict (zandbergen_landini / lowercase)" : "relaxed"}</div>`,
      `<div>Processed lines: ${report.lineCount}</div>`,
      `<div>Errors: ${report.errorCount}</div>`,
      `<div>Sanitized tokens: ${report.totalSanitizedTokens}</div>`,
      report.warnings.length ? `<div class='warn'>Warnings: ${report.warnings.join(" | ")}</div>` : "",
    ].join("");

    if (report.mode === "syntax") {
      normalized.value = report.normalizedText;
    } else {
      normalized.value = report.sanitizedText;
    }

    renderLineDiagnostics(report);
    renderMachine(report);
  }

  app.runValidator = function runValidator() {
    const mode = document.getElementById("validator-mode").value;
    const input = document.getElementById("validator-input").value;
    const strictCanonical = document.getElementById("validator-strict-canonical").checked;

    app.state.validator.lastText = input;
    const report = app.validateIVTFF(input, mode, { strictCanonical: strictCanonical });
    app.state.validator.lastReport = report;
    renderSummary(report);
    app.log(`Validator run: mode=${mode}, strict=${strictCanonical}, valid=${report.valid}, lines=${report.lineCount}`);

    return report;
  };

  app.initValidatorView = function initValidatorView() {
    const validateBtn = document.getElementById("validator-validate");
    const sampleBtn = document.getElementById("validator-sample");
    const clearBtn = document.getElementById("validator-clear");

    validateBtn.addEventListener("click", function onValidate() {
      app.runValidator();
    });

    sampleBtn.addEventListener("click", function onSample() {
      document.getElementById("validator-input").value = SAMPLE_TEXT;
      app.log("Loaded validator sample text.");
      app.runValidator();
    });

    clearBtn.addEventListener("click", function onClear() {
      document.getElementById("validator-input").value = "";
      document.getElementById("validator-normalized").value = "";
      document.getElementById("validator-summary").className = "report-box muted";
      document.getElementById("validator-summary").textContent = "No validation run yet.";
      document.getElementById("validator-lines").textContent = "";
      document.getElementById("validator-machine").className = "report-box muted";
      document.getElementById("validator-machine").textContent = "Not evaluated yet.";
      app.state.validator.lastReport = null;
      app.log("Validator cleared.");
    });
  };
})();
