/*
 * This script contains the language-specific data used by searchtools.js,
 * namely the list of stopwords, stemmer, scorer and splitter.
 */

const stopwords = new Set([]);
window.stopwords = stopwords; // Export to global scope

/* Non-minified versions are copied as separate JavaScript files, if available */

/**
 * Dummy stemmer for languages without stemming rules.
 */
var Stemmer = function () {
  this.stemWord = function (w) {
    return w;
  };
};
