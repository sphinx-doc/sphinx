import pathlib

extensions = [
    'sphinx.ext.javadoctest',
]

project = 'Test project for javadoctest with Java Maven'
root_doc = 'maven'
java_doctest_config = {
    'flavor': 'java_with_maven',
    'path': pathlib.Path(__file__).parent / 'example',
}
