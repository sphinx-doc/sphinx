/*
 * searchtools.js
 * ~~~~~~~~~~~~~~~~
 *
 * Sphinx JavaScript utilities for the full-text search.
 *
 * :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
 * :license: BSD, see LICENSE for details.
 *
 */

/**
 * select a different prefix for underscore
 */
$u = _.noConflict();

/**
 * Simple result scoring code.
 */
const Scorer = {
  // Implement the following function to further tweak the score for each result
  // The function takes a result array [filename, title, anchor, descr, score]
  // and returns the new score.
  /*
  score: result => {
    const [filename, title, anchor, descr, score] = result
    return score
  },
  */

  // query matches the full name of an object
  objNameMatch: 11,
  // or matches in the last dotted part of the object name
  objPartialMatch: 6,
  // Additive scores depending on the priority of the object
  objPrio: {
    0:  15,  // used to be importantResults
    1:  5,   // used to be objectResults
    2: -5    // used to be unimportantResults
  },
  //  Used when the priority is not in the mapping.
  objPrioDefault: 0,

  // query found in title
  title: 15,
  partialTitle: 7,
  // query found in terms
  term: 5,
  partialTerm: 2
};

const _removeChildren = element => {while (element.lastChild) element.removeChild(element.lastChild);}

/**
 * See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions#escaping
 */
const _escapeRegExp = string => string.replace(/[.*+\-?^${}()|[\]\\]/g, "\\$&"); // $& means the whole matched string

const _displayItem = (item, highlightTerms, searchTerms) => {
  const docBuilder = DOCUMENTATION_OPTIONS.BUILDER
  const docUrlRoot = DOCUMENTATION_OPTIONS.URL_ROOT
  const docFileSuffix = DOCUMENTATION_OPTIONS.FILE_SUFFIX
  const docLinkSuffix = DOCUMENTATION_OPTIONS.LINK_SUFFIX
  const docHasSource = DOCUMENTATION_OPTIONS.HAS_SOURCE

  const [docname, title, anchor, descr, score, filename] = item

  let listItem = document.createElement("li")
  let requestUrl;
  let linkUrl;
  if (docBuilder === "dirhtml") {
    // dirhtml builder
    let dirname = docname + "/";
    if (dirname.match(/\/index\/$/)) dirname = dirname.substring(0, dirname.length - 6);
    else if (dirname === "index/") dirname = "";
    requestUrl = docUrlRoot + dirname;
    linkUrl = requestUrl
  } else {
    // normal html builders
    requestUrl = docUrlRoot + docname + docFileSuffix;
    linkUrl = docname + docLinkSuffix;
  }
  const params = new URLSearchParams()
  params.set("highlight", highlightTerms.join(" "))
  let linkEl = listItem.appendChild(document.createElement("a"))
  linkEl.href = linkUrl + "?" + params.toString() + anchor
  linkEl.innerHTML = title
  if (descr) listItem.appendChild(document.createElement("span")).innerText = " (" + descr + ")"
  else if (docHasSource) fetch(requestUrl)
      .then(responseData => responseData.text())
      .then(data => {if (data) listItem.appendChild(Search.makeSearchSummary(data, searchTerms, highlightTerms));})
  Search.output.appendChild(listItem);
}
const _finishSearch = (resultCount) => {
  Search.stopPulse();
  Search.title.innerText = _("Search Results");
  if (!resultCount)
    Search.status.innerText = _("Your search did not match any documents. Please make sure that all words are spelled correctly and that you've selected enough categories.");
  else
    Search.status.innerText = _(`Search finished, found ${resultCount} page(s) matching the search query.`)
}
const _displayNextItem = (results, resultCount, highlightTerms, searchTerms) => {
  // results left, load the summary and display it
  // this is intended to be dynamic (don't sub resultsCount)
  if (results.length) {
    _displayItem(results.pop(), highlightTerms, searchTerms)
    setTimeout(() => _displayNextItem(results, resultCount, highlightTerms, searchTerms), 5)
  }
  // search finished, update title and status message
  else _finishSearch(resultCount)
};

/**
 * Search Module
 */
