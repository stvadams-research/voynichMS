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

  function scoreWord(word, prevWord, profile) {
    let score = 1;
    const suffixWeights = profile.suffixWeights;

    Object.keys(suffixWeights).forEach(function applySuffix(suffix) {
      if (word.endsWith(suffix)) {
        score += suffixWeights[suffix];
      }
    });

    if (prevWord) {
      const seen = new Set(prevWord.split(""));
      let overlap = 0;
      word.split("").forEach(function countOverlap(ch) {
        if (seen.has(ch)) {
          overlap += 1;
        }
      });
      score += overlap * profile.overlapWeight;
    }

    return score;
  }

  function chooseWeighted(words, prevWord, profile, random) {
    const weights = words.map(function buildWeight(word) {
      return scoreWord(word, prevWord, profile);
    });

    const total = weights.reduce(function sum(a, b) {
      return a + b;
    }, 0);

    if (total <= 0) {
      return words[randInt(random, 0, words.length - 1)];
    }

    let pivot = random() * total;
    for (let i = 0; i < words.length; i += 1) {
      pivot -= weights[i];
      if (pivot <= 0) {
        return words[i];
      }
    }

    return words[words.length - 1];
  }

  app.generateSyntheticFolio = function generateSyntheticFolio(options) {
    const grid = app.state.data.grid;
    if (!grid || !app.state.data.windowIds.length) {
      return {
        ok: false,
        message: "Lattice data unavailable.",
      };
    }

    const seed = Number.parseInt(options.seed, 10) || 42;
    const lineCount = Math.max(1, Number.parseInt(options.lineCount, 10) || 9);
    const minWords = Math.max(1, Number.parseInt(options.minWords, 10) || 6);
    const maxWords = Math.max(minWords, Number.parseInt(options.maxWords, 10) || 12);
    const folioLabelRaw = String(options.folioLabel || "f1000r").trim();
    const format = options.format || "content";
    const profile = profiles[options.profile] || profiles.hand1;
    const canonicalFilter = options.canonicalFilter !== false;
    const folioLabelPattern = /^f[0-9]+[rv][0-9]*$/;
    const folioLabel = folioLabelPattern.test(folioLabelRaw) ? folioLabelRaw : "f1000r";
    const warnings = [];
    if (folioLabel !== folioLabelRaw) {
      warnings.push(`Folio label "${folioLabelRaw}" is non-canonical; using "${folioLabel}".`);
    }

    const random = createRng(seed);
    const windowIds = app.state.data.windowIds;
    const numWindows = windowIds.length;

    let currentWindow;
    if (Number.isFinite(options.startWindow)) {
      currentWindow = ((options.startWindow % numWindows) + numWindows) % numWindows;
    } else {
      currentWindow = windowIds[randInt(random, 0, windowIds.length - 1)];
    }

    const lines = [];
    const ivtffLines = [];

    for (let lineIdx = 0; lineIdx < lineCount; lineIdx += 1) {
      const targetLength = randInt(random, minWords, maxWords);
      const tokens = [];
      let prevWord = null;

      for (let pos = 0; pos < targetLength; pos += 1) {
        const windowWords = app.getWindowWords(currentWindow);
        const words = canonicalFilter
          ? windowWords.filter(function keepCanonical(word) { return !/[A-Z]/.test(word); })
          : windowWords;
        if (!words.length) {
          tokens.push("???");
          currentWindow = (currentWindow + 1) % numWindows;
          prevWord = "???";
          continue;
        }

        const word = chooseWeighted(words, prevWord, profile, random);
        tokens.push(word);

        const nextRaw = grid.lattice_map[word];
        const nextWindow = typeof nextRaw === "undefined"
          ? (currentWindow + 1) % numWindows
          : Number.parseInt(nextRaw, 10);

        currentWindow = Number.isFinite(nextWindow)
          ? ((nextWindow % numWindows) + numWindows) % numWindows
          : (currentWindow + 1) % numWindows;
        prevWord = word;
      }

      lines.push(tokens);

      if (format === "ivtff") {
        const marker = lineIdx === 0 ? "@P0" : "+P0";
        ivtffLines.push(`<${folioLabel}.${lineIdx + 1},${marker}>      ${tokens.join(".")}`);
      }
    }

    const contentText = lines
      .map(function joinTokens(tokens) {
        return tokens.join(".");
      })
      .join("\n");

    return {
      ok: true,
      seed,
      lineCount,
      minWords,
      maxWords,
      format,
      profile: options.profile,
      lines,
      text: format === "ivtff" ? ivtffLines.join("\n") : contentText,
      contentText,
      warnings,
      avgWordsPerLine: lines.length
        ? lines.reduce(function sum(acc, tokens) { return acc + tokens.length; }, 0) / lines.length
        : 0,
    };
  };
})();
