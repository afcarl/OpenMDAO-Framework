
import sys
import os
import webbrowser

import pprint
import StringIO
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from subprocess import call
from fnmatch import fnmatch

from ordereddict import OrderedDict

from setuptools import find_packages

from openmdao.util.fileutil import build_directory, find_files
from openmdao.util.dep import PythonSourceTreeAnalyser

#from sphinx.setup_command import BuildDoc
import sphinx

# There are a number of string templates that are used to produce various
# files within the plugin distribution. These templates are stored in the
# _templates dict, with the key being the name of the file that the 
# template corresponds to.
_templates = {}

# This is the template for the file that Sphinx uses to configure itself.
# It's intended to match the conf.py for the OpenMDAO docs, so if those 
# change, this may need to be updated.
_templates['conf.py'] = '''

# This file is autogenerated during plugin_quickstart and overwritten during
# plugin_makedist. DO NOT CHANGE IT if you plan to use plugin_makedist to package
# distribution.

# -*- coding: utf-8 -*-
#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#

import sys, os

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 
              'sphinx.ext.doctest', 'sphinx.ext.todo','openmdao.util.doctools', 
              'sphinx.ext.viewcode'
      ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'%(name)s'
copyright = u'%(copyright)s'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '%(version)s'
#The short version is the one that shows up in the file when you use /version/.
# The full version, including alpha/beta/rc tags.
release = '%(release)s'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%%B %%d, %%Y'

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = 'default.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%%b %%d, %%Y'

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
#html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

html_theme = "default"

# using these theme options will make the docs share a consistent
# look with the OpenMDAO docs
html_theme_options = {
     "headtextcolor": "darkred",
     "headbgcolor": "gainsboro",
     "headfont": "Arial",
     "relbarbgcolor": "black",
     "relbartextcolor": "white",
     "relbarlinkcolor": "white",
     "sidebarbgcolor": "gainsboro",
     "sidebartextcolor": "darkred",
     "sidebarlinkcolor": "black",
     "footerbgcolor": "gainsboro",
     "footertextcolor": "darkred",
     "textcolor": "black",
     "codebgcolor": "#FFFFCC",
     "linkcolor": "darkred",
     "codebgcolor": "#ffffcc",
    }

todo_include_todos = True

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/dev': None}

autodoc_member_order = 'groupwise'

'''

# template for the top level file in the Sphinx docs for the plugin
_templates['index.rst'] = """

%(title_marker)s
%(name)s Documentation
%(title_marker)s

Contents:

.. toctree::
   :maxdepth: 2
    
   usage
   srcdocs
   pkgdocs

"""

# template for the file where the user may add specific usage documentation
# for the plugin
_templates['usage.rst'] = """

===========
Usage Guide
===========

No usage information has been provided for this plugin. Consult the
:ref:`%(name)s_src_label` section for more detail.

"""

# template for the file that packages and install the plugin using setuptools
_templates['setup.py'] = '''

#
# This file is autogenerated during plugin_quickstart and overwritten during
# plugin_makedist. DO NOT CHANGE IT if you plan to use plugin_makedist to update 
# the distribution.
#

from setuptools import setup, find_packages

kwargs = %(setup_options)s

setup(**kwargs)

'''

# template for the file that tells setuptools/distutils what extra data
# files to include in the distribution for the plugin
_templates['MANIFEST.in'] = """

graft src/%(name)s/sphinx_build/html
recursive-include src/%(name)s/test *.py

"""

# template for the README.txt file.
_templates['README.txt'] = """

README.txt file for %(name)s.

To view the Sphinx documentation for this distribution, type:

plugin_docs %(name)s

"""

# template for the setup configuration file, where all of the user
# supplied metadata is located.  This file may be hand edited by the 
# plugin developer.
_templates['setup.cfg'] = """

[metadata]
name = %(name)s
version = %(version)s
summary = 
description-file = README.txt
keywords = openmdao
home-page = 
download-url = 
author = 
author-email = 
maintainer = 
maintainer-email = 
license = 
classifier = Intended Audience :: Science/Research
    Topic :: Scientific/Engineering

requires-dist = openmdao.main
provides-dist = 
obsoletes-dist = 
requires-python = 
    >=2.6
    <2.7
requires-externals = 
project-url = 

[openmdao]
copyright =

"""


