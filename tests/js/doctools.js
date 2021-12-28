var DOCUMENTATION_OPTIONS = {};

describe('highlightText', function() {

  var cyrillicTerm = 'шеллы';
  var umlautTerm = 'gänsefüßchen';

  it('should highlight text incl. special characters correctly in HTML', function() {
    var highlightTestSpan =new DOMParser().parseFromString(
      '<span>This is the шеллы and Gänsefüßchen test!</span>', 'text/html').body.firstChild;
    document.body.append(highlightTestSpan);
    highlightText(highlightTestSpan, cyrillicTerm, 'highlighted');
    highlightText(highlightTestSpan, umlautTerm, 'highlighted');
    var expectedHtmlString =
      'This is the <span class=\"highlighted\">шеллы</span> and ' +
      '<span class=\"highlighted\">Gänsefüßchen</span> test!';
    expect(highlightTestSpan.toString()).toEqual(expectedHtmlString);
  });

  it('should highlight text incl. special characters correctly in SVG', function() {
    var highlightTestSvg = new DOMParser().parseFromString(
      '<span id="svg-highlight-test">' +
        '<svg xmlns="http://www.w3.org/2000/svg" height="50" width="500">' +
          '<text x="0" y="15">' +
            'This is the шеллы and Gänsefüßchen test!' +
          '</text>' +
        '</svg>' +
      '</span>', 'text/html').body.firstChild;
    document.body.append(highlightTestSvg);
    highlightText(highlightTestSvg, cyrillicTerm, 'highlighted');
    highlightText(highlightTestSvg, umlautTerm, 'highlighted');
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
    expect(highlightTestSvg.toString()).toMatch(new RegExp(expectedSvgString));
  });

});
