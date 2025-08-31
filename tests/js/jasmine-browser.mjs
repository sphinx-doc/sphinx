export default {
  srcDir: ".",
  srcFiles: [
    "sphinx/themes/basic/static/doctools.js",
    "sphinx/themes/basic/static/searchtools.js",
    "sphinx/themes/basic/static/sphinx_highlight.js",
    "tests/js/fixtures/**/*.js",
    "tests/js/documentation_options.js",
    "tests/js/language_data.js",
  ],
  specDir: "tests/js",
  specFiles: ["**/*.spec.js"],
  helpers: [],
  env: {
    stopSpecOnExpectationFailure: false,
    stopOnSpecFailure: false,
    random: true,
  },

  listenAddress: "127.0.0.1",
  hostname: "127.0.0.1",

  browser: {
    name: "headlessFirefox",
  },
};
