


project_name = 'foo'
import_statements = ['import pandas as pd', 'import numpy as np', 'from os.path import join']

with open('{}.py'.format(project_name), 'w') as f:
    for import_statement in import_statements:
        f.write('{}\n'.format(import_statement))