const Search = {

  _index: null,
  _queued_query: null,
  _pulse_status: -1,

  htmlToText: htmlString => {
    const htmlElement = document.createRange().createContextualFragment(htmlString)
    _removeChildren(htmlElement.querySelectorAll(".headerlink"));
    const docContent = htmlElement.querySelector('[role="main"]');
    if (docContent !== undefined) return docContent.textContent
    console.warn("Content block not found. Sphinx search tries to obtain it " +
        "via '[role=main]'. Could you check your theme or template.");
    return "";
  },

  init: () => {
    const query = new URLSearchParams(window.location.search).get("q");
    document.querySelectorAll('input[name="q"]').forEach(el => el.value = query)
    if (query) this.performSearch(query);
  },

  loadIndex : url => document.body.appendChild(document.createElement("script")).src = url,

  setIndex: index => {
    this._index = index;
    if (this._queued_query !== null) {
      this._queued_query = null;
      Search.query(this._queued_query);
    }
  },

  hasIndex: () => this._index !== null,

  deferQuery: query => this._queued_query = query,

  stopPulse: () => this._pulse_status = 0,

  startPulse: () => {
    if (this._pulse_status >= 0) return

    const pulse = () => {
      Search._pulse_status = (Search._pulse_status + 1) % 4
      Search.dots.innerText = ".".repeat(Search._pulse_status)
      if (Search._pulse_status >= 0) window.setTimeout(pulse, 500)
    }
    pulse()
  },

  /**
   * perform a search for something (or wait until index is loaded)
   */
  performSearch: query => {
    // create the required interface elements
    const searchText = document.createElement("h2");
    searchText.textContent = _("Searching");
    const searchSummary = document.createElement("p");
    searchSummary.classList.add("search-summary")
    searchSummary.innerText = ""
    const searchList = document.createElement("ul");
    searchList.classList.add("search")

    const out = document.getElementById("search-results");
    this.title = out.appendChild(searchText);
    this.dots = this.title.appendChild(document.createElement("span"))
    this.status = out.appendChild(searchSummary);
    this.output = out.appendChild(searchList);

    document.getElementById("search-progress").innerText = _("Preparing search...")
    this.startPulse();

    // index already loaded, the browser was quick!
    if (this.hasIndex()) this.query(query)
    else this.deferQuery(query)
  },

  /**
   * execute search (requires search index to be loaded)
   */
  query: query => {
    // stem the search terms and add them to the correct list
    const stemmer = new Stemmer();
    const searchTerms = [];
    const excluded = [];
    const highlightTerms = [];
    const objectTerms = query.toLowerCase().trim().split(/\s+/)
    query.trim().split(/\s+/).forEach(queryTerm => {
      const queryTermLower = queryTerm.toLowerCase()

      // maybe skip this "word"
      // stopwords array is from language_data.js
      if (stopwords.indexOf(queryTermLower) !== -1 || queryTerm.match(/^\d+$/)) return
      
      // stem the word
      let word = stemmer.stemWord(queryTermLower)
      // prevent stemmer from cutting word smaller than two chars
      if (word.length < 3 && queryTerm.length >= 3) {
        word = queryTerm;
      }
      // select the correct list
      if (word[0] === "-") {
        if (!excluded.includes(word.substr(1))) excluded.push(word.substr(1));  // only add if not already in the list
      } else {
        if (!searchTerms.includes(word)) searchTerms.push(word);  // only add if not already in the list
        highlightTerms.push(queryTermLower)
      }
    })

    // console.debug("SEARCH: searching for:");
    // console.info("required: ", searchTerms);
    // console.info("excluded: ", excluded);

    // prepare search
    const terms = this._index.terms;
    const titleTerms = this._index.titleterms;

    // array of [docname, title, anchor, descr, score, filename]
    let results = [];
    _removeChildren(document.getElementById("search-progress"))

    // lookup as object
    objectTerms.forEach((term, i) => {
      const otherTerms = [...objectTerms.slice(0, i), ...objectTerms.slice(i + 1)]
      results.push(...this.performObjectSearch(term, otherTerms))
    })

    // lookup as search terms in fulltext
    results.push(...this.performTermsSearch(searchTerms, excluded, terms, titleTerms))

    // let the scorer override scores with a custom scoring function
    if (Scorer.score) results.forEach(item => item[4] = Scorer.score(item))

    // now sort the results by score (in opposite order of appearance, since the
    // display function below uses pop() to retrieve items) and then
    // alphabetically
    results.sort((a, b) => {
      const leftScore = a[4];
      const rightScore = b[4];
      if (leftScore === rightScore) {
        // same score: sort alphabetically
        const leftTitle = a[1].toLowerCase();
        const rightTitle = b[1].toLowerCase();
        if (leftTitle === rightTitle) return 0
        return (leftTitle > rightTitle) ? -1 : 1  // inverted is intentional
      }
      return (leftScore > rightScore) ? 1 : -1
    })

    // for debugging
    //Search.lastresults = results.slice();  // a copy
    // console.info("search results:", Search.lastresults);

    // print the results
    _displayNextItem(results, results.length, highlightTerms, searchTerms);
  },

  /**
   * search for object names
   */
  performObjectSearch: (object, otherTerms) => {
    const filenames = this._index.filenames;
    const docNames = this._index.docnames;
    const objects = this._index.objects;
    const objNames = this._index.objnames;
    const titles = this._index.titles;

    let i;
    const results = [];

    const objectSearchCallback = (prefix, name) => {
      const fullname = (prefix ? prefix + "." : "") + name
      const fullnameLower = fullname.toLowerCase()
      if (fullnameLower.indexOf(object) < 0) return

      let score = 0;
      const parts = fullnameLower.split(".");

      // check for different match types: exact matches of full name or
      // "last name" (i.e. last dotted part)
      if (fullnameLower === object || parts.slice(-1)[0] === object) score += Scorer.objNameMatch
      else if (parts.slice(-1)[0].indexOf(object) > -1) score += Scorer.objPartialMatch  // matches in last name
      const match = objects[prefix][name];
      const objName = objNames[match[1]][2];
      const title = titles[match[0]];

      // If more than one term searched for, we require other words to be
      // found in the name/title/description
      if (otherTerms.length > 0) {
        const haystack = `${prefix} ${name} ${objName} ${title}`.toLowerCase()
        if (!otherTerms.every(otherTerm => haystack.indexOf(otherTerm) > -1)) return
      }

      let anchor = match[3];
      if (anchor === "") anchor = fullname;
      else if (anchor === "-") anchor = objNames[match[1]][1] + "-" + fullname;

      const descr = objName + _(", in ") + title;

      // add custom score for some objects according to scorer
      if (Scorer.objPrio.hasOwnProperty(match[2])) score += Scorer.objPrio[match[2]];
      else score += Scorer.objPrioDefault

      results.push([docNames[match[0]], fullname, "#" + anchor, descr, score, filenames[match[0]]]);
    }
    objects.forEach(prefix => objects[prefix].forEach(name => objectSearchCallback(prefix, name)))
    return results;
  },

  /**
   * See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions
   */
  escapeRegExp : function(string) {
    return string.replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
  },

  /**
   * search for full-text terms in the index
   */
  performTermsSearch : function(searchterms, excluded, terms, titleterms) {
    var docnames = this._index.docnames;
    var filenames = this._index.filenames;
    var titles = this._index.titles;

    var i, j, file;
    var fileMap = {};
    var scoreMap = {};
    var results = [];

    // perform the search on the required terms
    for (i = 0; i < searchterms.length; i++) {
      var word = searchterms[i];
      var files = [];
      var _o = [
        {files: terms[word], score: Scorer.term},
        {files: titleterms[word], score: Scorer.title}
      ];
      // add support for partial matches
      if (word.length > 2) {
        var word_regex = this.escapeRegExp(word);
        for (var w in terms) {
          if (w.match(word_regex) && !terms[word]) {
            _o.push({files: terms[w], score: Scorer.partialTerm})
          }
        }
        for (var w in titleterms) {
          if (w.match(word_regex) && !titleterms[word]) {
              _o.push({files: titleterms[w], score: Scorer.partialTitle})
          }
        }
      }

      // no match but word was a required one
      if ($u.every(_o, function(o){return o.files === undefined;})) {
        break;
      }
      // found search word in contents
      $u.each(_o, function(o) {
        var _files = o.files;
        if (_files === undefined)
          return

        if (_files.length === undefined)
          _files = [_files];
        files = files.concat(_files);

        // set score for the word in each file to Scorer.term
        for (j = 0; j < _files.length; j++) {
          file = _files[j];
          if (!(file in scoreMap))
            scoreMap[file] = {};
          scoreMap[file][word] = o.score;
        }
      });

      // create the mapping
      for (j = 0; j < files.length; j++) {
        file = files[j];
        if (file in fileMap && fileMap[file].indexOf(word) === -1)
          fileMap[file].push(word);
        else
          fileMap[file] = [word];
      }
    }

    // now check if the files don't contain excluded terms
    for (file in fileMap) {
      var valid = true;

      // check if all requirements are matched
      var filteredTermCount = // as search terms with length < 3 are discarded: ignore
        searchterms.filter(function(term){return term.length > 2}).length
      if (
        fileMap[file].length != searchterms.length &&
        fileMap[file].length != filteredTermCount
      ) continue;

      // ensure that none of the excluded terms is in the search result
      for (i = 0; i < excluded.length; i++) {
        if (terms[excluded[i]] == file ||
            titleterms[excluded[i]] == file ||
            $u.contains(terms[excluded[i]] || [], file) ||
            $u.contains(titleterms[excluded[i]] || [], file)) {
          valid = false;
          break;
        }
      }

      // if we have still a valid result we can add it to the result list
      if (valid) {
        // select one (max) score for the file.
        // for better ranking, we should calculate ranking by using words statistics like basic tf-idf...
        var score = $u.max($u.map(fileMap[file], function(w){return scoreMap[file][w]}));
        results.push([docnames[file], titles[file], '', null, score, filenames[file]]);
      }
    }
    return results;
  },

  /**
   * helper function to return a node containing the
   * search summary for a given text. keywords is a list
   * of stemmed words, highlightWords is the list of normal, unstemmed
   * words. the first one is used to find the occurrence, the
   * latter for highlighting it.
   */
  makeSearchSummary: (htmlText, keywords, highlightWords) => {
    const text = Search.htmlToText(htmlText).toLowerCase()
    if (text === "") return null

    const actualStartPosition = keywords.map(k => text.indexOf(k.toLowerCase())).filter(i => (i > -1)).slice(-1)[0]
    const startWithContext = Math.max(actualStartPosition - 120, 0)
    const top = (startWithContext === 0) ? "" : "..."
    const tail = (startWithContext + 240 < text.length) ? "..." : ""
    let summary = document.createElement("div")
    summary.classList.add("context")
    summary.innerText = top + text.substr(startWithContext, 240).trim() + tail
    highlightWords.forEach(highlightWord => _highlightText(summary, highlightWord, "highlighted"))
    return summary
  }
};

_ready(Search.init)
