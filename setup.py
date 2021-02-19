from setuptools import setup, find_packages

def _get_readme():
    with open('README.md') as fp:
        return fp.read()

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

tags = [
    'discord',
    'discord.py',
    'discord paginator',
    'discord reaction menu',
    'discord embed',
    'reaction menu',
    'paginator',
    'embed menu',
    'embed reaction menu',
    'embed paginator'
]

details = {
    'Github Repo' : 'https://github.com/Defxult/reactionmenu',
    'Github Issues' : 'https://github.com/Defxult/reactionmenu/issues'
}

setup(
    author='Defxult#8269',
    name='reactionmenu',
    description='A package to create a discord.py reaction menu. If your discord.py version is 1.5.0+, intents are required',
    version='1.0.2', 
    url='https://github.com/Defxult',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages(),
    install_requires=['discord.py>=1.4.0']
)