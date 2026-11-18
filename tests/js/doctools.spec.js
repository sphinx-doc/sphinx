describe("Documentation.ngettext", () => {
  const singular = "Search finished, found one page matching the search query.";
  const plural =
    "Search finished, found ${resultCount} pages matching the search query.";

  afterEach(() => {
    Documentation.TRANSLATIONS = {};
    Documentation.PLURAL_EXPR = (n) => (n === 1 ? 0 : 1);
  });

  it("falls back to the original message when the selected translation is empty", () => {
    Documentation.addTranslations({
      locale: "ru",
      plural_expr:
        "(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : n%10==0 || (n%10>=5 && n%10<=9) || (n%100>=11 && n%100<=14) ? 2 : 3)",
      messages: {
        [singular]: ["", "", "", ""],
      },
    });

    for (const n of [1, 2, 5, 21]) {
      const expected = n === 1 ? singular : plural;
      expect(Documentation.ngettext(singular, plural, n)).toBe(expected);
    }
  });

  it("uses the translation when it is not empty", () => {
    Documentation.addTranslations({
      locale: "test",
      plural_expr: "n==1 ? 0 : 1",
      messages: {
        [singular]: ["Une page", "Plusieurs pages"],
      },
    });

    expect(Documentation.ngettext(singular, plural, 2)).toBe("Plusieurs pages");
  });
});