# This dict contains string templates corresponding to skeleton python source files
# for each of the recognized plugin types.  These should be updated to reflect
# best practices because most plugin developers will start with these when they
# create new plugins.
_class_templates = {}

_class_templates['openmdao.component'] = '''

from openmdao.main.api import Component
from openmdao.lib.datatypes.api import Float


# Make sure that your class has some kind of docstring. Otherwise
# the descriptions for your variables won't show up in the
# source ducumentation.
class %(classname)s(Component):
    """
    """
    # declare inputs and outputs here, for example:
    #x = Float(0.0, iotype='in', desc='description for x')
    #y = Float(0.0, iotype='out', desc='description for y')

    def execute(self):
        """ do your calculations here """
        pass
        
'''

_class_templates['openmdao.driver'] = '''

from openmdao.main.api import Driver, HasParameters
from openmdao.util.decorators import add_delegate
from openmdao.lib.datatypes.api import Float

# Make sure that your class has some kind of docstring. Otherwise
# the descriptions for your variables won't show up in the
# source ducumentation.
#@add_delegate(HasParameters)  # uncomment this to add parameter handling
class %(classname)s(Driver):
    """
    """

    # declare inputs and outputs here, for example:
    #x = Float(0.0, iotype='in', desc='description for x')
    #y = Float(0.0, iotype='out', desc='description for y')
    
    def start_iteration(self):
        super(%(classname)s, self).start_iteration()

    def continue_iteration(self):
        return super(%(classname)s, self).continue_iteration()
    
    def pre_iteration(self):
        super(%(classname)s, self).pre_iteration()
        
    def run_iteration(self):
        super(%(classname)s, self).run_iteration()

    def post_iteration(self):
        super(%(classname)s, self).post_iteration()

'''

_class_templates['openmdao.variable'] = '''
from openmdao.main.variable import Variable

class %(classname)s(Variable):

    #def __init__(self, default_value = ???, **metadata):
    #    super(%(classname)s, self).__init__(default_value=default_value,
    #                                        **metadata)

    def validate(self, object, name, value):
        pass
        # insert validation code here
        
        # in the event of an error, call
        # self.error(object, name, value)
'''

def _get_srcdocs(destdir, name):
    startdir = os.getcwd()
    srcdir = os.path.join(destdir,'src')
    if os.path.exists(srcdir):
        os.chdir(srcdir)
        try:
            srcmods = _get_src_modules('.')
        finally:
            os.chdir(startdir)
    else:
        srcmods = ["%s.%s" % (name,name)]

    contents = [
        """
.. _%s_src_label:


====================
Source Documentation
====================
        
        """ % name
        ]
    
    for mod in srcmods:
        contents.append("""
.. automodule:: %s
   :members:
   :undoc-members:
   :show-inheritance:
    
        """ % mod)

    return ''.join(contents)


def _get_pkgdocs(cfg):
    """Return a string in reST format that contains the metadata
    for the package.
    
    cfg: ConfigParser
        ConfigParser object used to read the setup.cfg file
    """
    lines = ['\n',
             '================\n',
             'Package Metadata\n',
             '================\n',
             '\n']

    metadata = {}
    if cfg.has_section('metadata'):
        metadata.update(dict([item for item in cfg.items('metadata')]))
    if cfg.has_section('openmdao'):
        metadata.update(dict([item for item in cfg.items('openmdao')]))

    tuplist = list(metadata.items())
    tuplist.sort()
    for key,value in tuplist:
        if value.strip():
            if '\n' in value:
                lines.append("- **%s**:: \n\n" % key)
                for v in [vv.strip() for vv in value.split('\n')]:
                    if v:
                        lines.append("    %s\n" % v)
                lines.append('\n')
            elif value != 'UNKNOWN':
                lines.append("- **%s:** %s\n\n" % (key, value))
        
    return ''.join(lines)


