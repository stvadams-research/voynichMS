(function () {
  const app = window.SlipApp;

  const canonicalLocationPattern = /^[a-z0-9]+\.[^>]+$/;

  function findUppercaseToken(entry) {
    for (let i = 0; i < entry.tokens.length; i += 1) {
      const token = entry.tokens[i];
      if (/[A-Z]/.test(token)) {
        return token;
      }
    }
    return null;
  }

  app.validateIVTFF = function validateIVTFF(text, mode, options) {
    const opts = options || {};
    const strictCanonical = opts.strictCanonical !== false;
    const parsed = app.parseIVTFFText(text);

    const errors = [];
    const diagnostics = [];
    const normalizedLines = [];
    const sanitizedLines = [];

    parsed.forEach(function inspect(entry) {
      if (entry.isBlank || entry.isComment) {
        return;
      }

      if (entry.error) {
        errors.push({
          lineNumber: entry.lineNumber,
          message: entry.error,
        });
        diagnostics.push({
          lineNumber: entry.lineNumber,
          status: "error",
          message: entry.error,
        });
        return;
      }

      if (strictCanonical && entry.lineType === "full_line" && !canonicalLocationPattern.test(entry.location || "")) {
        const msg = "Non-canonical IVTFF location header for EVAParser-compatible input.";
        errors.push({
          lineNumber: entry.lineNumber,
          message: msg,
        });
        diagnostics.push({
          lineNumber: entry.lineNumber,
          status: "error",
          message: msg,
        });
        return;
      }

      const uppercaseToken = strictCanonical ? findUppercaseToken(entry) : null;
      if (uppercaseToken) {
        const msg = `Uppercase token "${uppercaseToken}" is non-canonical for the ZL EVA lowercase pipeline.`;
        errors.push({
          lineNumber: entry.lineNumber,
          message: msg,
        });
        diagnostics.push({
          lineNumber: entry.lineNumber,
          status: "error",
          message: msg,
        });
        return;
      }

      const sanitized = entry.tokens
        .map(function sanitizeTokenLocal(token) {
          return app.sanitizeToken(token);
        })
        .filter(function nonEmpty(token) {
          return token.length > 0;
        });

      diagnostics.push({
        lineNumber: entry.lineNumber,
        status: "ok",
        lineType: entry.lineType,
        tokenCount: entry.tokens.length,
        sanitizedCount: sanitized.length,
        canonical: strictCanonical ? "strict" : "relaxed",
      });

      normalizedLines.push(entry.tokens.join("."));
      sanitizedLines.push(sanitized);
    });

    const allSanitizedTokens = sanitizedLines.reduce(function flatten(acc, tokens) {
      return acc.concat(tokens);
    }, []);

    const report = {
      mode,
      valid: errors.length === 0,
      lineCount: diagnostics.length,
      errorCount: errors.length,
      diagnostics,
      errors,
      normalizedText: normalizedLines.join("\n"),
      sanitizedText: sanitizedLines
        .map(function joinTokens(tokens) {
          return tokens.join(".");
        })
        .join("\n"),
      totalSanitizedTokens: allSanitizedTokens.length,
      machine: null,
      warnings: [],
      strictCanonical,
    };

    if ((mode === "sanitized" || mode === "lattice") && !allSanitizedTokens.length) {
      report.warnings.push("No sanitized tokens remained after cleanup.");
    }

    if (strictCanonical && report.valid) {
      const contentOnlyLines = diagnostics.filter(function onlyContent(diag) {
        return diag.status === "ok" && diag.lineType === "content_only";
      }).length;
      if (contentOnlyLines > 0) {
        report.warnings.push(
          `Processed ${contentOnlyLines} content-only lines. Canonical ingestion usually uses full IVTFF line headers.`
        );
      }
    }

    if (mode === "lattice" && report.valid) {
      const machine = app.evaluateLatticeAdmissibility(sanitizedLines);
      report.machine = machine;
      if (machine.ready && machine.coverageRate < 0.2) {
        report.warnings.push(
          "Low lattice coverage detected. This usually means transliteration/model mismatch (e.g., Currier vs ZL)."
        );
      }
    }

    return report;
  };
})();
