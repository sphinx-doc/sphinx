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
    const parts = splitQuery("   Hello    World   ");
    expect(parts).toEqual(["Hello", "World"]);
  });

  it("can split special characters", () => {
    const parts = splitQuery("Pin-Code");
    expect(parts).toEqual(["Pin", "Code"]);
  });

  it("can split Chinese characters", () => {
    const parts = splitQuery("Hello from 中国 上海");
    expect(parts).toEqual(["Hello", "from", "中国", "上海"]);
  });

  it("can split Emoji (surrogate pair) characters. It should keep emojis.", () => {
    const parts = splitQuery("😁😁");
    expect(parts).toEqual(["😁😁"]);
  });

  it("can split umlauts. It should keep umlauts.", () => {
    const parts = splitQuery("Löschen Prüfung Abändern ærlig spørsmål");
    // prettier-ignore
    expect(parts).toEqual(["Löschen", "Prüfung", "Abändern", "ærlig", "spørsmål"])
  });
});
