from builtins import range
from setuptools import setup
from setuptools.command.install import install as dist_install

name = 'alfred'
version = '1.0.2b1'  # major.minor[.patch[sub] e.g. 0.1.0 first experimental version, 1.0.1b2 second beta release of the first patch of 1.0
desc = 'alfred : a library for rapid experiment development'
author = 'Christian Treffenstaedt, Paul Wiemann, Johannes Brachem'
author_email = 'treffenstaedt@psych.uni-goettingen.de'
license = 'MIT'
url = 'http://www.the-experimenter.com/alfred'
package_dir = {'': 'src'}
packages = ['alfred', 'alfred.helpmates']
package_data = {'alfred': ['files/*', 'static/css/*', 'static/img/*', 'static/js/*', 'templates/*', 'templates/elements/*']}
install_requires = ['future', 'cryptography', 'jinja2', 'PySide2', 'pymongo', 'flask', 'xmltodict']


class install(dist_install):
    user_options = dist_install.user_options + [('without-pyside', None, 'kommentiert alle pyside anweisungen aus')]

    def initialize_options(self):
        dist_install.initialize_options(self)
        self.without_pyside = 0

    def run(self):
        if self.without_pyside:
            self.debug_print("without-pyside flag gesetzt")
            self.escape_pyside()

        dist_install.do_egg_install(self)

    def escape_pyside(self):
        import os.path
        import re
        filelist = []

        for root, subFolders, files in os.walk(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src', 'alfred')):
            for file in files:
                if file.endswith(".py"):
                    filelist.append(os.path.join(root, file))

        for filename in filelist:
            with open(filename, 'r+') as f:
                lines = f.readlines()
                f.seek(0)
                f.truncate()

                for i in range(len(lines)):
                    line = lines[i]
                    if re.match(r"^\s*((import|from)\s+PySide2|@.*Slot)", line):
                        self.debug_print("In \"%s\" wird Zeile %s \"%s\" auskommentiert" % (filename, i, line[:-1]))
                        lines[i] = '#' + line

                f.writelines(lines)


setup(name=name,
      version=version,
      description=desc,
      author=author,
      author_email=author_email,
      license=license,
      url=url,
      packages=packages,
      package_dir=package_dir,
      package_data=package_data,
      install_requires=install_requires,
      cmdclass=dict(install=install)
      )
