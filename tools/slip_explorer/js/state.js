(function () {
  const app = (window.SlipApp = window.SlipApp || {});

  app.state = {
    route: "slips",
    data: {
      slips: [],
      grid: null,
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
  };
})();
