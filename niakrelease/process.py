"""
This module runs octave modules


copyright (c) P-O Quirion
Centre de recherche de l'institut de Gériatrie de Montréal
Université de Montréal, 2015-2016
Maintainer : poq@criugm.qc.ca

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
# TODO Write doc!
# TODO Remove hard coded path and reference to config inside methods
# TODO Remove all call to config.py
# TODO Make the exception - crash system more robust (except, finally)
__author__ = 'Pierre-Olivier Quirion <poq@criugm.qc.ca>'

import io
import logging
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile

import requests
import simplejson as json

# TODO Add these in setup.py
try:
    import psutil
except ImportError:
    pass
try:
    from . import config
    from . import simplegit
except SystemError:
    import config
    import simplegit

class Error(Exception):
    """
    Base exception for this module
    """
    pass


class Runner(object):
    """
    Class that can be used to execute script
    TODO write a parent class that will be used to build runner for other software (niak)
    """

    def __init__(self, error_form_log=False):
        """
        "super" the __ini__ in your class and fill the
        self.subprocess_cmd as a minimum
        """
        self.subprocess_cmd = []

        self.error_from_log = error_form_log
        self.cancel = False
        self._activity = {'last': None, 'error': None}
        self._timeout_once_done = 5 # in seconds
        self.sleep_loop = 0.05

    def run(self):
        """

        :return: the return value of the executed process
        """

        cmd = self.subprocess_cmd
        logging.info('Executing {0}'.format(" ".join(cmd)))

        child = subprocess.Popen(cmd,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 bufsize=1)

        completion_time = 0
        process_is_done = False
        stdout_is_close = False
        interrupt_the_process = False

        # (stdout, stderr) = child.communicate()

        stdout_queue = queue.Queue()
        stdout_monitor_thread = threading.Thread(
            target=self.read_from_stream,
            args=(child.stdout, self._activity, stdout_queue, True),
            )

        stdout_monitor_thread.daemon = True
        stdout_monitor_thread.start()

        stderr_monitor_thread = threading.Thread(
            target=self.read_from_stream,
            args=(child.stderr, self._activity, None, True),
            )
        stderr_monitor_thread.daemon = True
        stderr_monitor_thread.start()

        stdout_lines = []
        while not (process_is_done or stdout_is_close):

            now = time.time()

            # We need to cancel the processing!
            if self.cancel:
                logging.info('The execution needs to be stopped.')
                break

            # If the subprocess is dead/done, we exit the loop.
            if child.poll() is not None:
                logging.info("Subprocess is done.")
                process_is_done = True

            # Once the process is done, we keep
            # receiving standard out/err up until we reach the done_timeout.
            if (completion_time > 0) and (self._timeout_once_done > 0) and (now - completion_time > self._timeout_once_done):
                logging.info("Done-timeout reached.")
                break

            # TODO Check if that is really necessary
            # If there is nothing received from child process, either from the
            # standard output or the standard error streams, past a given amount
            # of time, we assume that the sidekick is done/dead.
            # if (self.inactivity_timeout > 0) and (now - self._activity['last'] > self.inactivity_timeout):
            #     logging.info("Inactivity-timeout reached.")
            #     break

            # Handle the standard output from the child process
            if child.stdout:
                while not stdout_queue.empty():
                    stdout_lines.append(stdout_queue.get_nowait())
            else:
                interrupt_the_process = False
                stdout_is_close = True
                process_is_done = True

            # Start the countdown for the done_timeout
            if process_is_done and not completion_time:
                completion_time = now

            # Sleep a bit to avoid using too much CPU while waiting for execution to be done.
            time.sleep(self.sleep_loop)

        return_code = child.poll()

        if return_code is None:

            if interrupt_the_process:
                logging.info("The sidekick is running (PID {0}). Sending it an interrupt signal..."
                             .format(child.pid))
                child.send_signal(signal.SIGTERM)


            # Let the subprocess die peacefully...
            time_to_wait = self._timeout_once_done
            while time_to_wait > 0 and child.poll() is None:
                time.sleep(0.1)
                time_to_wait -= 0.1

            # Force the process to die if it's still running.
            return_code = child.poll()
            if return_code is None:
                logging.info("The sidekick is still running (PID {}). Sending it a kill signal..."
                             .format(child.pid))
                self.force_stop(child)

        return_code = child.poll()
        if return_code != 0:
            logging.error("The process has exited with the following return code: {}".format(return_code))
        else:
            logging.info("The process was completed and returned 0 (success)")

        if self.error_from_log and self._activity['error']:

            logging.error( "The subprocess return code is {}, it has also logged line with"
                           " \"error\" in them\nreturning ".format(return_code))
            return 0
            # retval = input("Do you want to continue process? Y/[N]")
            # if retval == "Y":
            #     return_code = 0
            # else:
            #     return_code = 1

        return return_code


    @staticmethod
    def read_from_stream(stream, activity, std_queue=None, echo=False):
        error = re.compile("error", re.IGNORECASE)
        for line in iter(stream.readline, b''):
            if std_queue:
                std_queue.put(line)
                std_queue.put("error line!!!")
            if error.search(line.decode('utf-8')):
                activity["error"] = True
            activity['last'] = time.time()
            if echo:
                sys.stderr.write(line.decode('utf-8'))
        stream.close()

    @staticmethod
    def force_stop(sub_proc, including_parent=True):
        """
        Stops the execution of process and of its children
        :param sub_proc a process with a pid attribute:
        :param including_parent:
        :return:
        """
        parent = psutil.Process(sub_proc.pid)
        logging.info("Killing the sub-processes using psutil.")
        for child in parent.children(recursive=True):
            child.kill()
        if including_parent:
            parent.kill()


def delete_git_asset(repo_owner, repo_name, tag, asset_name, raise_on_error=False):
    """ Delete the assset "asset_name" of the git release "repo_owner/repo_name:tag"
    :param repo_owner: the repo owner
    :param repo_name: the repo name
    :param tag: the release tag
    :param asset_name: the asset name
    :return:
    """
    git = config.GIT()

    # if raise_on_error:
    #     class ERROR_THAT_DOES_NOT_EXIST(Exception):
    #         pass
    #     THE_ERROR = ERROR_THAT_DOES_NOT_EXIST
    # else:
    #     THE_ERROR = urllib.error.HTTPError


    headers = {"Accept": "application/vnd.github.manifold-preview",
                "Authorization": "token {}".format(git.TOKEN)}
    url = "{api}/repos/{owner}/{repo}/releases".format(api=git.API, owner=repo_owner, repo=repo_name)

    get = urllib.request.Request(url=url)

    to_be_deleted_id = None
    with urllib.request.urlopen(url=get) as fp:
        reply = json.loads(fp.read().decode('utf-8'))
        for elem in reply:
            if elem['tag_name'] == tag and elem.get("assets") is not None:
                for asset in elem["assets"]:
                    if asset["name"] == asset_name:
                        to_be_deleted_id = asset["id"]

    if to_be_deleted_id is None:
        logging.info("The asset does not exist, all is good")
        return

    del_url = "{api}/repos/{owner}/{repo}/releases/assets/{asset_id}"\
        .format(api=git.API, owner=repo_owner, repo=repo_name, asset_id=to_be_deleted_id)
    requests.delete(url=del_url, headers=headers)

def upload_release_to_git(repo_owner, repo_name, tag, file_path, asset_name
                          , prerelease=None
                          , body=None):
    """A convenience method to upload release file to github

    :param repo_owner: the repo owner
    :param repo_name: the repo name
    :param tag: the release tag
    :param file_path: the file to upload
    :return: the upload post reply

    """
    logging.info("Preparing {} to {}/{} tag {}".format(file_path, repo_owner, repo_name, tag))
    git = config.GIT()

    headers = {"Accept": "application/vnd.github.manifold-preview",
                "Authorization": "token {}".format(git.TOKEN)}


    # find the github  release id using the release tag
    url = "{api}/repos/{owner}/{repo}/releases".format(api=git.API, owner=repo_owner, repo=repo_name)
    get = urllib.request.Request(url=url)

    with urllib.request.urlopen(url=get) as fp:
        reply = json.loads(fp.read().decode('utf-8'))
        upload_url, git_id = next(((elem["upload_url"], elem["id"])
                            for elem in reply if elem['tag_name'] == tag), (None, None))

    # Release needs to be created before file is upload
    if git_id is None:

        if 'dev' in tag.lower():
            prerel = True
        else:
            prerel = False

        if prerelease is not None:
            prerel = prerelease

        if body is None:
            body = "Complete release"
        else:
            body = body
        data = json.dumps({"tag_name": tag, "name": tag, "body": body,
                           "draft": False, "prerelease": prerel}).encode(encoding='UTF-8')
        headers.update({"Content-Type": "application/json",
                        "Content-Length": len(data)})
        post = urllib.request.Request(url=url, headers=headers, data=data)
        with urllib.request.urlopen(url=post) as fp:
            reply = json.loads(fp.read().decode('utf-8'))
            upload_url, git_id = reply["upload_url"], reply["id"]

    # upload the file to the release
    if os.path.isfile(file_path):
        dir, file = os.path.split(file_path)
    else:
        raise FileNotFoundError(file_path)
    with open(file_path, "rb") as fp:

        upload_url = re.sub("\{.*\}", "?name={}".format(asset_name), upload_url)

        length = os.path.getsize(file_path)
        headers.update({"Content-Type": "application/zip",
                        "Content-Length": length})

        post = urllib.request.Request(url=upload_url, data=fp, headers=headers)
        #
        logging.info("url:\n{}\nheaders:\n{}".format(upload_url, headers))
        logging.info("uploading {} to github".format(file_path))
        logging.info("Be patient, this could take a while!")
        with urllib.request.urlopen(url=post) as reply:
                return json.loads(reply.read().decode('utf-8'))
        logging.info("Uploading sucessfull")


class TargetRelease(object):
    """
    Used for releasing targets

    """

    TAG_PREFIX = "target_test_niak_mnc1-"

    TARGET_NAME_IN_NIAK = "gb_niak_target_test"

    NIAK_GB_VARS = "commands/misc/niak_gb_vars.m"

    UNCOMMITTED_CHANGE = "Changes to be committed:"

    NOTING_TO_COMMIT = "nothing to commit, working directory clean"

    AT_ORIGIN = "Your branch is up-to-date with 'origin"

    TMP_BRANCH = '_TMP_RELEASE_BRANCH_'

    def __init__(self, target_path=None, target_suffix=None, niak_path=None,
                 niak_tag=None, dry_run=False, recompute_target=False, target_work_dir=None,
                 result_dir=None, release_target=True, niak_url=None, psom_path=None,
                 psom_url=None, new_niak_release=False, niak_release_from_branch=None,
                 niak_release_from_commit=None, force_niak_release=False, niak_release_branch=None):

        # TODO add a niak_release_from_commit option, right now release can only be done
        #       from the tip of a the niak_release_from_branch
        # , niak_release_commit=None):

        # the hash of the commit to release from
        if len(niak_release_from_commit) >= 7:
            self.niak_release_commit = niak_release_from_commit
        else:
            raise IOError('Commit hash needs at least 7 alphanumeric entries: {}'.format(niak_release_from_commit))

        # target tag name
        self.target_path = target_path

        self.niak_path = niak_path
        self.niak_url = niak_url
        self.psom_path = psom_path
        self.psom_url = psom_url

        # Where the new target is computed
        self.result_dir = result_dir

        # Will release on this branch
        self.niak_release_branch = niak_release_branch

        # Will release a target wit a tag
        self.release_target = release_target

        self.recompute_target = recompute_target

        self.work_dir = target_work_dir

        self.dry_run = dry_run

        # release from branch release
        self.niak_release_from_branch = niak_release_from_branch

        # Will release a new niak version with a tag
        self.new_niak_release = new_niak_release
        self.force_niak_release = force_niak_release

        # the name of the release
        if re.match('v[0-9]+\.[0-9]+.[0-9]+', niak_tag):
            self.niak_tag = niak_tag
        elif self.new_niak_release:
            IOError('{} not a valid niak release tag'.format(self.niak_tag))


        self._sanity_check()

        self.niak_repo = simplegit.Repo(self.niak_path)

        self.niak_repo.branch(self.TMP_BRANCH, delete=True)

        self._log_path = config.TARGET().LOG_PATH

        self.target_suffix = target_suffix

        self.target = None

    @property
    def target_tag_w_prefix(self):
        return self.TAG_PREFIX + self.target_suffix

    def _execute(self, cmd, cwd=None):
        logging.info("Executing \nin {0}: {1}".format(cwd, " ".join(cmd)))
        ret = subprocess.check_output(cmd, cwd=cwd, universal_newlines=True)
        logging.info("returning \n{}".format(ret))
        return ret

    def _sanity_check(self, take_action=True):
        """
            Runs series of test before it it good to go
            This should grow with time!

        :type take_action bool
        :return:
        """

        errors = []
        warning = []
        if os.getenv('GIT_TOKEN') is None:
            errors.append('GIT_TOKEN Missing from your environment, '
                          'take action before you continue!')
        else:
            logging.info('GIT_TOKEN is in your environment')

        # check if niak is at the right place
        if os.path.isdir(os.path.join(self.niak_path, '.git')):
            logging.info("The niak repo seems in place")
        else:
            if take_action:
                logging.info('cleaning niak directory')
                shutil.rmtree(self.niak_path, ignore_errors=True)
                logging.info('cloning niak')
                simplegit.clone(self.niak_url, self.niak_path)

            else:
                errors.append('"{}" is not a Niak/git repo'.format(self.niak_path))

        # check if psom is at the right place
        if os.path.isdir(os.path.join(self.psom_path, '.git')):
            logging.info("The psom repo is in place")
        else:
            if take_action:
                logging.info('cleaning psom directory')
                shutil.rmtree(self.psom_path, ignore_errors=True)
                logging.info('cloning niak')
                simplegit.clone(self.psom_url, self.psom_path)
                # git.Repo.clone_from(self.psom_url, self.psom_path)
            else:
                errors.append('"{}" is not a Niak/git repo '.format(self.psom_path))

        if errors:
            logging.error(errors)
            raise Exception(errors)

    def start(self):

        # DO setup and sanity check
        self.repo_prerelease_setup(sha1=self.niak_release_commit, branch=self.niak_release_from_branch)

        if self.release_target:
            if self.recompute_target:
                self.delete_target_log()
            self.target = self._build()
            pass

        self._release()

        self._finaly()

    def repo_prerelease_setup(self, sha1, branch=None, origin='origin', remote='remote'):
        """
        TODO: set origin url "git remote set-url" to the config USER (maybe put owner)
        SET local "form" and "release" branch to tip of remote branch
        Move the repo to the revision to be released.
            Targets can only be released at the tip of a branch
            Niak can be released at any revision (branch and commit)
        :param branch: The name of the dev branch to release from
        :return:
        """
        err_message = ("To release a target, the sha1 ref must be at "
             "the tip a a branch sha1 {} is not in branch {} "
             .format(sha1, branch))

        # Crash if the hash is not is the repo

        self.niak_repo.checkout("origin/master", force=True)
        self.niak_repo.branch(name=branch, delete=True)
        self.niak_repo.fetch()
        self.niak_repo.fail_on_error = True
        self.niak_repo.checkout(sha1, force=True)
        self.niak_repo.fail_on_error = False
        if self.release_target:
            if branch is None:
                raise IOError("You have to release target from a specific branch")
            ref_dico = {k[0:len(sha1)]: v for k, v in self.niak_repo.show_ref().items()}
            if sha1 in ref_dico:
                pass_test = False
                for ref in ref_dico[sha1]:
                    br = ref.split('/')
                    if origin in br[-2] and remote in br[-3] and branch in br[-1]:
                        pass_test = True
                        break
                if pass_test:
                    self.niak_repo.branch(branch, checkout=True)
                else:
                    raise IOError(err_message)

            else:
                raise IOError(err_message)

    def delete_target_log(self):
        """ Delete the target logs so it recomputes

        :return:
        """
        if os.path.isdir(self._log_path):
            shutil.rmtree(self._log_path)


    def _build(self):
        """
        build the target with niak_test_all

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        target = TargetBuilder(self.work_dir, self.niak_path, self.result_dir, self.target_tag_w_prefix
                               , error_form_log=True)
        ret_val = target.run()
        happiness = input("Are you happy with the target?Y/[N]")
        logging.info("look at {}/logs for more info".format(self.work_dir))

        # DEBUG !!!
        # if ret_val != 0 or happiness != 'Y':
        #     raise Error("The target was not computed properly")
        return target

    def _push(self, path, push_tag=None, remote_name=None, branch=None, force=False):
        #TODO lets change to non defaut
        repo = simplegit.Repo(path)
        # remote = repo.remote(remote_name=remote_name)
        # logging.info("pushing {} to {}".format(path, remote[remote_name]))
        repo.push(remote_name=remote_name, branch=branch, push_tags=push_tag, force=force)


    def _push_tag(self, path, tag, force=False):
        repo = simplegit.Repo(path)
        repo.push_tag(tag, force=False)


    def _commit(self, path, comment, branch=None, files=None, tag=None):
        """
        Add all change, add and remove files and then commit

        branch: if None, will be comited to current branch

        file : will only add and commit these
        """

        repo = simplegit.Repo(path)
        if branch:
            logging.info("checking out branch {} in ".format(branch, path))
            if branch:
                repo.branch(branch, checkout=True)

        if files is not None:
            repo.add(files)
        else:
            repo.add_all()
        repo.commit(comment)

        if tag:
            logging.warning("Adding tag {} to {} repo".format(tag, path))
            repo.tag(tag, force=True)

        return True

    def _update_niak(self):
        """
        niak_gb_var and Dockerfile will point to the right target*.zip file at download time
        """

        niak_gb_vars_path = os.path.join(self.niak_path, self.NIAK_GB_VARS)
        # docker_file = os.path.join(self.niak_path, config.DOCKER.FILE)
        commit_message = "new niak release"
        # Update version
        with open(niak_gb_vars_path, "r") as fp:
            fout = fp.read()
            if self.new_niak_release:
                fout = re.sub("GB_NIAK.version = .*",
                              "GB_NIAK.version = \'{0}\';".format(self.niak_tag), fout)
                commit_message += " Version {0}".format(self.niak_tag)
            if self.release_target:

                    fout = re.sub("GB_NIAK.target_test.*=.*",
                                  "GB_NIAK.target_test = \'{0}\';".format(self.target_suffix), fout)

                    commit_message += " Target \'{0}\'".format(self.target_suffix)

        with open(niak_gb_vars_path, "w") as fp:
            fp.write(fout)

        # with open(docker_file, "r") as fp:
        #     fout = re.sub("ENV {}.*".format(niak.VERSION_ENV_VAR),
        #                   "ENV {0} {1}".format(niak.VERSION_ENV_VAR,
        #                                        self.niak_tag), fp.read())

        # with open(docker_file, "w") as fp:
        #     fp.write(fout)

        self._commit(self.niak_path, commit_message,
                     files=[self.NIAK_GB_VARS, config.DOCKER.FILE],
                     branch=self.TMP_BRANCH)

    def _release(self):
        """
        Pushes the target to the repo and update niak_test_all and niak_gb_vars

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        try:
            self._update_niak()
        except BaseException as e:
            self._cleanup()
            raise e
        git = config.GIT()
        niak = config.NIAK()

        if not self.dry_run:

            self._merge(self.niak_repo, self.TMP_BRANCH, self.niak_release_branch, tag=self.niak_tag)

            if self.new_niak_release:
                self._push(self.niak_path, push_tag=self.niak_tag, branch=self.niak_release_branch, force=True)

            if self.release_target:
                # The tmp branch is also merge to the "release from"
                # branch so this development branch also point to the right target

                # Push target
                # merge and push niak
                self._merge(self.niak_repo, self.TMP_BRANCH, self.niak_release_from_branch)
                self.niak_repo.tag(self.target_tag_w_prefix, force=True)
                self._push(self.niak_path, push_tag=self.target_tag_w_prefix, force=True,
                           branch=self.niak_release_from_branch)


            if self.new_niak_release:
                niak_w_dependency_zip_path = self._build_niak_with_dependecy()

            if self.release_target:
                delete_git_asset(git.OWNER, niak.REPO,
                                 self.target_tag_w_prefix, self.target.zip_name)

                logging.info('pushing new target')
                upload_release_to_git(git.OWNER, niak.REPO,
                                      self.target_tag_w_prefix,
                                      self.target.zip_path, self.target.zip_name,
                                      prerelease=True,
                                      body="Target release only")

            if self.new_niak_release:
                    # if self.force_niak_release:
                    # Delete the release if it already exist and repush it.
                    logging.info('removing older asset with similar name')
                    delete_git_asset(git.OWNER, niak.REPO,
                                     self.niak_tag, niak.DEPENDENCY_RELEASE)
                    logging.info('pushing new niak release')
                    upload_release_to_git(git.OWNER, niak.REPO,
                                          self.niak_tag, niak_w_dependency_zip_path
                                          , niak.DEPENDENCY_RELEASE, prerelease=False)




        else:
            self._cleanup()


    def _build_niak_with_dependecy(self):
        """
        Take the released version and bundle it with psom and BCT in a zip file
        :return: the path to the zip file
        """
        niak = config.NIAK()
        psom = config.PSOM()
        if os.path.isdir(niak.WORK_DIR):
            shutil.rmtree(niak.WORK_DIR)
        ## HERE REFREACTOR!!!
        # Niak
        shutil.copytree(self.niak_path, niak.WORK_DIR)
        n_repo = simplegit.Repo(niak.WORK_DIR)
        n_repo.checkout(self.niak_release_branch)
        shutil.rmtree(niak.WORK_DIR+"/.git")
        # PSOM
        p_repo = simplegit.Repo(self.psom_path)
        p_repo.checkout(psom.RELEASE_TAG)
        shutil.copytree(psom.PATH, niak.WORK_DIR+"/extensions/psom-{}".format(psom.RELEASE_TAG))
        shutil.rmtree(niak.WORK_DIR+"/extensions/psom-{}/.git".format(psom.RELEASE_TAG))

        # BCT
        logging.info('download BCT form source and copying')
        BCTZIP = urllib.request.urlopen(config.BCT.url)
        with zipfile.ZipFile(io.BytesIO(BCTZIP.read())) as z:
            z.extractall(niak.WORK_DIR+"/extensions/BCT")

        # the base_dir funky stuff is the way to include the leading directory in zip...
        logging.info('creating niak w denpencency zip file')
        filename, ext = os.path.splitext(niak.DEPENDENCY_RELEASE)
        shutil.make_archive(niak.WORK_DIR+"/../"+filename,
                            ext[1:], root_dir=niak.WORK_DIR+"/../",
                            base_dir="niak-{}".format(self.niak_tag))

        return niak.WORK_DIR+"/../"+niak.DEPENDENCY_RELEASE

    def _merge(self, repo, branch1, branch2, tag=None):
        """
        Merge branch1 to branch2

        :param repo: a simplegit repo
        :param branch1: The branch that provide the merge (need to exist)
        :param branch2: The branch that receive the merge (does not need to exist)
        :param tag: Tag to be added to branch1
        :return: None
        """
        repo.branch(branch2, checkout=True)
        repo.merge(branch1, branch2, strategy='theirs')

        repo.commit("New Niak Release {0}{0}"
                    .format(self.niak_release_branch, tag))
        if tag is not None:
            repo.tag(tag, force=True)


    def _finaly(self):
        """
        Delete tmp branch and checkout to the tip of the original branch
        :return:
        """
        self.niak_repo.checkout(self.niak_repo._init_branch, force=True)
        self.niak_repo.branch(name=self.TMP_BRANCH, delete=True)

    def _cleanup(self):
        """
        Checkout niak modified file
        Make sure that we are back in the init repo
        Delete the TMP BRANCH and the local release branch
        :return:
        """
        self.niak_repo.checkout(self.niak_repo._init_branch, force=True)
        self.niak_repo.reset(self.niak_repo._init_sha1, hard=True)
        self.niak_repo.branch(self.TMP_BRANCH, delete=True)
        self.niak_repo.branch(self.niak_release_branch, delete=True)



class TargetBuilder(Runner):
    """ This class is used to release niak target

    """

    # DOCKER OPT CST
    MT = "-v"
    DOCKER_RUN = ["docker", "run"]
    FULL_PRIVILEDGE = ["--privileged"]
    RM = ["--rm"]
    MT_SHADOW = [MT, "/etc/shadow:/etc/shadow"]
    MT_GROUP = [MT, "/etc/group:/etc/group"]
    MT_TMP = [MT, "{0}:{0}".format(tempfile.gettempdir())]
    MT_PASSWD = [MT, "/etc/passwd:/etc/passwd"]
    MT_X11 = [MT, "/tmp/.X11-unix:/tmp/.X11-unix"]
    MT_HOME = [MT, "{0}:{0}".format(os.getenv("HOME"))]
    MT_ROOT = [MT, "{0}:{0}".format(config.Repo().ROOT)]
    ENV_DISPLAY = ["-e", "DISPLAY=unix$DISPLAY"]
    USER = ["--user", str(os.getuid())]
    IMAGE = [config.DOCKER.IMAGE]

    def __init__(self, work_dir, niak_path, result_dir, tag_name, error_form_log=False):

        super().__init__(error_form_log=error_form_log)

        #TODO make them arg not kwargs
        self.niak_path = niak_path
        self.work_dir = work_dir
        self.result_dir = result_dir

        self.tag_name = tag_name

        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)

        mt_work_dir = [self.MT, "{0}:{0}".format(self.work_dir)]

        self.load_niak = \
            "addpath(genpath('{}')); ".format(self.niak_path)


        # Only builds the target
        cmd_line = ['/bin/bash',  '-lic',
                    "cd {0}; octave "
                    "--eval \"{1};opt = struct(); path_test = struct()"
                    ";opt.flag_target=true;opt.psom.gb_psom_max_queued=6"
                    ";niak_test_all(path_test,opt);\""
                    .format(self.work_dir, self.load_niak)]

        # convoluted docker command
        self.docker = (self.DOCKER_RUN + self.FULL_PRIVILEDGE + self.RM +
                       self.MT_X11 + self.MT_ROOT + self.MT_TMP +
                       mt_work_dir + self.ENV_DISPLAY + self.USER + self.IMAGE + cmd_line)
        self.subprocess_cmd = self.docker
        self.archive_ext = 'zip'
        self._zip_path = None
        self.zip_name = '{0}.{1}'.format(self.tag_name, self.archive_ext)

    @property
    def zip_path(self):
        if self._zip_path is None:
            self._zip_path = self.build_zip()
        return self._zip_path

    def build_zip(self):

        target_path = "{0}/{1}".format(self.work_dir, self.tag_name)
        shutil.rmtree(target_path, ignore_errors=True)
        shutil.copytree(self.result_dir, target_path)
        shutil.make_archive(self.tag_name, self.archive_ext, self.work_dir, self.tag_name)
        # shutil.rmtree('{0}/{1}'.format(self.work_dir, self.zip_name), ignore_errors=True)
        try:
            new_zip_file = '{0}/{1}'.format(self.work_dir, self.zip_name)
            os.remove(new_zip_file)
        except FileNotFoundError:
            logging.info("{0} never created in that file".format(new_zip_file))
        return shutil.move(self.zip_name, self.work_dir)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    # release = TargetRelease()
    # release._build_niak_with_dependecy()

    # delete_git_asset("poquirion", "niak", "v0.13.4", "niak-with-dependencies.zip")
    # upload_release_to_git("poquirion", "niak", "v0.13.4", "/niak/work/niak-with-dependencies.zip"
    #                       , "niak-with-dependencies.zip")
