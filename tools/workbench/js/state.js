(function () {
  const app = (window.SlipApp = window.SlipApp || {});

  app.state = {
    route: "slips",
    data: {
      slips: [],
      grid: null,
      folios: [],
      folioMap: {},
      metadata: {},
      windowIds: [],
      windowSets: {},
    },
    slips: {
      selected: null,
    },
    lattice: {
      currentWindow: 0,
      output: [],
    },
    validator: {
      lastText: "",
      lastReport: null,
    },
    explorer: {
      selectedFolio: null,
      filterText: "",
    },
  };
})();