def _get_setup_options(distdir, metadata):
    # a set of names of variables that are supposed to be lists
    lists = set([
        'keywords',
        'install_requires',
        'packages',
        'classifiers',
        ])
    
    # mapping of new metadata names to old ones
    mapping = {
        'name': 'name',
        'version': 'version',
        'keywords': 'keywords',
        'summary': 'description',
        'description': 'long_description',
        'home-page': 'url',
        'download-url': 'download_url',
        'author': 'author',
        'author-email': 'author_email',
        'maintainer': 'maintainer',
        'maintainer-email': 'maintainer_email',
        'license': 'license',
        'classifier': 'classifiers',
        'requires-dist': 'install_requires',
        'entry_points': 'entry_points',
        #'py_modules': 'py_modules',
        'packages': 'packages',
        }
    
    # populate the package data with sphinx docs
    # we have to list all of the files because setuptools doesn't
    # handle nested directories very well
    pkgdir = os.path.join(distdir, 'src', metadata['name'])
    plen = len(pkgdir)+1
    sphinxdir = os.path.join(pkgdir, 'sphinx_build', 'html')
    testdir = os.path.join(pkgdir, 'test')
    pkglist = list(find_files(sphinxdir))
    pkglist.extend(list(find_files(testdir, exclude="*.py[co]")))
    pkglist = [p[plen:] for p in pkglist]
    setup_options = {
        #'packages': [metadata['name']],
        'package_data': { 
            metadata['name']: pkglist #[
            #'sphinx_build/html/*.*',
            #'sphinx_build/html/_modules/*',
            #'sphinx_build/html/_sources/*',
            #'sphinx_build/html/_static/*',
            #] 
        },
        'package_dir': {'': 'src'},
        'zip_safe': False,
        'include_package_data': True,
    }
    
    for key,val in metadata.items():
        if key in mapping:
            if isinstance(val, basestring):
                if mapping[key] in lists:
                    val = [p.strip() for p in val.split('\n') if p.strip()]
                else:
                    val = val.strip()
            setup_options[mapping[key]] = val

    return setup_options


def _pretty(obj):
    sio = StringIO.StringIO()
    pprint.pprint(obj, sio)
    return sio.getvalue()


def _get_py_files(distdir):
    def _pred(fname):
        parts = fname.split(os.sep)
        if parts[-1] in ['setup.py','__init__.py'] or 'test' in parts:
            return False
        return fname.endswith('.py')
    return list(find_files(distdir, _pred))
        

def _get_src_modules(topdir):
    topdir = os.path.abspath(os.path.expandvars(os.path.expanduser(topdir)))
    pyfiles = _get_py_files(topdir)
    noexts = [os.path.splitext(f)[0] for f in pyfiles]
    rel = [f[len(topdir)+1:] for f in noexts]
    return ['.'.join(f.split(os.sep)) for f in rel]
    

def _get_template_options(distdir, cfg, **kwargs):
    if cfg.has_section('metadata'):
        metadata = dict([item for item in cfg.items('metadata')])
    else:
        metadata = {}
    if cfg.has_section('openmdao'):
        openmdao_metadata = dict([item for item in cfg.items('openmdao')])
    else:
        openmdao.metadata = {}

    if 'packages' in kwargs:
        metadata['packages'] = kwargs['packages']
    else:
        metadata['packages'] = [metadata['name']]

    setup_options = _get_setup_options(distdir, metadata)
    
    template_options = {
        'copyright': '',
        'summary': '',
        'setup_options': _pretty(setup_options)
    }
    
    template_options.update(setup_options)
    template_options.update(openmdao_metadata)
    template_options.update(kwargs)
    
    name = template_options['name']
    version = template_options['version']
    
    template_options.setdefault('release', version)
    template_options.setdefault('title_marker', 
                                '='*(len(name)+len(' Documentation')))
        
    return template_options



test_template = """

import unittest


class %(classname)sTestCase(unittest.TestCase):

    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    # add some tests here...
    
    #def test_%(classname)s(self):
        #pass
        
if __name__ == "__main__":
    unittest.main()
    
"""


