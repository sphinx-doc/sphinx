import pathlib

extensions = [
    "sphinx.ext.javadoctest",
]

project = 'Test project for javadoctest with Java Maven'

javadoc_options = {
    'flavor': 'java_with_maven',
    'path': pathlib.Path(__file__).parent / 'example',
}
