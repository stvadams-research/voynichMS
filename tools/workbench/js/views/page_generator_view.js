(function () {
  const app = window.SlipApp;

  function buildActualText(folio, format) {
    if (!folio || !Array.isArray(folio.lines)) {
      return "";
    }
    if (format === "ivtff") {
      return folio.lines
        .map(function eachLine(line) {
          const location = String(line.location || "").trim();
          const content = String(line.content || "").trim();
          if (!location || !content) {
            return "";
          }
          return `<${location}>      ${content}`;
        })
        .filter(function keep(line) {
          return line.length > 0;
        })
        .join("\n");
    }
    return folio.lines
      .map(function eachLine(line) {
        return String(line.content || "").trim();
      })
      .filter(function keep(line) {
        return line.length > 0;
      })
      .join("\n");
  }

  function renderPageScan(folio) {
    const link = document.getElementById("page-scan-link");
    const img = document.getElementById("page-scan-thumb");
    const meta = document.getElementById("page-scan-meta");
    if (!link || !img || !meta) {
      return;
    }

    const thumb = folio && folio.scan_thumb ? folio.scan_thumb : "";
    const full = folio && folio.scan_full ? folio.scan_full : "";
    const scanLabel = folio && folio.scan_label ? folio.scan_label : "unmapped";

    if (!thumb && !full) {
      link.classList.add("disabled-link");
      link.removeAttribute("href");
      img.removeAttribute("src");
      img.style.display = "none";
      meta.textContent = "No mapped scan for this folio.";
      return;
    }

    img.style.display = "block";
    if (thumb) {
      img.setAttribute("src", thumb);
    } else if (full) {
      img.setAttribute("src", full);
    } else {
      img.removeAttribute("src");
    }

    link.classList.remove("disabled-link");
    link.setAttribute("href", "#");
    meta.textContent = full
      ? `Thumbnail from folios_1000. Click image to open popup with folios_2000 (${scanLabel}).`
      : `Click image to open popup with folios_1000 (${scanLabel}).`;

    img.onerror = function onThumbError() {
      img.removeAttribute("src");
      img.style.display = "none";
      meta.textContent = `Scan path unavailable on disk (${scanLabel}).`;
      link.classList.add("disabled-link");
      link.removeAttribute("href");
    };
  }

  function renderActualPreview(folioId, format) {
    const actualOutput = document.getElementById("page-actual-output");
    const folio = app.state.data.folioMap[folioId] || null;
    if (actualOutput) {
      actualOutput.value = buildActualText(folio, format);
    }
    renderPageScan(folio);
  }

  function bindPageScanLink() {
    const link = document.getElementById("page-scan-link");
    const folioInput = document.getElementById("page-folio-id");
    if (!link || !folioInput) {
      return;
    }

    if (typeof app.bindScanModalHandlers === "function") {
      app.bindScanModalHandlers();
    }

    link.addEventListener("click", function onPageScanClick(event) {
      event.preventDefault();
      if (link.classList.contains("disabled-link")) {
        return;
      }
      if (typeof app.openScanModal !== "function") {
        app.log("Page scan popup unavailable: scan modal handler not initialized.");
        return;
      }
      const folio = app.state.data.folioMap[folioInput.value.trim()] || null;
      app.openScanModal(folio);
    });
  }

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
      renderActualPreview(
        document.getElementById("page-folio-id").value.trim(),
        document.getElementById("page-format").value
      );
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
      diagRows.join(""),
    ].join("");

    output.value = result.text;
    renderActualPreview(result.folioId, result.format);
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
    const input = document.getElementById("page-folio-id");
    if (!input) {
      return;
    }
    input.innerHTML = "";
    const folioIds = Object.keys(app.state.data.folioMap || {})
      .sort(function sortFolios(a, b) {
        return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
      });

    folioIds.forEach(function addFolioId(folioId) {
      const option = document.createElement("option");
      option.value = folioId;
      option.textContent = folioId;
      input.appendChild(option);
    });

    if (!folioIds.length) {
      app.state.page.selectedFolio = null;
      renderActualPreview("", document.getElementById("page-format").value);
      return;
    }

    const current = String(input.value || "").trim();
    if (!current || !app.state.data.folioMap[current]) {
      input.value = folioIds[0];
      app.state.page.selectedFolio = folioIds[0];
    } else {
      app.state.page.selectedFolio = current;
    }
    renderActualPreview(input.value.trim(), document.getElementById("page-format").value);
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
    const formatInput = document.getElementById("page-format");

    populateFolioList();
    app.renderPageView();
    bindPageScanLink();

    folioInput.addEventListener("change", function onFolioChange() {
      app.state.page.selectedFolio = folioInput.value.trim();
      renderActualPreview(folioInput.value.trim(), formatInput.value);
    });

    formatInput.addEventListener("change", function onFormatChange() {
      renderActualPreview(folioInput.value.trim(), formatInput.value);
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