def plugin_quickstart(argv=None):
    """A command line script (plugin_quickstart) points to this.  It generates a
    directory structure for an openmdao plugin package along with Sphinx docs.
    
    usage: plugin_quickstart <dist_name> [-v <version>] [-d <dest_dir>] [-g <plugin_group>] [-c class_name]
    
    """
    
    if argv is None:
        argv = sys.argv[1:]
    
    parser = OptionParser()
    parser.usage = "plugin_quickstart <dist_name> [options]"
    parser.add_option("-v", "--version", action="store", type="string", dest='version', default='0.1',
                      help="version id of the plugin (optional)")
    parser.add_option("-c", "--class", action="store", type="string", dest='classname',
                      help="plugin class name (optional)")
    parser.add_option("-d", "--dest", action="store", type="string", dest='dest', default='.',
                      help="directory where new plugin directory will be created (optional)")
    parser.add_option("-g", "--group", action="store", type="string", dest='group', 
                      default = 'openmdao.component',
                      help="specify plugin group (openmdao.component, openmdao.driver, openmdao.variable) (optional)")
    
    (options, args) = parser.parse_args(argv)

    if len(args) < 1 or len(args) > 2:
        parser.print_help()
        sys.exit(-1)

    name = args[0]
    if options.classname:
        classname = options.classname
    else:
        classname = "%s%s" % ((name.upper())[0], name[1:])
    version = options.version
    
    options.dest = os.path.abspath(os.path.expandvars(os.path.expanduser(options.dest)))

    startdir = os.getcwd()
    try:
        os.chdir(options.dest)
        
        if os.path.exists(name):
            raise OSError("Can't create directory '%s' because it already exists." %
                          os.path.join(options.dest, name))
        
        cfg = SafeConfigParser(dict_type=OrderedDict)
        stream = StringIO.StringIO(_templates['setup.cfg'] % { 'name':name, 
                                                              'version':version })
        cfg.readfp(stream, 'setup.cfg')
        cfgcontents = StringIO.StringIO()
        cfg.write(cfgcontents)
        
        template_options = _get_template_options(os.path.join(options.dest,name),
                                                 cfg, classname=classname)
        
        template_options['srcmod'] = name
    
        dirstruct = {
            name: {
                'setup.py': _templates['setup.py'] % template_options,
                'setup.cfg': cfgcontents.getvalue(),
                'MANIFEST.in': _templates['MANIFEST.in'] % template_options,
                'README.txt': _templates['README.txt'] % template_options,
                'src': {
                    name: {
                        '__init__.py': '', #'from %s import %s\n' % (name,classname),
                        '%s.py' % name: _class_templates[options.group] % template_options,
                        'test': {
                                'test_%s.py' % name: test_template % template_options
                            },
                        },
                    },
                'docs': {
                    'conf.py': _templates['conf.py'] % template_options,
                    'index.rst': _templates['index.rst'] % template_options,
                    'srcdocs.rst': _get_srcdocs(options.dest, name),
                    'pkgdocs.rst': _get_pkgdocs(cfg),
                    'usage.rst': _templates['usage.rst'] % template_options,
                    },
            },
        }

        build_directory(dirstruct)
    
    finally:
        os.chdir(startdir)

        
def _verify_dist_dir(dpath):
    """Try to make sure that the directory we've been pointed to actually
    contains a distribution.
    """
    if not os.path.isdir(dpath):
        raise IOError("directory '%s' does not exist" % dpath)
    
    expected = ['src', 'docs', 'setup.py', 'setup.cfg', 'MANIFEST.in',
                os.path.join('docs','conf.py'),
                os.path.join('docs','index.rst'),
                os.path.join('docs','srcdocs.rst')]
    for f in expected:
        if not os.path.exists(os.path.join(dpath, f)):
            raise IOError("directory '%s' does not contain '%s'" %
                          (dpath, f))

        
#
# FIXME: this still needs some work, but for testing purposes it's ok for now
#
def _find_all_plugins(searchdir):
    """Return a dict containing lists of each plugin type found, keyed by
    plugin group name, e.g., openmdao.component, openmdao.variable, etc.
    """
    dct = {}
    psta = PythonSourceTreeAnalyser(searchdir)
    
    comps = psta.find_inheritors('openmdao.main.component.Component')
    comps.extend(psta.find_inheritors('openmdao.main.api.Component'))
    comps = set(comps)
    
    drivers = psta.find_inheritors('openmdao.main.driver.Driver')
    drivers.extend(psta.find_inheritors('openmdao.main.api.Driver'))
    drivers = set(drivers)
    
    comps = comps - drivers
    
    dct['openmdao.component'] = comps
    dct['openmdao.driver'] = drivers
    
    variables = psta.find_inheritors('openmdao.main.api.Variable')
    variables.extend(psta.find_inheritors('openmdao.main.variable.Variable'))
    dct['openmdao.variable'] = set(variables)

    return dct

