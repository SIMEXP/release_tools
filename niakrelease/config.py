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



import logging
import os.path

DEBUG = False

def to_full_dir_path(path):
    return os.path.dirname(os.path.abspath(os.path.expandvars(os.path.expanduser(path))))

if DEBUG:
    import getpass
    ROOT = "/niak/niak_debug"
    USER = getpass.getuser()
else:
    ROOT = "/niak"
    USER = "simexp"


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
    URL = "https://github.com/{0}/niak_target.git".format(USER)

    WORK_DIR = "{}/work/target".format(ROOT)
    PATH = "{}/niak_target".format(ROOT)
    RESULT_DIR = os.path.join(WORK_DIR, "result")  # Niak default output
    # TAG_NAME is typically "X.Y.Z"
    LOG_PATH = "{}/result/logs".format(WORK_DIR)
    TAG_SUFFIX = "ad"


class NIAK:
    """
    Niak release Config
    """
    # Hash that will be used for the release
    REPO = "niak"
    HASH = ""
    PATH = "{}/niak".format(ROOT)

    URL = "https://github.com/{0}/niak.git".format(USER)

    # RELEASE_BRANCH = "niak-boss"
    # RELEASE_BRANCH = "master"
    RELEASE_BRANCH = "subtype"
    # RELEASE_FROM_BRANCH = "master"
    RELEASE_FROM_BRANCH = "subtype"
    # RELEASE_FROM_BRANCH = "issue228"
    RELEASE_FROM_COMMIT = None  # If None will release from tip

    # RELEASE_BRANCH = ""
    # TAG_NAME = "v0.17.0"
    TAG_NAME = "dev"
    # release Name
    DEPENDENCY_RELEASE = "niak-with-dependencies.zip"
    WORK_DIR = "{}/work/niak-{}".format(ROOT, TAG_NAME)

    VERSION_ENV_VAR = "NIAK_VERSION"


class PSOM:
    """
    PSOM config
    """
    PATH = "{}/psom".format(ROOT)
    URL = "https://github.com/{0}/psom.git".format(USER)
# URL = "https://github.com/poquirion/psom.git"
    RELEASE_TAG = "v2.1.0"


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
    API = "https://api.github.com"
    UPLOAD_API = "https://uploads.github.com"
    TOKEN = os.getenv("GIT_TOKEN")
    if DEBUG:
        OWNER = "poquirion"
    else:
        OWNER = "simexp"
