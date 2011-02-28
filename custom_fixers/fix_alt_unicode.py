from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import Name

class FixAltUnicode(BaseFix):
    PATTERN = """
    func=funcdef< 'def' name='__unicode__'
                  parameters< '(' NAME ')' > any+ >
    """

    def transform(self, node, results):
        name = results['name']
        name.replace(Name('__str__', prefix=name.prefix))
