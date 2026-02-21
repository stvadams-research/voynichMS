(function () {
  const app = window.SlipApp;

  function gridReady() {
    return !!(app.state.data.grid && app.state.data.windowIds.length);
  }

  function getWindowSet(windowId) {
    return app.state.data.windowSets[String(windowId)] || new Set();
  }

  function modulo(n, m) {
    return ((n % m) + m) % m;
  }

  app.getWindowWords = function getWindowWords(windowId) {
    if (!gridReady()) {
      return [];
    }
    const key = String(windowId);
    return app.state.data.grid.window_contents[key] || app.state.data.grid.window_contents[windowId] || [];
  };

  app.latticeStep = function latticeStep(word) {
    if (!gridReady()) {
      return null;
    }
    const latticeMap = app.state.data.grid.lattice_map;
    const ids = app.state.data.windowIds;
    const numWindows = ids.length;
    const currentWindow = app.state.lattice.currentWindow;

    const nextWindowRaw = latticeMap[word];
    const nextWindow = typeof nextWindowRaw === "undefined"
      ? modulo(currentWindow + 1, numWindows)
      : Number.parseInt(nextWindowRaw, 10);

    app.state.lattice.output.push(word);
    app.state.lattice.currentWindow = Number.isNaN(nextWindow)
      ? modulo(currentWindow + 1, numWindows)
      : modulo(nextWindow, numWindows);

    return {
      word,
      currentWindow,
      nextWindow: app.state.lattice.currentWindow,
    };
  };

  app.resetLatticeState = function resetLatticeState(windowId) {
    const ids = app.state.data.windowIds;
    if (!ids.length) {
      app.state.lattice.currentWindow = 0;
    } else if (typeof windowId === "number" && Number.isFinite(windowId)) {
      app.state.lattice.currentWindow = modulo(windowId, ids.length);
    } else {
      app.state.lattice.currentWindow = ids[0];
    }
    app.state.lattice.output = [];
  };

  app.evaluateLatticeAdmissibility = function evaluateLatticeAdmissibility(lines) {
    if (!gridReady()) {
      return {
        ready: false,
        message: "Lattice data not loaded.",
      };
    }

    const latticeMap = app.state.data.grid.lattice_map;
    const ids = app.state.data.windowIds;
    const numWindows = ids.length;

    let strict = 0;
    let drift = 0;
    let total = 0;
    let covered = 0;
    let currentWindow = ids[0];

    lines.forEach(function eachLine(tokens) {
      tokens.forEach(function eachToken(word) {
        total += 1;

        if (Object.prototype.hasOwnProperty.call(latticeMap, word)) {
          covered += 1;
        }

        const strictSet = getWindowSet(currentWindow);
        let isStrict = strictSet.has(word);
        let isDrift = isStrict;

        if (!isDrift) {
          const left = modulo(currentWindow - 1, numWindows);
          const right = modulo(currentWindow + 1, numWindows);
          if (getWindowSet(left).has(word)) {
            isDrift = true;
            currentWindow = left;
          } else if (getWindowSet(right).has(word)) {
            isDrift = true;
            currentWindow = right;
          }
        }

        if (isStrict) {
          strict += 1;
          drift += 1;
          currentWindow = Object.prototype.hasOwnProperty.call(latticeMap, word)
            ? Number.parseInt(latticeMap[word], 10)
            : modulo(currentWindow + 1, numWindows);
        } else if (isDrift) {
          drift += 1;
          currentWindow = Object.prototype.hasOwnProperty.call(latticeMap, word)
            ? Number.parseInt(latticeMap[word], 10)
            : modulo(currentWindow + 1, numWindows);
        } else if (Object.prototype.hasOwnProperty.call(latticeMap, word)) {
          currentWindow = Number.parseInt(latticeMap[word], 10);
        }

        if (!Number.isFinite(currentWindow)) {
          currentWindow = ids[0];
        }
      });
    });

    const windowSizes = ids.map(function windowSize(id) {
      return app.getWindowWords(id).length;
    });
    const totalWindowWords = windowSizes.reduce(function sum(a, b) {
      return a + b;
    }, 0);
    const avgWindowSize = numWindows ? totalWindowWords / numWindows : 0;
    const vocabSize = Object.keys(latticeMap).length;
    const strictChance = vocabSize ? avgWindowSize / vocabSize : 0;
    const driftChance = Math.min(1, strictChance * 3);

    return {
      ready: true,
      total,
      covered,
      coverageRate: total ? covered / total : 0,
      strict,
      drift,
      strictRate: total ? strict / total : 0,
      driftRate: total ? drift / total : 0,
      strictChance,
      driftChance,
    };
  };
})();
