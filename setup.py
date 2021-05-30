from setuptools import setup, find_packages

def _get_readme():
    with open('README.md', encoding='utf-8') as fp:
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
    'discord reactions'
    'discord embed',
    'discord menu'
    'reaction menu',
    'paginator',
    'pagination'
    'embed menu',
    'embed reaction menu',
    'embed paginator'
]

details = {
    'Changelog' : 'https://github.com/Defxult/reactionmenu/blob/main/CHANGELOG.md'
}

setup(
    author='Defxult#8269',
    name='reactionmenu',
    version='1.0.9', 
    description='A package to create a discord.py reaction menu (paginator). If your discord.py version is 1.5.0+, intents are required',
    url='https://github.com/Defxult/reactionmenu',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages(),
    install_requires=['discord.py>=1.4.0']
)
