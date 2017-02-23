"""
This module includes the default configuration if the SIMEXP release tools


Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
# @TODO Write doc!
__author__ = 'Pierre-Olivier Quirion <pioliqui@gmail.com>'

import getpass
import os.path


def to_full_dir_path(path):
    return os.path.dirname(os.path.abspath(os.path.expandvars(os.path.expanduser(path))))

class Repo():

    DEBUG = False

    @property
    def ROOT(self):
        if self.DEBUG:
            return "/niak/niak_debug"
        else:
            return "/niak"
    @property
    def USER(self):
        if self.DEBUG:
            return getpass.getuser()
        else:
            return "simexp"

    @property
    def OWNER(self):
        if self.DEBUG:
            return "poquirion"
        else:
            return "simexp"


class DOCKER:
    """
    Docker Config
    """
    # Version of octave docker image used
    IMAGE = "simexp/niak_dependency:u12_o4"
    FILE = "Dockerfile"

class TARGET:
    """
        Target config
    """
    def __init__(self):
        self.URL = "https://github.com/{0}/niak_target.git".format(Repo().USER)
        self.WORK_DIR = "{}/work/target".format(Repo().ROOT)
        self.PATH = "{}/niak_target".format(Repo().ROOT)
        self.RESULT_DIR = os.path.join(self.WORK_DIR, "result")  # Niak default output
        self.LOG_PATH = "{}/result/logs".format(self.WORK_DIR)
        self.TAG_SUFFIX = "ae"


class NIAK:
    """
    Niak release Config
    """
    def __init__(self):
        # Hash that will be used for the release
        self.REPO = "niak"
        self.HASH = ""
        self.PATH = "{}/niak".format(Repo().ROOT)

        self.URL = "https://github.com/{0}/niak.git".format(Repo().USER)

        self.RELEASE_BRANCH = "devel"
        self.RELEASE_FROM_BRANCH = "devel"
        self.RELEASE_FROM_COMMIT = None  # If None will release from tip

        # RELEASE_BRANCH = ""
        self.TAG_NAME = "v0.18.0"
        # self.TAG_NAME = "dev"
        # release Name
        self.DEPENDENCY_RELEASE = "niak-with-dependencies.zip"
        self.WORK_DIR = "{}/work/niak-{}".format(Repo().ROOT, self.TAG_NAME)

        self.VERSION_ENV_VAR = "NIAK_VERSION"


class PSOM:
    """
    PSOM config
    """
    def __init__(self):
        self.PATH = "{}/psom".format(Repo().ROOT)
        self.URL = "https://github.com/{0}/psom.git".format(Repo().USER)
    # URL = "https://github.com/poquirion/psom.git"
        self.RELEASE_TAG = "v2.2.2"


class BCT:
    """
    BCT config
    """
    url = "https://sites.google.com/site/bctnet/Home/functions/BCT.zip"


class GIT:
    """
    GIT api config
    Do not forget to setup you git token! 
    You get one on git hub and set it as en env var in your .bashrc.
    """
    def __init__(self):
        self.API = "https://api.github.com"
        self.UPLOAD_API = "https://uploads.github.com"
        self.TOKEN = os.getenv("GIT_TOKEN")
        self.OWNER = Repo().OWNER


if __name__ == '__main__':
    print(Repo())