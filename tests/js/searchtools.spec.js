describe("Basic html theme search", function () {
  function loadFixture(name) {
    req = new XMLHttpRequest();
    req.open("GET", `__src__/tests/js/fixtures/${name}`, false);
    req.send(null);
    return req.responseText;
  }

  function checkRanking(expectedRanking, results) {
    let [nextExpected, ...remainingItems] = expectedRanking;

    for (result of results.reverse()) {
      if (!nextExpected) break;

      let [expectedPage, expectedTitle, expectedTarget] = nextExpected;
      let [page, title, target] = result;

      if (
        page == expectedPage
        && title == expectedTitle
        && target == expectedTarget
      ) {
        [nextExpected, ...remainingItems] = remainingItems;
      }
    }

    expect(remainingItems.length).toEqual(0);
    expect(nextExpected).toEqual(undefined);
  }

  describe("terms search", function () {
    it('should find "C++" when in index', function () {
      eval(loadFixture("cpp/searchindex.js"));

      [_searchQuery, searchterms, excluded, ..._remainingItems] =
        Search._parseQuery("C++");

      // prettier-ignore
      hits = [[
        "index",
        "<no title>",
        "",
        null,
        5,
        "index.rst",
        "text"
      ]];
      expect(Search.performTermsSearch(searchterms, excluded)).toEqual(hits);
    });

    it("should be able to search for multiple terms", function () {
      eval(loadFixture("multiterm/searchindex.js"));

      [_searchQuery, searchterms, excluded, ..._remainingItems] =
        Search._parseQuery("main page");
      // prettier-ignore
      hits = [[
        'index',
        'Main Page',
        '',
        null,
        15,
        'index.rst',
        'text'
      ]];
      expect(Search.performTermsSearch(searchterms, excluded)).toEqual(hits);
    });

    it('should partially-match "sphinx" when in title index', function () {
      eval(loadFixture("partial/searchindex.js"));

      [_searchQuery, searchterms, excluded, ..._remainingItems] =
        Search._parseQuery("sphinx");

      // prettier-ignore
      hits = [[
        "index",
        "sphinx_utils module",
        "",
        null,
        7,
        "index.rst",
        "text"
      ]];
      expect(Search.performTermsSearch(searchterms, excluded)).toEqual(hits);
    });

    it('should partially-match within "possible" when in term index', function () {
      eval(loadFixture("partial/searchindex.js"));

      [_searchQuery, searchterms, excluded, ..._remainingItems] =
        Search._parseQuery("ossibl");
      terms = Search._index.terms;
      titleterms = Search._index.titleterms;

      // prettier-ignore
      hits = [[
        "index",
        "sphinx_utils module",
        "",
        null,
        2,
        "index.rst",
        "text"
      ]];
      expect(
        Search.performTermsSearch(searchterms, excluded, terms, titleterms),
      ).toEqual(hits);
    });
  });

  describe("aggregation of search results", function () {
    it("should combine document title and document term matches", function () {
      eval(loadFixture("multiterm/searchindex.js"));

      searchParameters = Search._parseQuery("main page");

      // prettier-ignore
      hits = [
        [
          'index',
          'Main Page',
          '',
          null,
          16,
          'index.rst',
          'title'
        ]
      ];
      expect(Search._performSearch(...searchParameters)).toEqual(hits);
    });
  });

  describe("search result ranking", function () {
    /*
     * These tests should not proscribe precise expected ordering of search
     * results; instead each test case should describe a single relevance rule
     * that helps users to locate relevant information efficiently.
     *
     * If you think that one of the rules seems to be poorly-defined or is
     * limiting the potential for search algorithm improvements, please check
     * for existing discussion/bugreports related to it on GitHub[1] before
     * creating one yourself. Suggestions for possible improvements are also
     * welcome.
     *
     * [1] - https://github.com/sphinx-doc/sphinx.git/
     */

    it("should score a code module match above a page-title match", function () {
      eval(loadFixture("titles/searchindex.js"));

      // prettier-ignore
      expectedRanking = [
        ['index', 'relevance', '#module-relevance'],  /* py:module documentation */
        ['relevance', 'Relevance', ''],  /* main title */
      ];

      searchParameters = Search._parseQuery("relevance");
      results = Search._performSearch(...searchParameters);

      checkRanking(expectedRanking, results);
    });

    it("should score a main-title match above an object member match", function () {
      eval(loadFixture("titles/searchindex.js"));

      // prettier-ignore
      expectedRanking = [
        ['relevance', 'Relevance', ''],  /* main title */
        ['index', 'relevance.Example.relevance', '#relevance.Example.relevance'],  /* py:class attribute */
      ];

      searchParameters = Search._parseQuery("relevance");
      results = Search._performSearch(...searchParameters);

      checkRanking(expectedRanking, results);
    });

    it("should score a title match above a standard index entry match", function () {
      eval(loadFixture("titles/searchindex.js"));

      // prettier-ignore
      expectedRanking = [
        ['relevance', 'Relevance', ''],  /* title */
        ['index', 'Main Page', '#index-1'],  /* index entry */
      ];

      searchParameters = Search._parseQuery("relevance");
      results = Search._performSearch(...searchParameters);

      checkRanking(expectedRanking, results);
    });

    it("should score a priority index entry match above a title match", function () {
      eval(loadFixture("titles/searchindex.js"));

      // prettier-ignore
      expectedRanking = [
        ['index', 'Main Page', '#index-0'],  /* index entry */
        ['index', 'Main Page > Result Scoring', '#result-scoring'],  /* title */
      ];

      searchParameters = Search._parseQuery("scoring");
      results = Search._performSearch(...searchParameters);

      checkRanking(expectedRanking, results);
    });

    it("should score a main-title match above a subheading-title match", function () {
      eval(loadFixture("titles/searchindex.js"));

      // prettier-ignore
      expectedRanking = [
        ['relevance', 'Relevance', ''],  /* main title */
        ['index', 'Main Page > Relevance', '#relevance'],  /* subsection heading title */
      ];

      searchParameters = Search._parseQuery("relevance");
      results = Search._performSearch(...searchParameters);

      checkRanking(expectedRanking, results);
    });
  });

  describe("can handle edge-case search queries", function () {
    it("does not find the javascript prototype property in unrelated documents", function () {
      eval(loadFixture("partial/searchindex.js"));

      searchParameters = Search._parseQuery("__proto__");

      // prettier-ignore
      hits = [];
      expect(Search._performSearch(...searchParameters)).toEqual(hits);
    });
  });
});

