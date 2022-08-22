from typing import Final, Literal
from setuptools import find_packages, setup
from reactionmenu import __source__

def _get_readme() -> str:
    with open('README.md', encoding='utf-8') as fp:
        return fp.read()

def _version_info() -> str:
    version = (3, 1, 0)
    release_level: Literal['alpha', 'beta', 'rc', 'final'] = 'rc'
        
    BASE: Final[str] = '.'.join([str(n) for n in version])

    if release_level == 'final':
        return BASE
    else:
        # try and get the last commit hash for a more precise version, if it fails, just use the basic version
        try:
            import subprocess
            p = subprocess.Popen(['git', 'ls-remote', __source__, 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            short_hash = out.decode('utf-8')[:7]
            p.kill()
            return BASE + f"{release_level}+{short_hash}"
        except Exception:
            print('reactionmenu notification: An error occurred when attempting to get the last commit ID of the repo for a more precise version of the library. Returning base development version instead.')
            return BASE + release_level

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
    'discord.py 2.0',
    'd.py',
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
    'interactions paginator',
    'menus',
    'paginator',
    'pagination',
    'pagination menu',
    'reaction menu'
]

details = {
    'Changelog' : 'https://github.com/Defxult/reactionmenu/blob/main/CHANGELOG.md'
}

setup(
    author='Defxult#8269',
    name='reactionmenu',
    version=_version_info(),
    description='A library to create a discord.py 2.0+ paginator. Supports pagination with buttons, reactions, and category selection using selects.',
    url='https://github.com/Defxult/reactionmenu',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages(),
    install_requires=['discord.py>=2.0.0']
)
