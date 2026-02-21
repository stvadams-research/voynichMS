(function () {
  const app = window.SlipApp;

  function toInt(value, fallback) {
    const n = Number.parseInt(value, 10);
    return Number.isNaN(n) ? fallback : n;
  }

  app.loadData = function loadData() {
    const slipsBlob = window.WORKBENCH_SLIPS || { slips: [] };
    const latticeBlob = window.WORKBENCH_LATTICE || {};
    const folioBlob = window.WORKBENCH_FOLIOS || { folios: [] };
    const grid = latticeBlob.results || latticeBlob;

    app.state.data.slips = Array.isArray(slipsBlob.slips) ? slipsBlob.slips : [];
    app.state.data.grid = grid && grid.lattice_map && grid.window_contents ? grid : null;
    app.state.data.folios = Array.isArray(folioBlob.folios) ? folioBlob.folios : [];
    const folioMap = {};
    app.state.data.folios.forEach(function eachFolio(entry) {
      if (entry && entry.folio) {
        folioMap[entry.folio] = entry;
      }
    });
    app.state.data.folioMap = folioMap;
    app.state.data.metadata = window.WORKBENCH_METADATA || {};

    if (app.state.data.grid) {
      const ids = Object.keys(app.state.data.grid.window_contents)
        .map(function mapIds(id) {
          return toInt(id, 0);
        })
        .sort(function sortIds(a, b) {
          return a - b;
        });
      app.state.data.windowIds = ids;

      const windowSets = {};
      ids.forEach(function buildWindowSet(id) {
        const words = app.state.data.grid.window_contents[id] || app.state.data.grid.window_contents[String(id)] || [];
        windowSets[String(id)] = new Set(words);
      });
      app.state.data.windowSets = windowSets;

      const firstWindow = ids.length ? ids[0] : 0;
      app.state.lattice.currentWindow = firstWindow;
    }

    const slipCount = app.state.data.slips.length;
    const vocab = app.state.data.grid ? Object.keys(app.state.data.grid.lattice_map).length : 0;
    const folioCount = app.state.data.folios.length;
    app.log(`Loaded data: slips=${slipCount}, lattice_vocab=${vocab}, folios=${folioCount}`);
  };
})();