def _get_entry_points(startdir):
    plugins = _find_all_plugins(startdir)
    entrypoints = StringIO.StringIO()
    for key,val in plugins.items():
        epts = []
        for v in val:
            mod,cname = v.rsplit('.', 1)
            epts.append('%s.%s=%s:%s' % (mod,cname,mod,cname))
        if epts:
            entrypoints.write("\n[%s]\n" % key)
            for ept in epts:
                entrypoints.write("%s\n" % ept)
    
    return entrypoints.getvalue()

def plugin_makedist(argv=None):
    """A command line script (plugin_makedist) points to this.  It creates a 
    source distribution containing sphinx documentation for the specified
    distribution directory.  If no directory is specified, the current directory
    is assumed.
    
    usage: plugin_makedist [dist_dir_path]
    
    """
    
    if argv is None:
        argv = sys.argv[1:]
        
    if len(argv) == 0:
        destdir = os.getcwd()
    elif len(argv) == 1:
        destdir = os.path.abspath(os.path.expandvars(os.path.expanduser(argv[0])))
    else:
        raise RuntimeError("\nusage: plugin_makedist [dist_dir_name]\n")

    _verify_dist_dir(destdir)

    startdir = os.getcwd()
    os.chdir(destdir)
    
    try:
        plugin_build_docs([destdir])
        
        cfg = SafeConfigParser(dict_type=OrderedDict)
        cfg.readfp(open('setup.cfg', 'r'), 'setup.cfg')
            
        cfg.set('metadata', 'entry_points', _get_entry_points('src'))
        
        template_options = _get_template_options(destdir, cfg,
                                                 packages=find_packages('src'))

        dirstruct = {
            'setup.py': _templates['setup.py'] % template_options,
            }
        
        name = cfg.get('metadata', 'name')
        version = cfg.get('metadata', 'version')
        
        if sys.platform == 'win32':
            disttar = "%s-%s.zip" % (name, version)
        else:
            disttar = "%s-%s.tar.gz" % (name, version)
        disttarpath = os.path.join(startdir, disttar)
        if os.path.exists(disttarpath):
            sys.stderr.write("ERROR: distribution %s already exists.\n" % disttarpath)
            sys.exit(-1)
        
        build_directory(dirstruct, force=True)

        cmdargs = [sys.executable, 'setup.py', 'sdist', '-d', startdir]
        cmd = ' '.join(cmdargs)
        retcode = call(cmdargs)
        if retcode:
            sys.stderr.write("\nERROR: command '%s' returned error code: %s\n" % (cmd,retcode))
    finally:
        os.chdir(startdir)

    if os.path.exists(disttar):
        print "Created distribution %s" % disttar
    else:
        sys.stderr.write("\nERROR: failed to make distribution %s" % disttar)

def plugin_docs(argv=None):
    """A command line script (plugin_docs) points to this. It brings up
    the sphinx documentation for the named plugin in a browser.
    """
    if argv is None:
        argv = sys.argv[1:]
        
    if len(argv) != 1:
        print 'usage: plugin_docs <plugin_dist_name> [browser_name]'
        sys.exit(-1)
        
    if len(argv) > 1:
        browser = argv[1]
    else:
        browser = None
        
    _plugin_docs(argv[0], browser)
        
        
