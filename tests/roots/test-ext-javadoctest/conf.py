extensions = [
    'sphinx.ext.javadoctest',
]

project = 'test project for javadoctest'
root_doc = 'javadoctest'
javadoctest_global_setup = '''
boolean docker = true;
'''
javadoctest_config = {
    'flavor': 'java',
}
