from distutils.core import setup
from Cython.Build import cythonize
from os import listdir

for file in listdir('.'):
    if file[-4:] == '.pyx':
        setup(ext_modules = cythonize(file))
