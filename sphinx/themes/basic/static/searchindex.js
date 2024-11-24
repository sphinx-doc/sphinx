req = new XMLHttpRequest();
req.open("GET", "searchindex.json", false);
req.send(null);
Search.setIndex(req.responseText);
