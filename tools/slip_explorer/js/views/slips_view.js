(function () {
  const app = window.SlipApp;

  function renderTokenRow(containerId, tokens, highlightIndex, extraClass) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    tokens.forEach(function drawToken(token, idx) {
      const span = document.createElement("span");
      span.className = `token${idx === highlightIndex ? ` ${extraClass}` : ""}`;
      span.textContent = token;
      container.appendChild(span);
    });
  }

  function showSlipDetails(slip) {
    const empty = document.getElementById("slips-empty");
    const detail = document.getElementById("slips-detail");
    const meta = document.getElementById("slip-meta");

    empty.classList.add("hidden");
    detail.classList.remove("hidden");

    const tokenPos = Number.parseInt(slip.token_pos, 10);
    renderTokenRow(
      "slip-prev-line",
      Array.isArray(slip.previous_line) ? slip.previous_line : [],
      Number.isNaN(tokenPos) ? -1 : tokenPos - 1,
      "source"
    );
    renderTokenRow(
      "slip-curr-line",
      Array.isArray(slip.current_line) ? slip.current_line : [],
      Number.isNaN(tokenPos) ? -1 : tokenPos,
      "highlight"
    );

    meta.innerHTML = [
      `<strong>Line:</strong> ${slip.line_no}`,
      `<strong>Word:</strong> ${slip.word}`,
      `<strong>Type:</strong> ${slip.type || "unknown"}`,
    ].join("<br>");
  }

  function renderSlipList() {
    const status = document.getElementById("slips-status");
    const list = document.getElementById("slips-list");

    const slips = app.state.data.slips;
    if (!slips.length) {
      status.textContent = "No slip dataset found.";
      list.innerHTML = "<div class='item-card'>No slip items available.</div>";
      return;
    }

    status.textContent = `Loaded ${slips.length} slips (showing first 250).`;
    list.innerHTML = "";

    slips.slice(0, 250).forEach(function eachSlip(slip, idx) {
      const row = document.createElement("div");
      row.className = "item-card";
      row.innerHTML = `<strong>Line ${slip.line_no}</strong> - ${slip.word}`;
      row.addEventListener("click", function onSelect() {
        app.state.slips.selected = slip;
        list.querySelectorAll(".item-card").forEach(function clearActive(card) {
          card.classList.remove("active");
        });
        row.classList.add("active");
        showSlipDetails(slip);
      });

      if (idx === 0 && !app.state.slips.selected) {
        app.state.slips.selected = slip;
        row.classList.add("active");
        showSlipDetails(slip);
      }

      list.appendChild(row);
    });
  }

  app.initSlipsView = function initSlipsView() {
    renderSlipList();
  };
})();
