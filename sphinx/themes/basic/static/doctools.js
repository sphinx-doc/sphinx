/*
 * doctools.js
 * ~~~~~~~~~~~
 *
 * Sphinx JavaScript utilities for all documentation.
 *
 * :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
 * :license: BSD, see LICENSE for details.
 *
 */

/**
 * make the code below compatible with browsers without
 * an installed firebug like debugger
if (!window.console || !console.firebug) {
  var names = ["log", "debug", "info", "warn", "error", "assert", "dir",
    "dirxml", "group", "groupEnd", "time", "timeEnd", "count", "trace",
    "profile", "profileEnd"];
  window.console = {};
  for (var i = 0; i < names.length; ++i)
    window.console[names[i]] = function() {};
}
 */

/**
 * highlight a given string on a node by wrapping it in
 * span elements with the given class name.
 */
const _highlight = (node, addItems, text, className) => {
  if (node.nodeType === Node.TEXT_NODE) {
    const val = node.nodeValue;
    const parent = node.parentNode
    const pos = val.toLowerCase().indexOf(text);
    if (pos >= 0
        && !parent.classList.contains(className)
        && !parent.classList.contains("nohighlight")
    ) {
      let span;
      const closestNode = parent.closest("body, svg, foreignObject");
      const isInSVG = closestNode && closestNode.matches("svg")
      if (isInSVG) {
        span = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      } else {
        span = document.createElement("span");
        span.classList.add(className);
      }
      span.appendChild(document.createTextNode(val.substr(pos, text.length)));
      parent.insertBefore(span, parent.insertBefore(
          document.createTextNode(val.substr(pos + text.length)),
          node.nextSibling));
      node.nodeValue = val.substr(0, pos);
      if (isInSVG) {
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        const bbox = parent.getBBox();
        rect.x.baseVal.value = bbox.x;
        rect.y.baseVal.value = bbox.y;
        rect.width.baseVal.value = bbox.width;
        rect.height.baseVal.value = bbox.height;
        rect.setAttribute("class", className);
        addItems.push({
          "parent": parent,
          "target": rect});
      }
    }
  }
  else if (!node.matches("button, select, textarea")) {
    node.childNodes.forEach(el => _highlight(el, addItems, text, className));
  }
};
const highlightText = (thisNode, text, className) => {
  let addItems = [];
  _highlight(thisNode, addItems, text, className)
  for (let i = 0; i < addItems.length; ++i) addItems[i].parent.insertAdjacentHTML("beforebegin", addItems[i].target)
}

/**
 * Small JavaScript module for the documentation.
 */
var Documentation = {

  init : function() {
    this.highlightSearchWords();
    this.initIndexTable();
    if (DOCUMENTATION_OPTIONS.NAVIGATION_WITH_KEYS) {
      this.initOnKeyListeners();
    }
  },

  /**
   * i18n support
   */
  TRANSLATIONS : {},
  PLURAL_EXPR : function(n) { return n === 1 ? 0 : 1; },
  LOCALE : 'unknown',

  // gettext and ngettext don't access this so that the functions
  // can safely bound to a different name (_ = Documentation.gettext)
  gettext : function(string) {
    var translated = Documentation.TRANSLATIONS[string];
    if (typeof translated === 'undefined')
      return string;
    return (typeof translated === 'string') ? translated : translated[0];
  },

  ngettext : function(singular, plural, n) {
    var translated = Documentation.TRANSLATIONS[singular];
    if (typeof translated === 'undefined')
      return (n == 1) ? singular : plural;
    return translated[Documentation.PLURALEXPR(n)];
  },

  addTranslations : function(catalog) {
    for (var key in catalog.messages)
      this.TRANSLATIONS[key] = catalog.messages[key];
    this.PLURAL_EXPR = new Function('n', 'return +(' + catalog.plural_expr + ')');
    this.LOCALE = catalog.locale;
  },

  /**
   * add context elements like header anchor links
   */
  addContextElements : function() {
    $('div[id] > :header:first').each(function() {
      $('<a class="headerlink">\u00B6</a>').
      attr('href', '#' + this.id).
      attr('title', _('Permalink to this headline')).
      appendTo(this);
    });
    $('dt[id]').each(function() {
      $('<a class="headerlink">\u00B6</a>').
      attr('href', '#' + this.id).
      attr('title', _('Permalink to this definition')).
      appendTo(this);
    });
  },

  /**
   * highlight the search words provided in the url in the text
   */
  highlightSearchWords : function() {
    var highlight = new URLSearchParams(document.location.search).get("highlight")
    var terms = (highlight) ? highlight.split(/\s+/) : [];
    if (terms.length) {
      let body = document.querySelectorAll("div.body");
      if (!body.length) body = document.querySelector("body")
      window.setTimeout(() => {
        terms.forEach(term => highlightText(body, term.toLowerCase(), 'highlighted'))
      }, 10);
      $('<p class="highlight-link"><a href="javascript:Documentation.' +
        'hideSearchWords()">' + _('Hide Search Matches') + '</a></p>')
          .appendTo($('#searchbox'));
    }
  },

  /**
   * init the domain index toggle buttons
   */
  initIndexTable : function() {
    var togglers = $('img.toggler').click(function() {
      var src = $(this).attr('src');
      var idnum = $(this).attr('id').substr(7);
      $('tr.cg-' + idnum).toggle();
      if (src.substr(-9) === 'minus.png')
        $(this).attr('src', src.substr(0, src.length-9) + 'plus.png');
      else
        $(this).attr('src', src.substr(0, src.length-8) + 'minus.png');
    }).css('display', '');
    if (DOCUMENTATION_OPTIONS.COLLAPSE_INDEX) {
        togglers.click();
    }
  },

  /**
   * helper function to hide the search marks again
   */
  hideSearchWords : function() {
    $('#searchbox .highlight-link').fadeOut(300);
    $('span.highlighted').removeClass('highlighted');
  },

  /**
   * make the url absolute
   */
  makeURL : function(relativeURL) {
    return DOCUMENTATION_OPTIONS.URL_ROOT + '/' + relativeURL;
  },

  /**
   * get the current relative url
   */
  getCurrentURL: () => document.location.pathname.split(/\//).slice(-1)[0],
  // the original (jQuery) function was broken (the check would always return false). Fixing it would represent a breaking change.
  // getCurrentURL: () => document.location.pathname.split(/\//).slice(DOCUMENTATION_OPTIONS.URL_ROOT.split(/\//).filter(item => item === "..").length + 1).join("/"),

  initOnKeyListeners: () => {
    const blacklistedElements = new Set(["TEXTAREA", "INPUT", "SELECT", "BUTTON"])
    document.addEventListener("keydown",event => {
      if (blacklistedElements.has(document.activeElement.tagName)) return  // bail for input elements
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return  // bail with special keys
      if (event.key === "ArrowLeft") {
        const prevLink = document.querySelector('link[rel="prev"]');
        if (prevLink && prevLink.href) window.location.href = prevLink.href;
      } else if (event.key === "ArrowRight") {
        const nextLink = document.querySelector('link[rel="next"]').href
        if (nextLink && nextLink.href) window.location.href = nextLink.href;
      }
    })
  }
};

// quick alias for translations
_ = Documentation.gettext;

$(document).ready(function() {
  Documentation.init();
});
