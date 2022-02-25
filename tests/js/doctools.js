const DOCUMENTATION_OPTIONS = {};

describe('highlightText', function() {

  const cyrillicTerm = 'шеллы';
  const umlautTerm = 'gänsefüßchen';

  it('should highlight text incl. special characters correctly in HTML', function() {
    const highlightTestSpan = new DOMParser().parseFromString(
      '<span>This is the шеллы and Gänsefüßchen test!</span>', 'text/html').body.firstChild
    _highlightText(highlightTestSpan, cyrillicTerm, 'highlighted');
    _highlightText(highlightTestSpan, umlautTerm, 'highlighted');
    const expectedHtmlString =
      'This is the <span class=\"highlighted\">шеллы</span> and ' +
      '<span class=\"highlighted\">Gänsefüßchen</span> test!';
    expect(highlightTestSpan.innerHTML).toEqual(expectedHtmlString);
  });

  it('should highlight text incl. special characters correctly in SVG', function() {
    const highlightTestSvg = new DOMParser().parseFromString(
      '<span id="svg-highlight-test">' +
        '<svg xmlns="http://www.w3.org/2000/svg" height="50" width="500">' +
          '<text x="0" y="15">' +
            'This is the шеллы and Gänsefüßchen test!' +
          '</text>' +
        '</svg>' +
      '</span>', 'text/html').body.firstChild
    _highlightText(highlightTestSvg, cyrillicTerm, 'highlighted');
    _highlightText(highlightTestSvg, umlautTerm, 'highlighted');
    /* Note wild cards and ``toMatch``; allowing for some variability
       seems to be necessary, even between different FF versions */
    const expectedSvgString =
      '<svg xmlns="http://www.w3.org/2000/svg" height="50" width="500">'
      + '<rect x=".*" y=".*" width=".*" height=".*" class="highlighted"/>'
      + '<rect x=".*" y=".*" width=".*" height=".*" class="highlighted"/>'
      + '<text x=".*" y=".*">This is the <tspan>шеллы</tspan> and '
      + '<tspan>Gänsefüßchen</tspan> test!</text></svg>';
    expect(new XMLSerializer().serializeToString(highlightTestSvg.firstChild)).toMatch(new RegExp(expectedSvgString));
  });

});