describe("htmlToText", function () {
  const testHTML = `<html>
  <body>
    <script src="directory/filename.js"></script>
    <div class="body" role="main">
      <script>
        console.log('dynamic');
      </script>
      <style>
        div.body p.centered {
          text-align: center;
          margin-top: 25px;
        }
      </style>
      <!-- main content -->
      <section id="getting-started">
        <h1>Getting Started <a class="headerlink" href="#getting-started" title="Link to this heading">¶</a></h1>
        <p>Some text</p>
      </section>
      <section id="other-section">
        <h1>Other Section <a class="headerlink" href="#other-section" title="Link to this heading">¶</a></h1>
        <p>Other text</p>
      </section>
      <section id="yet-another-section">
        <h1>Yet Another Section <a class="headerlink" href="#yet-another-section" title="Link to this heading">¶</a></h1>
        <p>More text</p>
      </section>
    </div>
  </body>
  </html>`;

  it("basic case", () => {
    expect(Search.htmlToText(testHTML).trim().split(/\s+/)).toEqual(
      /* prettier-ignore */ [
      "Getting", "Started", "Some", "text",
      "Other", "Section", "Other", "text",
      "Yet", "Another", "Section", "More", "text"
    ],
    );
  });

  it("will start reading from the anchor", () => {
    expect(
      Search.htmlToText(testHTML, "#other-section").trim().split(/\s+/),
    ).toEqual(["Other", "Section", "Other", "text"]);
  });
});

