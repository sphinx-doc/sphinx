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
        2,
        "index.rst"
      ]];
      expect(Search.performTermsSearch(searchterms, excluded, terms, titleterms)).toEqual(hits);
    });

  });

});
