import os
import sys
from setuptools import setup, find_packages

def read(filename):
    with open(filename, encoding='utf-8') as f:
        return f.read()

def get_version():
    version_file = os.path.join('wilayah_indonesia', '__init__.py')
    with open(version_file, encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

def build_package():
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
        
    os.system("python setup.py sdist bdist_wheel")
    if os.system("twine check dist/*"):
        print("twine check failed. Packages might be outdated.")
        print("Try using `pip install -U twine wheel`.\nExiting.")
        sys.exit()

version = get_version()

if sys.argv[-1] == 'publish':
    build_package()
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()
 
setup(
    name='django-wilayah-indonesia',
    version=version,
    url='https://github.com/irfanpule/wilayah_indonesia',
    license='MIT',
    description='A simple Django app to provide Indonesia region',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='irfanpule',
    author_email='irfan.pule2@gmail.com',
    packages=find_packages(exclude=['tests*', 'demo*']),
    include_package_data=True,
    install_requires=[
        'django>=4.2',
        'django-select2>=8.4.0'
    ],
    python_requires=">=3.6",
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
    ],
)