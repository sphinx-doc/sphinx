var DOCUMENTATION_OPTIONS = {};


describe('jQuery extensions', function() {

  describe('highlightText', function() {

    var cyrillicTerm = 'шеллы';
    var umlautTerm = 'gänsefüßchen';

    it('should highlight text incl. special characters correctly in HTML', function() {
      var highlightTestSpan =
        jQuery('<span>This is the шеллы and Gänsefüßchen test!</span>');
      jQuery(document.body).append(highlightTestSpan);
      highlightTestSpan.highlightText(cyrillicTerm, 'highlighted');
      highlightTestSpan.highlightText(umlautTerm, 'highlighted');
      var expectedHtmlString =
        'This is the <span class=\"highlighted\">шеллы</span> and ' +
        '<span class=\"highlighted\">Gänsefüßchen</span> test!';
      expect(highlightTestSpan.html()).toEqual(expectedHtmlString);
    });

    it('should highlight text incl. special characters correctly in SVG', function() {
      var highlightTestSvg = jQuery(
        '<span id="svg-highlight-test">' +
          '<svg xmlns="http://www.w3.org/2000/svg" height="50" width="500">' +
            '<text x="0" y="15">' +
              'This is the шеллы and Gänsefüßchen test!' +
            '</text>' +
          '</svg>' +
        '</span>');
      jQuery(document.body).append(highlightTestSvg);
      highlightTestSvg.highlightText(cyrillicTerm, 'highlighted');
      highlightTestSvg.highlightText(umlautTerm, 'highlighted');
      /* Note wild cards and ``toMatch``; allowing for some variability
         seems to be necessary, even between different FF versions */
      var expectedSvgString =
        '<svg xmlns="http://www.w3.org/2000/svg" height="50" width="500">' +
          '<rect x=".*" y=".*" width=".*" height=".*" class="highlighted">' +
          '</rect>' +
          '<rect x=".*" y=".*" width=".*" height=".*" class="highlighted">' +
          '</rect>' +
          '<text x=".*" y=".*">' +
            'This is the ' +
            '<tspan>шеллы</tspan> and ' +
            '<tspan>Gänsefüßchen</tspan> test!' +
          '</text>' +
        '</svg>';
      expect(highlightTestSvg.html()).toMatch(new RegExp(expectedSvgString));
    });

  });


});


