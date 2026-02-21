(function () {
  const app = window.SlipApp;

  const profiles = {
    hand1: {
      suffixWeights: { dy: 12, in: 4, y: 8, m: 3 },
      overlapWeight: 2,
    },
    hand2: {
      suffixWeights: { in: 20, dy: 2, m: 10, y: 5 },
      overlapWeight: 2,
    },
  };

  function createRng(seed) {
    let t = (seed >>> 0) || 1;
    return function random() {
      t += 0x6d2b79f5;
      let x = t;
      x = Math.imul(x ^ (x >>> 15), x | 1);
      x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    };
  }

  function randInt(random, min, max) {
    const low = Math.min(min, max);
    const high = Math.max(min, max);
    return low + Math.floor(random() * (high - low + 1));
  }

  function modulo(value, size) {
    return ((value % size) + size) % size;
  }

  function scoreWord(word, prevWord, profile) {
    let score = 1;
    Object.keys(profile.suffixWeights).forEach(function applySuffix(suffix) {
      if (word.endsWith(suffix)) {
        score += profile.suffixWeights[suffix];
      }
    });

    if (prevWord) {
      const seen = new Set(prevWord.split(""));
      let overlap = 0;
      word.split("").forEach(function overlapCount(ch) {
        if (seen.has(ch)) {
          overlap += 1;
        }
      });
      score += overlap * profile.overlapWeight;
    }

    return score;
  }

  function chooseWeighted(words, prevWord, profile, random) {
    if (!words.length) {
      return null;
    }

    const weights = words.map(function buildWeight(word) {
      return scoreWord(word, prevWord, profile);
    });

    const total = weights.reduce(function sum(acc, value) {
      return acc + value;
    }, 0);

    if (total <= 0) {
      return words[randInt(random, 0, words.length - 1)];
    }

    let pivot = random() * total;
    for (let idx = 0; idx < words.length; idx += 1) {
      pivot -= weights[idx];
      if (pivot <= 0) {
        return words[idx];
      }
    }
    return words[words.length - 1];
  }

  function parseMarkerFromLocation(location) {
    const raw = String(location || "");
    if (!raw.includes(",")) {
      return "";
    }
    return raw.split(",", 2)[1].trim();
  }

  function getFolioObservedMarkers(folio) {
    const lines = Array.isArray(folio.lines) ? folio.lines : [];
    return lines.map(function toMarker(line, idx) {
      const marker = parseMarkerFromLocation(line.location);
      if (marker) {
        return marker;
      }
      return idx === 0 ? "@P0" : "+P0";
    });
  }

  function extractLineAffix(content) {
    const raw = String(content || "").trim();
    if (!raw) {
      return { prefix: "", suffix: "" };
    }
    const prefixMatch = raw.match(/^((?:<[^>]+>)+)/);
    const suffixMatch = raw.match(/((?:<[^>]+>)+)$/);
    return {
      prefix: prefixMatch ? prefixMatch[1] : "",
      suffix: suffixMatch ? suffixMatch[1] : "",
    };
  }

  function getFolioObservedAffixes(folio) {
    const lines = Array.isArray(folio.lines) ? folio.lines : [];
    return lines.map(function toAffix(line) {
      return extractLineAffix(line.content);
    });
  }

  function getFolioScheduleEntry(pageSchedule, folioId) {
    if (!pageSchedule || !Array.isArray(pageSchedule.folios)) {
      return null;
    }
    for (let idx = 0; idx < pageSchedule.folios.length; idx += 1) {
      const entry = pageSchedule.folios[idx];
      if (entry && entry.folio === folioId) {
        return entry;
      }
    }
    return null;
  }

  function getSectionMarkerPrior(pagePriors, section, side, firstLine) {
    if (!pagePriors || !pagePriors.marker_priors) {
      return {};
    }
    const field = firstLine ? "first_line" : "continuation";
    const bySection = (pagePriors.marker_priors.by_section || {})[section] || {};
    const bySide = (pagePriors.marker_priors.by_side || {})[side] || {};
    const global = pagePriors.marker_priors.global || {};

    return bySection[field] || bySide[field] || global[field] || {};
  }

  function pickFromProbMap(probMap, random, fallback) {
    const entries = Object.entries(probMap || {});
    if (!entries.length) {
      return fallback;
    }

    let pivot = random();
    for (let idx = 0; idx < entries.length; idx += 1) {
      const key = entries[idx][0];
      const prob = Number(entries[idx][1]) || 0;
      pivot -= prob;
      if (pivot <= 0) {
        return key;
      }
    }
    return entries[entries.length - 1][0] || fallback;
  }

  function sampleLineCount(pagePriors, section, side, random, fallback) {
    if (!pagePriors || !pagePriors.line_count_priors) {
      return { lineCount: fallback, source: "fallback_observed" };
    }

    const bySection = (pagePriors.line_count_priors.by_section || {})[section];
    const bySide = (pagePriors.line_count_priors.by_side || {})[side];
    const global = pagePriors.line_count_priors.global || {};
    const hist = (bySection && bySection.histogram)
      || (bySide && bySide.histogram)
      || global.histogram
      || {};

    const entries = Object.entries(hist);
    if (!entries.length) {
      return { lineCount: fallback, source: "fallback_observed" };
    }

    const total = entries.reduce(function sum(acc, pair) {
      return acc + (Number(pair[1]) || 0);
    }, 0);
    if (total <= 0) {
      return { lineCount: fallback, source: "fallback_observed" };
    }

    let pivot = random() * total;
    for (let idx = 0; idx < entries.length; idx += 1) {
      const lineCount = Number.parseInt(entries[idx][0], 10);
      const count = Number(entries[idx][1]) || 0;
      pivot -= count;
      if (pivot <= 0 && Number.isFinite(lineCount) && lineCount > 0) {
        if (bySection && bySection.histogram) {
          return { lineCount: lineCount, source: "section_prior" };
        }
        if (bySide && bySide.histogram) {
          return { lineCount: lineCount, source: "side_prior" };
        }
        return { lineCount: lineCount, source: "global_prior" };
      }
    }

    const fallbackLineCount = Number.parseInt(entries[entries.length - 1][0], 10);
    if (Number.isFinite(fallbackLineCount) && fallbackLineCount > 0) {
      return { lineCount: fallbackLineCount, source: "global_prior" };
    }
    return { lineCount: fallback, source: "fallback_observed" };
  }

  function resolveLineOffset(scheduleEntry, lineIndex, scheduleMode, globalOffset) {
    if (scheduleMode === "global_only") {
      return { offset: globalOffset, source: "global_mode" };
    }

    if (!scheduleEntry) {
      return { offset: globalOffset, source: "global_mode" };
    }

    const lines = Array.isArray(scheduleEntry.lines) ? scheduleEntry.lines : [];
    if (lineIndex < lines.length) {
      const line = lines[lineIndex];
      if (line && Number.isFinite(Number(line.offset))) {
        return {
          offset: Number(line.offset),
          source: String(line.source || "line_inferred"),
        };
      }
    }

    if (Number.isFinite(Number(scheduleEntry.folio_mode_offset))) {
      return { offset: Number(scheduleEntry.folio_mode_offset), source: "folio_mode" };
    }
    if (Number.isFinite(Number(scheduleEntry.section_mode_offset))) {
      return { offset: Number(scheduleEntry.section_mode_offset), source: "section_mode" };
    }
    return { offset: globalOffset, source: "global_mode" };
  }

  app.generatePageByFolio = function generatePageByFolio(options) {
    const grid = app.state.data.grid;
    if (!grid || !app.state.data.windowIds.length) {
      return { ok: false, message: "Lattice data unavailable." };
    }

    const folioId = String(options.folioId || "").trim();
    const folio = app.state.data.folioMap[folioId];
    if (!folio) {
      return { ok: false, message: `Unknown folio "${folioId}".` };
    }

    const seed = Number.parseInt(options.seed, 10) || 42;
    const random = createRng(seed);
    const profile = profiles[options.profile] || profiles.hand1;
    const canonicalFilter = options.canonicalFilter !== false;
    const format = options.format === "ivtff" ? "ivtff" : "content";
    const scheduleMode = options.scheduleMode || "auto";
    const lineCountMode = options.lineCountMode || "observed";
    const minWords = Math.max(1, Number.parseInt(options.minWords, 10) || 6);
    const maxWords = Math.max(minWords, Number.parseInt(options.maxWords, 10) || 12);
    const warnings = [];

    const pageSchedule = app.state.data.pageSchedule;
    const pagePriors = app.state.data.pagePriors;
    const scheduleEntry = getFolioScheduleEntry(pageSchedule, folioId);
    const section = scheduleEntry ? String(scheduleEntry.section || "Other") : "Other";
    const hand = scheduleEntry ? String(scheduleEntry.hand || "Unknown") : "Unknown";
    const side = folioId.endsWith("r") ? "r" : (folioId.endsWith("v") ? "v" : "unknown");

    if (!scheduleEntry) {
      warnings.push("No folio schedule entry found; using global mode offset fallback.");
    }

    const globalOffset = Number.isFinite(Number((pageSchedule || {}).global_mode_offset))
      ? Number(pageSchedule.global_mode_offset)
      : 17;

    const observedLineCount = Math.max(1, Number.parseInt(folio.line_count, 10) || 1);
    let lineCount = observedLineCount;
    let lineCountSource = "observed";
    if (lineCountMode === "sampled") {
      const sampled = sampleLineCount(pagePriors, section, side, random, observedLineCount);
      lineCount = sampled.lineCount;
      lineCountSource = sampled.source;
      if (sampled.source === "fallback_observed") {
        warnings.push("Sampled line count unavailable for this context; using observed line count.");
      }
    }

    const observedMarkers = getFolioObservedMarkers(folio);
    const observedAffixes = getFolioObservedAffixes(folio);
    const sourceCounts = {};
    const ivtffLines = [];
    const contentLines = [];
    const lineDiagnostics = [];

    const windowIds = app.state.data.windowIds;
    const numWindows = windowIds.length;
    const latticeMap = grid.lattice_map;

    for (let lineIdx = 0; lineIdx < lineCount; lineIdx += 1) {
      const lineInfo = resolveLineOffset(scheduleEntry, lineIdx, scheduleMode, globalOffset);
      sourceCounts[lineInfo.source] = (sourceCounts[lineInfo.source] || 0) + 1;
      const targetWords = randInt(random, minWords, maxWords);

      let marker = observedMarkers[lineIdx] || "";
      if (!marker) {
        if (lineCountMode === "sampled") {
          const prior = getSectionMarkerPrior(pagePriors, section, side, lineIdx === 0);
          marker = pickFromProbMap(prior, random, lineIdx === 0 ? "@P0" : "+P0");
        } else {
          marker = lineIdx === 0 ? "@P0" : "+P0";
        }
      }

      let currentWindow = randInt(random, 0, numWindows - 1);
      let prevWord = null;
      const tokens = [];
      for (let tokenIdx = 0; tokenIdx < targetWords; tokenIdx += 1) {
        const shiftedWindow = modulo(currentWindow + lineInfo.offset, numWindows);
        const shiftedWords = app.getWindowWords(shiftedWindow);
        const candidates = canonicalFilter
          ? shiftedWords.filter(function keepCanonical(word) { return !/[A-Z]/.test(word); })
          : shiftedWords;
        if (!candidates.length) {
          tokens.push("???");
          currentWindow = modulo(currentWindow + 1, numWindows);
          prevWord = "???";
          continue;
        }

        const chosenWord = chooseWeighted(candidates, prevWord, profile, random);
        tokens.push(chosenWord);
        const assignedRaw = latticeMap[chosenWord];
        const assignedWindow = typeof assignedRaw === "undefined"
          ? modulo(currentWindow + 1, numWindows)
          : Number.parseInt(assignedRaw, 10);
        if (Number.isFinite(assignedWindow)) {
          currentWindow = modulo(assignedWindow - lineInfo.offset, numWindows);
        } else {
          currentWindow = modulo(currentWindow + 1, numWindows);
        }
        prevWord = chosenWord;
      }

      const affix = observedAffixes[lineIdx] || { prefix: "", suffix: "" };
      let content = tokens.join(".");
      if (affix.prefix) {
        content = `${affix.prefix}${content}`;
      }
      if (affix.suffix) {
        content = `${content}${affix.suffix}`;
      }
      contentLines.push(content);
      if (format === "ivtff") {
        ivtffLines.push(`<${folioId}.${lineIdx + 1},${marker}>      ${content}`);
      }
      lineDiagnostics.push({
        lineIndex: lineIdx,
        marker: marker,
        offset: lineInfo.offset,
        offsetSource: lineInfo.source,
        words: tokens.length,
      });
    }

    const avgWords = contentLines.length
      ? lineDiagnostics.reduce(function sum(acc, row) { return acc + row.words; }, 0) / contentLines.length
      : 0;
    const text = format === "ivtff" ? ivtffLines.join("\n") : contentLines.join("\n");

    return {
      ok: true,
      seed: seed,
      folioId: folioId,
      section: section,
      hand: hand,
      side: side,
      lineCount: lineCount,
      lineCountSource: lineCountSource,
      scheduleMode: scheduleMode,
      globalOffset: globalOffset,
      sourceCounts: sourceCounts,
      warnings: warnings,
      profile: options.profile || "hand1",
      format: format,
      avgWordsPerLine: avgWords,
      text: text,
      lines: contentLines,
      lineDiagnostics: lineDiagnostics,
    };
  };
})();