def _plugin_docs(plugin_name, browser=None):
    """This brings up the sphinx docs for the named plugin using the
    specified browser.  The plugin must be importable in the current 
    environment.
    
    plugin_name: str
        Name of the plugin distribution.
        
    browser: str (optional)
        Name of the browser (according to the webbrowser library) to
        use to view the plugin docs.  If none is specified, the platform
        default browser will be used.
    """
    try:
        mod = __import__(plugin_name)
    except ImportError:
        raise RuntimeError("Can't locate plugin '%s'" % plugin_name)
    
    idx = os.path.join(os.path.dirname(os.path.abspath(mod.__file__)),
                       'sphinx_build', 'html', 'index.html')
    
    if not os.path.isfile(idx):
        raise RuntimeError("Cannot locate index file for plugin '%s'" % plugin_name)
    
    wb = webbrowser.get(browser)
    wb.open(idx)


def plugin_install(argv=None):
    """A command line script (plugin_install) points to this. It installs
    the specified plugin distribution into the current environment.
    
    """
    if argv is None:
        argv = sys.argv[1:]
        
    parser = OptionParser()
    parser.usage = "plugin_install [plugin_distribution] [options]"
    parser.add_option("-f", "--find-links", action="store", type="string", dest='findlinks', 
                      help="URL of find-links server") 
    
    (options, args) = parser.parse_args(argv)
    
    develop = False
    if len(args) == 0:
        print "installing distribution from current directory as a 'develop' egg"
        develop = True
    elif len(args) > 1:
        parser.print_help()
        sys.exit(-1)
        
    if develop:
        cmdargs = [sys.executable, 'setup.py', 'develop', '-N']
    else:
        cmdargs = ['easy_install']
        if options.findlinks:
            cmdargs.extend(['-f', options.findlinks])
        else:
            cmdargs.extend(['-f', 'http://openmdao.org/dists']) # make openmdao.org the default
        cmdargs.append(argv[0])
    cmd = ' '.join(cmdargs)
    retcode = call(cmdargs)
    if retcode:
        sys.stderr.write("\nERROR: command '%s' returned error code: %s\n" % (cmd,retcode))
        sys.exit(-1)

    
def _plugin_build_docs(destdir, cfg):
    """Builds the Sphinx docs for the plugin distribution, assuming it has
    a structure like the one created by plugin_quickstart.
    """
    name = cfg.get('metadata', 'name')
    version = cfg.get('metadata', 'version')
    
    path_added = False
    try:
        docdir = os.path.join(destdir, 'docs')
        srcdir = os.path.join(destdir, 'src')
        
        # have to add srcdir to sys.path or autodoc won't find source code
        if srcdir not in sys.path:
            sys.path[0:0] = [srcdir]
            path_added = True
            
        sphinx.main(argv=['','-E','-a','-b', 'html',
                          '-Dversion=%s' % version,
                          '-Drelease=%s' % version,
                          '-d', os.path.join(srcdir, name, 'sphinx_build', 'doctrees'), 
                          docdir, 
                          os.path.join(srcdir, name, 'sphinx_build', 'html')])
    finally:
        if path_added:
            sys.path.remove(srcdir)
    
    
def plugin_build_docs(argv=None):
    """A command line script (plugin_build_docs) points to this.  It builds the
    sphinx documentation for the specified distribution directory.  
    If no directory is specified, the current directory is assumed.
    
    usage: plugin_build_docs [dist_dir_path]
    
    """
    
    if argv is None:
        argv = sys.argv[1:]
        
    if len(argv) == 0:
        destdir = os.getcwd()
    elif len(argv) == 1:
        destdir = os.path.abspath(os.path.expandvars(os.path.expanduser(argv[0])))
    else:
        raise RuntimeError("\nusage: plugin_build_docs [dist_dir_name]\n")

    _verify_dist_dir(destdir)
    cfgfile = os.path.join(destdir, 'setup.cfg')

    cfg = SafeConfigParser(dict_type=OrderedDict)
    cfg.readfp(open(cfgfile, 'r'), cfgfile)
    
    cfg.set('metadata', 'entry_points', 
            _get_entry_points(os.path.join(destdir,'src')))
    
    template_options = _get_template_options(destdir, cfg)

    dirstruct = {
        'docs': {
            'conf.py': _templates['conf.py'] % template_options,
            'pkgdocs.rst': _get_pkgdocs(cfg),
            'srcdocs.rst': _get_srcdocs(destdir, template_options['name']),
            },
        }
    
    build_directory(dirstruct, force=True, topdir=destdir)
    _plugin_build_docs(destdir, cfg)

