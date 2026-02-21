(function () {
  const app = window.SlipApp;

  function renderOutput() {
    const output = document.getElementById("lattice-output");
    output.textContent = app.state.lattice.output.join(" ");
  }

  function renderWords() {
    const grid = app.state.data.grid;
    const label = document.getElementById("lattice-window-label");
    const wordsBox = document.getElementById("window-words");

    if (!grid) {
      label.textContent = "-";
      wordsBox.innerHTML = "<div class='muted'>No lattice loaded.</div>";
      return;
    }

    const current = app.state.lattice.currentWindow;
    label.textContent = String(current);

    const words = app.getWindowWords(current);
    wordsBox.innerHTML = "";

    if (!words.length) {
      wordsBox.innerHTML = "<div class='muted'>Window has no words.</div>";
      return;
    }

    words.forEach(function eachWord(word) {
      const button = document.createElement("button");
      button.className = "engine-word";
      button.textContent = word;
      button.addEventListener("click", function onWordClick() {
        const result = app.latticeStep(word);
        if (result) {
          app.log(`Lattice step: ${result.word} (${result.currentWindow} -> ${result.nextWindow})`);
          renderWindowList();
          renderWords();
          renderOutput();
        }
      });
      wordsBox.appendChild(button);
    });
  }

  function renderWindowList() {
    const status = document.getElementById("lattice-status");
    const list = document.getElementById("window-list");
    const ids = app.state.data.windowIds;

    if (!ids.length) {
      status.textContent = "No lattice model loaded.";
      list.innerHTML = "<div class='item-card'>No windows available.</div>";
      return;
    }

    const vocab = Object.keys(app.state.data.grid.lattice_map).length;
    status.textContent = `Loaded ${ids.length} windows, vocab ${vocab}.`;
    list.innerHTML = "";

    ids.forEach(function eachWindow(id) {
      const words = app.getWindowWords(id);
      const row = document.createElement("div");
      row.className = "item-card" + (id === app.state.lattice.currentWindow ? " active" : "");
      row.textContent = `Window ${id} (${words.length})`;
      row.addEventListener("click", function onSelect() {
        app.state.lattice.currentWindow = id;
        renderWindowList();
        renderWords();
      });
      list.appendChild(row);
    });
  }

  function randomWindow() {
    const ids = app.state.data.windowIds;
    if (!ids.length) {
      return;
    }
    const randomId = ids[Math.floor(Math.random() * ids.length)];
    app.state.lattice.currentWindow = randomId;
    app.log(`Jumped to window ${randomId}`);
    renderWindowList();
    renderWords();
  }

  app.renderLatticeView = function renderLatticeView() {
    renderWindowList();
    renderWords();
    renderOutput();
  };

  app.initLatticeView = function initLatticeView() {
    const reset = document.getElementById("lattice-reset");
    const random = document.getElementById("lattice-random");

    reset.addEventListener("click", function onReset() {
      app.resetLatticeState();
      app.log("Lattice reset.");
      app.renderLatticeView();
    });

    random.addEventListener("click", function onRandom() {
      randomWindow();
    });

    app.renderLatticeView();
  };
})();
