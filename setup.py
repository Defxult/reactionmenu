from setuptools import setup, find_packages

def _get_readme():
    with open('README.md', encoding='utf-8') as fp:
        return fp.read()

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

tags = [
    'buttons',
    'buttons paginator',
    'buttons menu',
    'discord',
    'discord.py',
    'components',
    'components paginator',
    'components menu',
    'discord components',
    'discord components menu',
    'discord buttons',
    'discord buttons paginator',
    'discord buttons menu',
    'discord paginator',
    'discord pagination',
    'discord reaction menu',
    'discord reactions',
    'discord embed',
    'discord menu',
    'discord interactions',
    'embed menu',
    'embed reaction menu',
    'embed paginator',
    'interactions',
    'interactions menu',
    'paginator',
    'pagination',
    'pagination menu',
    'pycord',
    'py-cord',
    'reaction menu'
]

details = {
    'Changelog' : 'https://github.com/Defxult/reactionmenu/blob/main/CHANGELOG.md'
}

setup(
    author='Defxult#8269',
    name='reactionmenu',
    version='3.0.1',
    description='A library to create a discord paginator. Supports pagination with Discords Buttons feature and reactions.',
    url='https://github.com/Defxult/reactionmenu',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages()
    #! for release, install requires needs to be here
)
