var DOCUMENTATION_OPTIONS = {};


describe('jQuery extensions', function() {

  describe('urldecode', function() {

    it('should correctly decode URLs and replace `+`s with a spaces', function() {
      var test_encoded_string =
        '%D1%88%D0%B5%D0%BB%D0%BB%D1%8B+%D1%88%D0%B5%D0%BB%D0%BB%D1%8B';
      var test_decoded_string = 'шеллы шеллы';
      expect(jQuery.urldecode(test_encoded_string)).toEqual(test_decoded_string);
    });

    it('+ should result in " "', function() {
      expect(jQuery.urldecode('+')).toEqual(' ');
    });

  });

  describe('getQueryParameters', function() {
    var paramString = '?q=test+this&check_keywords=yes&area=default';
    var queryParamObject = {
      area: ['default'],
      check_keywords: ['yes'],
      q: ['test this']
    };

    it('should correctly create query parameter object from string', function() {
      expect(jQuery.getQueryParameters(paramString)).toEqual(queryParamObject);
    });

    it('should correctly create query param object from URL params', function() {
      history.pushState({}, '_', window.location + paramString);
      expect(jQuery.getQueryParameters()).toEqual(queryParamObject);
    });

  });

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


