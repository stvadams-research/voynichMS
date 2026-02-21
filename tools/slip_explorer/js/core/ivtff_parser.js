(function () {
  const app = window.SlipApp;

  const fullLinePattern = /^<([^>]+)>\s*(.*)$/;
  const folioOnlyPattern = /^f\d+[rv]\d*$/;

  function splitTokens(content) {
    return content
      .split(/[.\s]+/)
      .map(function normalize(token) {
        return token.trim();
      })
      .filter(function nonEmpty(token) {
        return token.length > 0;
      });
  }

  app.parseIVTFFLine = function parseIVTFFLine(rawLine, lineNumber) {
    const line = String(rawLine || "").trim();
    if (!line) {
      return {
        lineNumber,
        rawLine,
        isBlank: true,
      };
    }

    if (line.startsWith("#")) {
      return {
        lineNumber,
        rawLine,
        isComment: true,
        commentType: "hash_comment",
      };
    }

    let location = null;
    let content = line;
    let lineType = "content_only";

    if (line.startsWith("<%>") || line.startsWith("<$>") || line.startsWith("<!")) {
      content = line;
      lineType = "content_only";
    } else if (line.startsWith("<")) {
      const match = fullLinePattern.exec(line);
      if (!match) {
        return {
          lineNumber,
          rawLine,
          error: "Malformed IVTFF location header.",
        };
      }
      location = match[1];
      content = match[2].trim();
      lineType = "full_line";

      // Match EVAParser behavior: page-level metadata lines are not token lines.
      if (folioOnlyPattern.test(location) && content.startsWith("<!")) {
        return {
          lineNumber,
          rawLine,
          isComment: true,
          commentType: "folio_metadata",
        };
      }
    }

    if (!content) {
      return {
        lineNumber,
        rawLine,
        lineType,
        location,
        error: "Missing line content after header.",
      };
    }

    const tokens = splitTokens(content);
    if (!tokens.length) {
      return {
        lineNumber,
        rawLine,
        lineType,
        location,
        error: "No tokens found in line content.",
      };
    }

    return {
      lineNumber,
      rawLine,
      lineType,
      location,
      content,
      tokens,
    };
  };

  app.parseIVTFFText = function parseIVTFFText(text) {
    const rows = String(text || "").split(/\r?\n/);
    return rows.map(function parseRow(rawLine, index) {
      return app.parseIVTFFLine(rawLine, index + 1);
    });
  };
})();
