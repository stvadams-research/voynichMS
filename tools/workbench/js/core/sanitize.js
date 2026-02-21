(function () {
  const app = window.SlipApp;

  const reInlineMeta = /<!.*?>/g;
  const reAngleTags = /<.*?>/g;
  const reAngleUnclosed = /<[!%$].*/g;
  const reBracketContent = /\[.*?\]/g;
  const reSymbols = /[{}*$<>]/g;
  const rePunct = /[,\.;]/g;

  app.sanitizeToken = function sanitizeToken(token) {
    let t = String(token || "");
    t = t.replace(reInlineMeta, "");
    t = t.replace(reAngleTags, "");
    t = t.replace(reAngleUnclosed, "");
    t = t.replace(reBracketContent, "");
    t = t.replace(reSymbols, "");
    t = t.replace(rePunct, "");
    return t.trim();
  };
})();
