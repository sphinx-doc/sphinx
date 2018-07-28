var DOCUMENTATION_OPTIONS = {};

describe('urldecode', function() {

  it('should correctly decode URLs and replace `+`s with a spaces', function() {
    var test_encoded_string =
      '%D1%88%D0%B5%D0%BB%D0%BB%D1%8B+%D1%88%D0%B5%D0%BB%D0%BB%D1%8B';
    var test_decoded_string = 'шеллы шеллы';
    expect(jQuery.urldecode(test_encoded_string)).toEqual(test_decoded_string);
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

