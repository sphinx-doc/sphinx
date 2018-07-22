var DOCUMENTATION_OPTIONS = {};

describe('urldecode', function() {

  it('should fail', function() {
    var test_encoded_string =
      '%D1%88%D0%B5%D0%BB%D0%BB%D1%8B+%D1%88%D0%B5%D0%BB%D0%BB%D1%8B';
    var test_decoded_string = 'шеллы шеллы';
    expect(jQuery.urldecode(test_encoded_string)).toEqual(test_decoded_string);
  });

});
