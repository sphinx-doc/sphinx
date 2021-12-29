/*
 * doctools.js
 * ~~~~~~~~~~~
 *
 * Base JavaScript utilities for all Sphinx HTML documentation.
 *
 * :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
 * :license: BSD, see LICENSE for details.
 *
 */
"use strict";

const _ready = callback => {
  if (document.readyState !== "loading") return callback()
  document.addEventListener("DOMContentLoaded", callback)
}

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
const _highlightText = (thisNode, text, className) => {
  let addItems = [];
  _highlight(thisNode, addItems, text, className)
  for (let i = 0; i < addItems.length; ++i) addItems[i].parent.insertAdjacentHTML("beforebegin", addItems[i].target)
}

/**
 * Small JavaScript module for the documentation.
 */
const Documentation = {

  init : () => {
    this.highlightSearchWords();
    this.initDomainIndexTable();
    if (DOCUMENTATION_OPTIONS.NAVIGATION_WITH_KEYS) this.initOnKeyListeners()
  },

  /**
   * i18n support
   */
  TRANSLATIONS : {},
  PLURAL_EXPR : n => (n === 1) ? 0 : 1,
  LOCALE : "unknown",

  // gettext and ngettext don't access this so that the functions
  // can safely bound to a different name (_ = Documentation.gettext)
  gettext : string => {
    const translated = Documentation.TRANSLATIONS[string];
    switch (typeof translated) {
      case "undefined": return string // no translation
      case "string": return translated  // translation exists
      default: return translated[0]  // (singular, plural) translation tuple exists
    }
  },

  ngettext : (singular, plural, n) => {
    const translated = Documentation.TRANSLATIONS[singular];
    if (typeof translated !== "undefined") return translated[Documentation.PLURAL_EXPR(n)];
    return (n === 1) ? singular : plural;
  },

  addTranslations : catalog => {
    Object.assign(this.TRANSLATIONS, catalog.messages)
    this.PLURAL_EXPR = new Function("n", `return (${catalog.plural_expr})`)
    this.LOCALE = catalog.locale
  },

  /**
   * highlight the search words provided in the url in the text
   */
  highlightSearchWords: () => {
    const highlight = new URLSearchParams(window.location.search).get("highlight")
    const terms = (highlight) ? highlight.split(/\s+/) : [];
    if (terms.length === 0) return  // nothing to do

    let body = document.querySelectorAll("div.body");
    if (!body.length) body = document.querySelector("body")
    window.setTimeout(() => {
      terms.forEach(term => _highlightText(body, term.toLowerCase(), "highlighted"))
    }, 10);

    document.getElementById("searchbox").appendChild(
      document.createRange().createContextualFragment(
          '<p class="highlight-link">'
          +'<a href="javascript:Documentation.hideSearchWords()">'
          + this.gettext("Hide Search Matches")
          + "</a></p>"));
  },

  /**
   * helper function to hide the search marks again
   */
  hideSearchWords: () => {
    document.querySelectorAll("#searchbox .highlight-link").forEach(el => el.remove())
    document.querySelectorAll("span.highlighted").forEach(el => el.classList.remove("highlighted"))
  },

  /**
   * Initialise the domain index toggle buttons
   */
  initDomainIndexTable: () => {
    const toggler = el => {
      const idNumber = el.id.substr(7)
      const toggledRows = document.querySelectorAll(`tr.cg-${idNumber}`)
      if (el.src.substr(-9) === "minus.png") {
        el.src = `${el.src.substr(0, el.src.length - 9)}plus.png`
        toggledRows.forEach(el => el.style.display = "none")
      } else {
        el.src = `${el.src.substr(0, el.src.length - 8)}minus.png`
        toggledRows.forEach(el => el.style.display = "")
      }
    }
    const togglerElements = document.querySelectorAll("img.toggler")
    togglerElements.forEach(el => el.addEventListener("click", event => toggler(event.currentTarget)))
    togglerElements.forEach(el => el.style.display = "")
    if (DOCUMENTATION_OPTIONS.COLLAPSE_INDEX) togglerElements.forEach(toggler)
  },

  /**
   * make the url absolute
   */
  makeURL : relativeURL => `${DOCUMENTATION_OPTIONS.URL_ROOT}/${relativeURL}`,

  /**
   * get the current relative url
   */
  getCurrentURL: () => window.location.pathname.split(/\//).slice(-1)[0],
  // the original (jQuery) function was broken (the check would always return false). Fixing it would represent a breaking change.
  // getCurrentURL: () => window.location.pathname.split(/\//).slice(DOCUMENTATION_OPTIONS.URL_ROOT.split(/\//).filter(item => item === "..").length + 1).join("/"),

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
const _ = Documentation.gettext;

_ready(Documentation.init);
