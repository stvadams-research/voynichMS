(function () {
  const app = window.SlipApp;
  let scanModalBound = false;

  function selectedFolio() {
    const selectedId = app.state.explorer.selectedFolio;
    if (!selectedId) {
      return null;
    }
    return app.state.data.folioMap[selectedId] || null;
  }

  function closeScanModal() {
    const modal = document.getElementById("explorer-scan-modal");
    const img = document.getElementById("explorer-scan-modal-img");
    if (!modal || !img) {
      return;
    }
    modal.classList.remove("active");
    modal.setAttribute("hidden", "hidden");
    img.removeAttribute("src");
    document.body.classList.remove("modal-open");
  }

  function openScanModal(folio) {
    const modal = document.getElementById("explorer-scan-modal");
    const img = document.getElementById("explorer-scan-modal-img");
    const meta = document.getElementById("explorer-scan-modal-meta");
    const closeBtn = document.getElementById("explorer-scan-close");

    if (!modal || !img || !meta || !folio) {
      return;
    }

    const full = folio.scan_full || "";
    const thumb = folio.scan_thumb || "";
    const source = full || thumb;
    const scanLabel = folio.scan_label || folio.folio || "unmapped";

    if (!source) {
      return;
    }

    img.setAttribute("src", source);
    meta.textContent = full
      ? `Showing folios_2000 image (${scanLabel}).`
      : `Showing folios_1000 image only (${scanLabel}).`;
    modal.removeAttribute("hidden");
    modal.classList.add("active");
    document.body.classList.add("modal-open");
    if (closeBtn) {
      closeBtn.focus();
    }
  }

  function bindScanModalHandlers() {
    if (scanModalBound) {
      return;
    }

    const link = document.getElementById("explorer-scan-link");
    const modal = document.getElementById("explorer-scan-modal");
    const closeBtn = document.getElementById("explorer-scan-close");

    if (!link || !modal || !closeBtn) {
      return;
    }

    link.addEventListener("click", function onScanClick(event) {
      event.preventDefault();
      if (link.classList.contains("disabled-link")) {
        return;
      }
      openScanModal(selectedFolio());
    });

    closeBtn.addEventListener("click", function onCloseClick() {
      closeScanModal();
    });

    modal.addEventListener("click", function onModalBackdrop(event) {
      if (event.target === modal) {
        closeScanModal();
      }
    });

    document.addEventListener("keydown", function onEscape(event) {
      if (event.key === "Escape") {
        closeScanModal();
      }
    });

    scanModalBound = true;
  }

  app.openScanModal = openScanModal;
  app.closeScanModal = closeScanModal;
  app.bindScanModalHandlers = bindScanModalHandlers;

  function renderScan(folio) {
    const link = document.getElementById("explorer-scan-link");
    const img = document.getElementById("explorer-scan-thumb");
    const meta = document.getElementById("explorer-scan-meta");

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

    if (full || thumb) {
      link.classList.remove("disabled-link");
      link.setAttribute("href", "#");
      meta.textContent = full
        ? `Thumbnail from folios_1000. Click image to open popup with folios_2000 (${scanLabel}).`
        : `Click image to open popup with folios_1000 (${scanLabel}).`;
    } else {
      link.classList.add("disabled-link");
      link.removeAttribute("href");
      meta.textContent = `Thumbnail only (${scanLabel}); no 2000px mapping found.`;
    }

    img.onerror = function onThumbError() {
      img.removeAttribute("src");
      img.style.display = "none";
      meta.textContent = `Scan path unavailable on disk (${scanLabel}).`;
      link.classList.add("disabled-link");
      link.removeAttribute("href");
    };
  }

  function buildContentOnlyText(folio) {
    const lines = Array.isArray(folio.lines) ? folio.lines : [];
    return lines
      .map(function eachLine(line) {
        return String(line.content || "").trim();
      })
      .filter(function keep(text) {
        return text.length > 0;
      })
      .join("\n");
  }

  function buildFullLineText(folio) {
    const lines = Array.isArray(folio.lines) ? folio.lines : [];
    return lines
      .map(function eachLine(line) {
        const location = String(line.location || "").trim();
        const content = String(line.content || "").trim();
        if (!location || !content) {
          return "";
        }
        return `<${location}>      ${content}`;
      })
      .filter(function keep(text) {
        return text.length > 0;
      })
      .join("\n");
  }

  function renderFolioDetail() {
    const title = document.getElementById("explorer-folio-title");
    const container = document.getElementById("explorer-line-list");
    const selectedId = app.state.explorer.selectedFolio;

    if (!selectedId || !app.state.data.folioMap[selectedId]) {
      title.textContent = "Select a folio";
      container.innerHTML = "<div class='explorer-line muted'>No folio selected.</div>";
      renderScan(null);
      return;
    }

    const folio = app.state.data.folioMap[selectedId];
    title.textContent = `${folio.folio} (${folio.line_count} lines)`;
    renderScan(folio);

    const rows = (folio.lines || []).map(function eachLine(line) {
      const location = line.location || "";
      const content = line.content || "";
      return `<div class='explorer-line'><span class='explorer-location'>&lt;${location}&gt;</span>${content}</div>`;
    });

    container.innerHTML = rows.join("") || "<div class='explorer-line muted'>No lines found for this folio.</div>";
  }

  function filteredFolios() {
    const filter = (app.state.explorer.filterText || "").toLowerCase().trim();
    const folios = app.state.data.folios;

    if (!filter) {
      return folios;
    }

    return folios.filter(function matchFolio(folio) {
      return String(folio.folio || "").toLowerCase().includes(filter);
    });
  }

  function renderFolioList() {
    const status = document.getElementById("explorer-status");
    const list = document.getElementById("explorer-folio-list");
    const folios = filteredFolios();

    if (!app.state.data.folios.length) {
      status.textContent = "No ZL3b folio data loaded.";
      list.innerHTML = "<div class='item-card'>No folios available.</div>";
      return;
    }

    status.textContent = `Loaded ${app.state.data.folios.length} folios (${folios.length} shown).`;
    list.innerHTML = "";

    folios.forEach(function eachFolio(folio) {
      const row = document.createElement("div");
      row.className = "item-card" + (folio.folio === app.state.explorer.selectedFolio ? " active" : "");
      row.innerHTML = `<strong>${folio.folio}</strong> (${folio.line_count})`;
      row.addEventListener("click", function onSelect() {
        app.state.explorer.selectedFolio = folio.folio;
        renderFolioList();
        renderFolioDetail();
      });
      list.appendChild(row);
    });

    if (!app.state.explorer.selectedFolio && folios.length) {
      app.state.explorer.selectedFolio = folios[0].folio;
      renderFolioList();
      renderFolioDetail();
    }
  }

  function sendToValidator(format) {
    const selectedId = app.state.explorer.selectedFolio;
    if (!selectedId || !app.state.data.folioMap[selectedId]) {
      app.log("Explorer: no selected folio to send.");
      return;
    }

    const folio = app.state.data.folioMap[selectedId];
    const text = format === "full" ? buildFullLineText(folio) : buildContentOnlyText(folio);
    document.getElementById("validator-input").value = text;
    document.getElementById("validator-mode").value = "syntax";
    document.getElementById("validator-strict-canonical").checked = true;
    app.setRoute("validator");
    app.runValidator();
    app.log(`Explorer -> Validator (${format}) for ${folio.folio}`);
  }

  app.renderExplorerView = function renderExplorerView() {
    renderFolioList();
    renderFolioDetail();
  };

  app.initExplorerView = function initExplorerView() {
    const filterInput = document.getElementById("explorer-filter");
    const sendContent = document.getElementById("explorer-send-content");
    const sendFull = document.getElementById("explorer-send-full");
    bindScanModalHandlers();

    filterInput.addEventListener("input", function onFilterChange() {
      app.state.explorer.filterText = filterInput.value;
      renderFolioList();
    });

    sendContent.addEventListener("click", function onSendContent() {
      sendToValidator("content");
    });

    sendFull.addEventListener("click", function onSendFull() {
      sendToValidator("full");
    });

    app.renderExplorerView();
  };
})();
