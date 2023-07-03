import pathlib

extensions = [
    'sphinx.ext.javadoctest',
]

project = 'Test project for javadoctest with Java Maven'
root_doc = 'maven'
javadoctest_config = {
    'flavor': 'java_with_maven',
    'path': pathlib.Path(__file__).parent / 'example',
}
