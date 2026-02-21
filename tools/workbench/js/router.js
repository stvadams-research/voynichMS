(function () {
  const app = window.SlipApp;

  app.initRouter = function initRouter() {
    const nav = document.getElementById("app-nav");
    if (!nav) {
      return;
    }

    nav.addEventListener("click", function onNavClick(event) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      if (!target.classList.contains("nav-btn")) {
        return;
      }
      const route = target.dataset.route;
      if (!route) {
        return;
      }
      app.setRoute(route);
    });
  };

  app.setRoute = function setRoute(route) {
    app.state.route = route;

    document.querySelectorAll(".nav-btn").forEach(function applyNavState(btn) {
      btn.classList.toggle("active", btn.dataset.route === route);
    });

    document.querySelectorAll(".view").forEach(function applyViewState(view) {
      view.classList.toggle("active", view.id === `view-${route}`);
    });

    if (typeof app.onRouteChanged === "function") {
      app.onRouteChanged(route);
    }

    app.log(`Route -> ${route}`);
  };
})();
