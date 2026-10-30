from sphinx.builders.xml import XMLBuilder


class NoSmartQuotesBuilder(XMLBuilder):
    name = 'xml-no-smartquotes'

    def init(self):
        self.env.settings['smart_quotes'] = False


def setup(app):
    app.add_builder(NoSmartQuotesBuilder)
