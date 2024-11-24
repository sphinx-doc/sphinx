window.fetch("searchindex.json").then(response => response.json()).then(Search.setIndex);
