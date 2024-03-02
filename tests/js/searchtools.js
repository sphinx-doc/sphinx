describe('Basic html theme search', function() {

  describe('terms search', function() {

    it('should find "C++" when in index', function() {
      index = {
        docnames:["index"],
        filenames:["index.rst"],
        terms:{'c++':0},
        titles:["&lt;no title&gt;"],
        titleterms:{}
      }
      Search.setIndex(index);
      searchterms = ['c++'];
      excluded = [];
      terms = index.terms;
      titleterms = index.titleterms;

      hits = [[
        "index",
        "&lt;no title&gt;",
        "",
        null,
        5,
        "index.rst"
      ]];
      expect(Search.performTermsSearch(searchterms, excluded, terms, titleterms)).toEqual(hits);
    });

    it('should partially-match "sphinx" when in title index', function() {
      index = {
        docnames:["index"],
        filenames:["index.rst"],
        terms:{'useful': 0, 'utilities': 0},
        titles:["sphinx_utils module"],
        titleterms:{'sphinx_utils': 0}
      }
      Search.setIndex(index);
      searchterms = ['sphinx'];
      excluded = [];
      terms = index.terms;
      titleterms = index.titleterms;

      hits = [[
        "index",
        "sphinx_utils module",
        "",
        null,
        7,
        "index.rst"
      ]];
      expect(Search.performTermsSearch(searchterms, excluded, terms, titleterms)).toEqual(hits);
    });

  });

});

describe("htmlToText", function() {

  const testHTML = `<html>
  <div class="body" role="main">
    <section id="getting-started">
      <h1>Getting Started</h1>
      <p>Some text</p>
    </section>
    <section id="other-section">
      <h1>Other Section</h1>
      <p>Other text</p>
    </section>
    <section id="yet-another-section">
      <h1>Yet Another Section</h1>
      <p>More text</p>
    </section>
  </div>
  </html>`;

  it("basic case", () => {
    expect(Search.htmlToText(testHTML).trim().split(/\s+/)).toEqual([
      'Getting', 'Started', 'Some', 'text', 
      'Other', 'Section', 'Other', 'text', 
      'Yet', 'Another', 'Section', 'More', 'text'
    ]);
  });

  it("will start reading from the anchor", () => {
    expect(Search.htmlToText(testHTML, '#other-section').trim().split(/\s+/)).toEqual(['Other', 'Section', 'Other', 'text']);
  });
});

// This is regression test for https://github.com/sphinx-doc/sphinx/issues/3150
describe('splitQuery regression tests', () => {

  it('can split English words', () => {
    const parts = splitQuery('   Hello    World   ')
    expect(parts).toEqual(['Hello', 'World'])
  })

  it('can split special characters', () => {
    const parts = splitQuery('Pin-Code')
    expect(parts).toEqual(['Pin', 'Code'])
  })

  it('can split Chinese characters', () => {
    const parts = splitQuery('Hello from 中国 上海')
    expect(parts).toEqual(['Hello', 'from', '中国', '上海'])
  })

  it('can split Emoji (surrogate pair) characters. It should keep emojis.', () => {
    const parts = splitQuery('😁😁')
    expect(parts).toEqual(['😁😁'])
  })

  it('can split umlauts. It should keep umlauts.', () => {
    const parts = splitQuery('Löschen Prüfung Abändern ærlig spørsmål')
    expect(parts).toEqual(['Löschen', 'Prüfung', 'Abändern', 'ærlig', 'spørsmål'])
  })

})
