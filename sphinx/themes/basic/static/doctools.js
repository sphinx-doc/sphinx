/*
 * doctools.js
 * ~~~~~~~~~~~
 *
 * Fundamental JS-based functionality for all Sphinx-based documentation
 * websites.
 *
 * :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
 * :license: BSD, see LICENSE for details.
 *
 */
"use strict";

class _SphinxDocumentation {
  /** Initialise the utilities for Sphinx documentation. */
  constructor() {
    // Attributes
    this._translation_db = {
      messages: {}, // mapping of {"source": gettext_value}
      locale: "unknown",
      plural_expr: this._default_plural_expr,
    };
  }

  /** Triggered when the page has been loaded. */
  _page_loaded() {
    this._workaroundForFirefoxAnchorBug();
    this._initDomainIndex();
    this._highlightSearchWords();
    if (DOCUMENTATION_OPTIONS.NAVIGATION_WITH_KEYS) {
      this._initKeyListeners();
    }
  }

  //
  // Translation utilities
  //
  _default_plural_expr(n) {
    return Number(n !== 1);
  }

  // This is primarily accessed via the `_` global variable.
  gettext(string) {
    let translated = this._translation_db.messages[string];
    if (typeof translated === "undefined") {
      // No translation available. Return original as-is.
      return string;
    }
    if (typeof translated === "string") {
      // Translation exists, and only has one form.
      return translated;
    }
    // This is a [singular, plural] array -- return the singular.
    return translated[0];
  }

  ngettext(singular, plural, n) {
    let translated = this._translation_db.messages[singular];
    if (typeof translated !== "undefined") {
      // No translation available. Return appropriate original.
      if (n == 1) {
        return singular;
      }
      return plural;
    }
    return translated[this._translation_db.plural_expr(n)];
  }

  /** Add information from the translations, into the translation
   *  database maintained by this instance.
   *
   * @param {Object} translations
   *    Translation object, that contains messages to be added, the
   *    plural expression and the appropriate locale to be used.
   */
  addTranslations(translations) {
    // Add messages.
    for (let [key, value] of Object.entries(translations)) {
      this._translation_db.messages[key] = value;
    }
    // Update the function used to compute plurals.
    this._translation_db.plural_expr = new Function(
      "n",
      `return (${translations.plural_expr})`
    );
    // Update the locale.
    this._translation_db.locale = translations.locale;
  }

  //
  // Search highlighting
  //

  _highlightSearchWords() {
    let parameters = new URLSearchParams(window.location.search);
    let highlight_words = parameters.getAll("highlight");
    if (highlight_words.length === 0) {
      // Nothing to highlight.
      return;
    }

    // Highlight content within `role="main"`
    // TODO: implement this.
    //   window.setTimeout(function () {
    //     $.each(terms, function () {
    //       element.highlightText(this.toLowerCase(), "highlighted");
    //     });
    //   }, 10);

    let searchbox = document.getElementById("searchbox");
    if (searchbox !== null) {
      searchbox.insertAdjacentHTML(
        "afterend",
        '<p class="highlight-link">' +
          '<a href="javascript:Documentation.hideSearchWords()">' +
          this.gettext("Hide Search Matches") +
          "</a>" +
          "</p>"
      );
    }
  }

  hideSearchWords() {
    let searchbox = document.getElementById("searchbox");
    if (searchbox === null) {
      return;
    }
    // Remove any .highlight-link nodes.
    searchbox
      .querySelectorAll(".highlight-link")
      .forEach((element) => element.remove());
    // Remove all the highlighted classes.
    document
      .querySelector('[role="main"]')
      .querySelectorAll("span.highlighted")
      .forEach((element) => element.classList.remove("highlighted"));
  }

  //
  // Domain Index stuff
  //

  /** Initialize domain index toggle buttons
   */
  _initDomainIndex() {
    let toggle = (element) => {
      if (window.getComputedStyle(element).display === "block") {
        element.style.display = "none";
      } else {
        element.style.display = "block";
      }
    };

    let toggle_images = document.querySelectorAll('[role="main"] img.toggler');

    toggle_images.forEach((element) => {
      element.addEventListener("click", () => {
        let src = element.getAttribute("src");
        let id_number = element.getAttribute("id").substr(7);

        // Toggle visibility.
        toggle(document.querySelector(`tr.cg-${id_number}`));
        // Toggle icon.
        let new_src =
          src.substr(-9) === "minus.png"
            ? src.substr(0, src.length - 9) + "plus.png"
            : src.substr(0, src.length - 8) + "minus.png";
        element.setAttribute("src", new_src);
      });
    });

    if (DOCUMENTATION_OPTIONS.COLLAPSE_INDEX) {
      toggle_images.forEach((e) => e.click());
    }
  }

  //
  // Keyboard handling
  //
  _keyListener(event) {
    let tag_name = document.activeElement.tagName;
    if (
      tag_name === "TEXTAREA" ||
      tag_name === "INPUT" ||
      tag_name === "SELECT" ||
      tag_name === "BUTTON"
    ) {
      // Don't handle keyboard presses in input elements.
      return;
    }
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
      // Don't handle keyboard presses with modifier keys.
      return;
    }

    // Actual event handling
    if (event.keyCode == 37) {
      // Left
      let link_prev = document.querySelector('link[rel="prev"]');
      if (link_prev !== null && link_prev.href !== "") {
        window.location.href = link_prev.href;
      }
    } else if (event.keyCode == 39) {
      // Right
      let link_next = document.querySelector('link[rel="next"]');
      if (link_next !== null && link_next.href !== "") {
        window.location.href = link_next.href;
      }
    }
  }

  _initKeyListeners() {
    document.addEventListener("keydown", this._keyListener);
  }

  //
  // Misc
  //

  /**
   * Workaround for a weird Firefox bug around anchor handling.
   * See https://bugzilla.mozilla.org/show_bug.cgi?id=645075 for details.
   */
  _workaroundForFirefoxAnchorBug() {
    document.location.href += "";
  }
}

// We expose a single object, for public use.
var Documentation = new _SphinxDocumentation();

// a common short alias
_ = Documentation.gettext;

if (
  document.readyState === "complete" ||
  document.readyState === "interactive"
) {
  setTimeout(Documentation._page_loaded, 1);
} else {
  document.addEventListener("DOMContentLoaded", Documentation._page_loaded);
}
