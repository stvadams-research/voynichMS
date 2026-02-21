(function () {
  const app = window.SlipApp;

  function parseOptionalInt(raw) {
    if (raw === null || raw === undefined || raw === "") {
      return null;
    }
    const n = Number.parseInt(raw, 10);
    return Number.isNaN(n) ? null : n;
  }

  function gatherOptions() {
    return {
      seed: Number.parseInt(document.getElementById("folio-seed").value, 10),
      lineCount: Number.parseInt(document.getElementById("folio-lines").value, 10),
      minWords: Number.parseInt(document.getElementById("folio-min-words").value, 10),
      maxWords: Number.parseInt(document.getElementById("folio-max-words").value, 10),
      startWindow: parseOptionalInt(document.getElementById("folio-start-window").value),
      folioLabel: document.getElementById("folio-label").value.trim() || "f1000r",
      profile: document.getElementById("folio-profile").value,
      canonicalFilter: document.getElementById("folio-canonical-filter").checked,
      format: document.getElementById("folio-format").value,
    };
  }

  function renderGeneration(result) {
    const stats = document.getElementById("folio-stats");
    const output = document.getElementById("folio-output");

    if (!result.ok) {
      stats.className = "report-box err";
      stats.textContent = result.message;
      output.value = "";
      return;
    }

    stats.className = "report-box";
    const rows = [
      `<div><strong>Seed:</strong> ${result.seed}</div>`,
      `<div><strong>Lines:</strong> ${result.lineCount}</div>`,
      `<div><strong>Avg words/line:</strong> ${result.avgWordsPerLine.toFixed(2)}</div>`,
      `<div><strong>Format:</strong> ${result.format}</div>`,
      `<div><strong>Profile:</strong> ${result.profile}</div>`,
    ];
    if (Array.isArray(result.warnings) && result.warnings.length) {
      rows.push(`<div class='warn'><strong>Warnings:</strong> ${result.warnings.join(" | ")}</div>`);
    }
    stats.innerHTML = rows.join("");

    output.value = result.text;
  }

  function generate() {
    const result = app.generateSyntheticFolio(gatherOptions());
    renderGeneration(result);
    if (result.ok) {
      app.log(`Generated folio: lines=${result.lineCount}, avg_words=${result.avgWordsPerLine.toFixed(2)}`);
    } else {
      app.log(`Folio generation failed: ${result.message}`);
    }
    return result;
  }

  app.initFolioView = function initFolioView() {
    document.getElementById("folio-generate").addEventListener("click", function onGenerate() {
      generate();
    });

    document.getElementById("folio-generate-validate").addEventListener("click", function onGenerateValidate() {
      const result = generate();
      if (!result.ok) {
        return;
      }

      document.getElementById("validator-input").value = result.text;
      document.getElementById("validator-mode").value = "lattice";
      app.setRoute("validator");
      app.runValidator();
      app.log("Generated folio sent to validator (lattice mode).");
    });
  };
})();
