(function () {
  const app = window.SlipApp;

  function gatherOptions() {
    return {
      folioId: document.getElementById("page-folio-id").value.trim(),
      scheduleMode: document.getElementById("page-schedule-mode").value,
      lineCountMode: document.getElementById("page-line-count-mode").value,
      seed: Number.parseInt(document.getElementById("page-seed").value, 10),
      minWords: Number.parseInt(document.getElementById("page-min-words").value, 10),
      maxWords: Number.parseInt(document.getElementById("page-max-words").value, 10),
      profile: document.getElementById("page-profile").value,
      canonicalFilter: document.getElementById("page-canonical-filter").checked,
      format: document.getElementById("page-format").value,
    };
  }

  function renderStatus(result) {
    const status = document.getElementById("page-status");
    const diagnostics = document.getElementById("page-diagnostics");
    const output = document.getElementById("page-output");

    if (!result.ok) {
      status.className = "report-box err";
      status.textContent = result.message;
      diagnostics.className = "report-box muted";
      diagnostics.textContent = "No diagnostics available.";
      output.value = "";
      return;
    }

    status.className = "report-box";
    status.innerHTML = [
      `<div><strong>Folio:</strong> ${result.folioId}</div>`,
      `<div><strong>Section:</strong> ${result.section}</div>`,
      `<div><strong>Hand:</strong> ${result.hand}</div>`,
      `<div><strong>Lines:</strong> ${result.lineCount} (${result.lineCountSource})</div>`,
      `<div><strong>Schedule mode:</strong> ${result.scheduleMode}</div>`,
      `<div><strong>Format:</strong> ${result.format}</div>`,
      `<div><strong>Avg words/line:</strong> ${result.avgWordsPerLine.toFixed(2)}</div>`,
      Array.isArray(result.warnings) && result.warnings.length
        ? `<div class='warn'><strong>Warnings:</strong> ${result.warnings.join(" | ")}</div>`
        : "",
    ].join("");

    const sourceRows = Object.keys(result.sourceCounts || {})
      .sort()
      .map(function mapSource(key) {
        return `${key}: ${result.sourceCounts[key]}`;
      });
    const diagRows = (result.lineDiagnostics || []).slice(0, 18).map(function lineDiag(row) {
      return `<div>Line ${row.lineIndex + 1}: marker=${row.marker || "n/a"}, offset=${row.offset}, source=${row.offsetSource}, words=${row.words}</div>`;
    });
    const hiddenCount = Math.max(0, (result.lineDiagnostics || []).length - diagRows.length);
    if (hiddenCount > 0) {
      diagRows.push(`<div class='muted'>... ${hiddenCount} additional lines hidden ...</div>`);
    }

    diagnostics.className = "report-box";
    diagnostics.innerHTML = [
      `<div><strong>Offset Source Counts:</strong> ${sourceRows.join(" | ") || "none"}</div>`,
      `<div><strong>Global Mode Offset:</strong> ${result.globalOffset}</div>`,
      "<hr>",
      diagRows.join(""),
    ].join("");

    output.value = result.text;
  }

  function generate() {
    const options = gatherOptions();
    const result = app.generatePageByFolio(options);
    app.state.page.lastResult = result;
    renderStatus(result);
    if (result.ok) {
      app.log(
        `Page generated: folio=${result.folioId}, lines=${result.lineCount}, line_source=${result.lineCountSource}, avg_words=${result.avgWordsPerLine.toFixed(2)}`
      );
    } else {
      app.log(`Page generation failed: ${result.message}`);
    }
    return result;
  }

  function populateFolioList() {
    const list = document.getElementById("page-folio-list");
    const input = document.getElementById("page-folio-id");
    if (!list || !input) {
      return;
    }
    list.innerHTML = "";
    const folios = app.state.data.folios || [];
    folios.forEach(function addFolio(entry) {
      const option = document.createElement("option");
      option.value = entry.folio;
      list.appendChild(option);
    });

    if (!input.value && folios.length) {
      input.value = folios[0].folio;
      app.state.page.selectedFolio = folios[0].folio;
    }
  }

  app.renderPageView = function renderPageView() {
    const availability = document.getElementById("page-availability");
    const hasSchedule = !!app.state.data.pageSchedule;
    const hasPriors = !!app.state.data.pagePriors;

    if (hasSchedule && hasPriors) {
      availability.className = "muted";
      availability.textContent = "Page schedule and priors loaded.";
    } else if (hasSchedule && !hasPriors) {
      availability.className = "warn";
      availability.textContent = "Priors missing: sampled line count mode will fallback to observed counts.";
    } else if (!hasSchedule && hasPriors) {
      availability.className = "warn";
      availability.textContent = "Schedule missing: offsets will fallback to global mode.";
    } else {
      availability.className = "warn";
      availability.textContent = "Phase 18 data unavailable: generator runs in fallback mode only.";
    }
  };

  app.initPageView = function initPageView() {
    const generateBtn = document.getElementById("page-generate");
    const generateValidateBtn = document.getElementById("page-generate-validate");
    const folioInput = document.getElementById("page-folio-id");

    populateFolioList();
    app.renderPageView();

    folioInput.addEventListener("change", function onFolioChange() {
      app.state.page.selectedFolio = folioInput.value.trim();
    });

    generateBtn.addEventListener("click", function onGenerate() {
      generate();
    });

    generateValidateBtn.addEventListener("click", function onGenerateValidate() {
      const result = generate();
      if (!result.ok) {
        return;
      }
      document.getElementById("validator-input").value = result.text;
      document.getElementById("validator-mode").value = "lattice";
      document.getElementById("validator-strict-canonical").checked = true;
      app.setRoute("validator");
      app.runValidator();
      app.log(`Page Generator -> Validator for ${result.folioId} (mode=lattice).`);
    });
  };
})();
