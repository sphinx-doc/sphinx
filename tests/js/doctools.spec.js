describe("Documentation translations", function () {
  let originalTranslations;
  let originalPluralExpr;
  let originalLocale;

  beforeEach(function () {
    originalTranslations = Documentation.TRANSLATIONS;
    originalPluralExpr = Documentation.PLURAL_EXPR;
    originalLocale = Documentation.LOCALE;
    Documentation.TRANSLATIONS = {};
  });

  afterEach(function () {
    Documentation.TRANSLATIONS = originalTranslations;
    Documentation.PLURAL_EXPR = originalPluralExpr;
    Documentation.LOCALE = originalLocale;
  });

  it("selects translated forms with a boolean plural expression", function () {
    Documentation.addTranslations({
      locale: "de",
      plural_expr: "(n != 1)",
      messages: { page: ["Seite", "Seiten"] },
    });

    expect(Documentation.ngettext("page", "pages", 1)).toBe("Seite");
    expect(Documentation.ngettext("page", "pages", 2)).toBe("Seiten");
  });

  it("selects all translated forms with a numeric plural expression", function () {
    Documentation.addTranslations({
      locale: "pl",
      plural_expr:
        "(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : 2)",
      messages: { page: ["strona", "strony", "stron"] },
    });

    expect(Documentation.ngettext("page", "pages", 1)).toBe("strona");
    expect(Documentation.ngettext("page", "pages", 2)).toBe("strony");
    expect(Documentation.ngettext("page", "pages", 5)).toBe("stron");
    expect(Documentation.ngettext("page", "pages", 11)).toBe("stron");
    expect(Documentation.ngettext("page", "pages", 12)).toBe("stron");
    expect(Documentation.ngettext("page", "pages", 21)).toBe("stron");
    expect(Documentation.ngettext("page", "pages", 22)).toBe("strony");
  });
});
