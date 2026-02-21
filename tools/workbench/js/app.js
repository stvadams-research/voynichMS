(function () {
  const app = window.SlipApp;

  app.onRouteChanged = function onRouteChanged(route) {
    if (route === "lattice") {
      app.renderLatticeView();
    } else if (route === "explorer") {
      app.renderExplorerView();
    } else if (route === "page" && typeof app.renderPageView === "function") {
      app.renderPageView();
    }
  };

  window.addEventListener("DOMContentLoaded", function onReady() {
    app.clearLog();
    app.log("Initializing Voynich Tool Workbench...");

    app.initRouter();
    app.loadData();

    app.initSlipsView();
    app.initLatticeView();
    app.initExplorerView();
    app.initValidatorView();
    app.initFolioView();
    app.initPageView();

    app.setRoute("slips");

    const metadata = app.state.data.metadata || {};
    if (metadata.generated_at) {
      app.log(`Bundle metadata: generated_at=${metadata.generated_at}`);
    }
    app.log("Ready.");
  });
})();
