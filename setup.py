import glob
import os
import sys
import unittest

from distutils.core import setup, Command


def get_version():
    f = open("bugzilla/__init__.py")
    for line in f:
        if line.startswith('__version__'):
            return eval(line.split('=')[-1])


class TestCommand(Command):
    user_options = [
        ("ro-functional", None,
         "Run readonly functional tests against actual bugzilla instances. "
         "This will be very slow."),
        ("rw-functional", None,
         "Run read/write functional tests against actual bugzilla instances. "
         "As of now this only runs against partner-bugzilla.redhat.com, "
         "which requires an RH bugzilla account with cached cookies. "
         "This will also be very slow.")
    ]

    def initialize_options(self):
        self.ro_functional = False
        self.rw_functional = False

    def finalize_options(self):
        pass

    def run(self):
        os.environ["__BUGZILLA_UNITTEST"] = "1"

        import coverage
        cov = coverage.coverage(omit=["/*/tests/*", "/usr/*"])

        cov.erase()
        cov.start()

        testfiles = []
        for t in glob.glob(os.path.join(os.getcwd(), 'tests', '*.py')):
            if t.endswith("__init__.py"):
                continue

            base = os.path.basename(t)
            if (base == "ro_functional.py" and not self.ro_functional):
                continue

            if (base == "rw_functional.py" and not self.rw_functional):
                continue

            testfiles.append('.'.join(['tests', os.path.splitext(base)[0]]))


        if hasattr(unittest, "installHandler"):
            try:
                unittest.installHandler()
            except:
                print "installHandler hack failed"

        tests = unittest.TestLoader().loadTestsFromNames(testfiles)
        t = unittest.TextTestRunner(verbosity=1)

        result = t.run(tests)

        cov.stop()
        cov.save()

        err = int(bool(len(result.failures) > 0 or
                       len(result.errors) > 0))
        if not err:
            cov.report(show_missing=False)
        sys.exit(err)


class PylintCommand(Command):
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        os.system("pylint "
            "--reports=n "
            "--output-format=colorized "
            "--dummy-variables-rgx=\"dummy|ignore*|.*ignore\" "
            # Lines in modules, function size, ...
            "--disable Design "
            # Line length, spacing, ...
            "--disable Format "
            # Duplicate code
            "--disable Similarities "
            # Use of * or **
            "--disable W0142 "
            # Name doesn't match some style regex
            "--disable C0103 "
            # C0111: No docstring
            "--disable C0111 "
            # W0603: Using the global statement
            "--disable W0603 "
            # W0703: Catching too general exception:
            "--disable W0703 "
            # I0012: Warn about pylint messages disabled in comments
            "--disable I0011 "
            # R0201: Method could be a function
            "--disable R0201 "

            # Would be nice to disable these 2 but it just
            # ain't work reorganizing the code to not trigger them
            # W0223: Abstract method not overwritten in
            "--disable W0223 "
            # W0212: Access to a protected member of a client class
            "--disable W0212 "

            "bugzilla/ bin/bugzilla tests/*.py ")

        os.system("pep8 --format=pylint "
            "bugzilla/ bin/bugzilla tests/ "
            "--exclude scriptimports "
            # E303: Too many blank lines
            # E125: Continuation indent isn't different from next block
            # E128: Not indented for visual style
            "--ignore E303,E125,E128")


setup(name='python-bugzilla',
      version=get_version(),
      description='Bugzilla XMLRPC access module',
      author='Will Woods',
      author_email='wwoods@redhat.com',
      license="GPLv2",
      url='https://fedorahosted.org/python-bugzilla/',
      packages = ['bugzilla'],
      scripts=['bin/bugzilla'],
      data_files=[('share/man/man1', ['bugzilla.1'])],

      cmdclass={
        "test" : TestCommand,
        "pylint" : PylintCommand,
      }
)