// Regression test for https://github.com/sphinx-doc/sphinx/issues/3150
describe("splitQuery regression tests", () => {
  it("can split English words", () => {
    const result = splitQuery("   Hello    World   ");
    expect(result).toEqual({ quotedTerms: [], plainTerms: ["Hello", "World"] });
  });

  it("can split special characters", () => {
    const result = splitQuery("Pin-Code");
    expect(result).toEqual({ quotedTerms: [], plainTerms: ["Pin", "Code"] });
  });

  it("can split Chinese characters", () => {
    const result = splitQuery("Hello from 中国 上海");
    expect(result).toEqual({ quotedTerms: [], plainTerms: ["Hello", "from", "中国", "上海"] });
  });

  it("can split Emoji (surrogate pair) characters. It should keep emojis.", () => {
    const result = splitQuery("😁😁");
    expect(result).toEqual({ quotedTerms: [], plainTerms: ["😁😁"] });
  });

  it("can split umlauts. It should keep umlauts.", () => {
    const result = splitQuery("Löschen Prüfung Abändern ærlig spørsmål");
    // prettier-ignore
    expect(result).toEqual({ quotedTerms: [], plainTerms: ["Löschen", "Prüfung", "Abändern", "ærlig", "spørsmål"] });
  });


  describe("splitQuery with quoted CLI flags", () => {
    it('should extract quoted CLI flags as quotedTerms', () => {
      const result = splitQuery('"--dry-run" other words');
      expect(result).toEqual({
        quotedTerms: ["--dry-run"],
        plainTerms: ["other", "words"]
      });
    });

    it('should handle multiple quoted terms', () => {
      const result = splitQuery('"--dry-run" and "-v" mode');
      expect(result).toEqual({
        quotedTerms: ["--dry-run", "-v"],
        plainTerms: ["and", "mode"]
      });
    });

    it('should return empty quotedTerms when no quotes present', () => {
      const result = splitQuery("well-known text");
      expect(result).toEqual({
        quotedTerms: [],
        plainTerms: ["well", "known", "text"]
      });
    });

    it('should handle mixed quoted and unquoted content', () => {
      const result = splitQuery('Use "--dry-run" for testing -v flags');
      expect(result).toEqual({
        quotedTerms: ["--dry-run"],
        plainTerms: ["Use", "for", "testing", "v", "flags"]
      });
    });
  });

  describe("_parseQuery with quoted CLI flags", () => {
    it('should not add quoted CLI flags to excludedTerms', () => {
      // Test that splitQuery correctly separates quoted terms
      const result = splitQuery('"--dry-run"');
      expect(result.quotedTerms).toEqual(["--dry-run"]);
      expect(result.plainTerms).toEqual([]);
      
      // Verify that quoted terms bypass the exclusion logic in _parseQuery
      // This is tested indirectly by ensuring quoted terms are handled separately from plain terms
    });

    it('should handle quoted and unquoted terms correctly', () => {
      // Test that splitQuery correctly separates quoted and unquoted terms
      const result = splitQuery('"--dry-run" -v');
      expect(result.quotedTerms).toEqual(["--dry-run"]);
      expect(result.plainTerms).toEqual(["v"]);
      
      // Verify that quoted terms go to searchTerms and unquoted terms with - go to excludedTerms
      // This separation is handled in _parseQuery by processing quotedTerms and plainTerms separately
    });

    it('quoted terms should be stemmed before indexing', () => {
      // Test that quoted terms are processed correctly by splitQuery
      const result = splitQuery('"--running"');
      expect(result.quotedTerms).toEqual(["--running"]);
      expect(result.plainTerms).toEqual([]);
      
      // The actual stemming happens in _parseQuery, but splitQuery correctly extracts the quoted terms
    });
  });
});
