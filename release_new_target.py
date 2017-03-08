#!/usr/bin/env python3
"""
This module is an executable that should be able
- to create a niak target and, give it a name (default is version_number).
- to update the target link in the niak distro.
- push the target to a git repo (or lfs) with the name as a tag.


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


import argparse
import logging
import os
import sys

import niakrelease as niakr 


# TODO Write doc!
# TODO Force tag in option, make tool crash when not provides (no more default value)
__author__ = 'Pierre-Olivier Quirion <pioliqui@gmail.com>'

def main(args=None):


    if args is None:
        args = sys.argv[1:]

    example = """Example:
A Typical release including a new target and an new Niak release would be
    > ./release_new_target.py -rn <commit_hash>

To release only a new niak
    > ./release_new_target.py -n <commit_hash>

To release only a new target
    > ./release_new_target.py -r <commit_hash> 
               """

    parser = argparse.ArgumentParser(description='Create and release new Niak target.', epilog=example,
                                     formatter_class=argparse.RawTextHelpFormatter)

    partial_parse = argparse.ArgumentParser(description='Create and release new Niak target.', epilog=example,
                                     formatter_class=argparse.RawTextHelpFormatter, add_help=False)

    parser.add_argument('--debug', help='run the release tool in debug mode', action='store_true')
    partial_parse.add_argument('--debug', help='run the release tool in debug mode', action='store_true')

    # Set debug value first to make sure that default values are right
    parsed = partial_parse.parse_known_args([e for e in args if e != '-h'], )
    niakr.config.Repo.DEBUG = parsed[0].debug

    niak = niakr.config.NIAK()
    psom = niakr.config.PSOM()
    target = niakr.config.TARGET()
    parser.add_argument('from_commit', help='the niak commit from which to start the release')

    parser.add_argument('--branch', '-b', help='the niak branch where to put the version',
                        default=niak.RELEASE_BRANCH)

    parser.add_argument('--from_branch', help='the niak branch from which to start the release',
                        default=niak.RELEASE_FROM_BRANCH)


    parser.add_argument('--dry_run', '-d', action='store_true', help='no commit no push!')

    parser.add_argument('--niak_path', '-N', help='the path to the Niak repo',
                        default=niak.PATH)

    parser.add_argument('--niak_url', '-O', help='the url to the Niak git repo',
                        default=niak.URL)

    parser.add_argument('--niak_version', help='Niak release version',
                        default=niak.TAG_NAME)

    parser.add_argument('--psom_path', '-P', help='the path to the PSOM repo',
                        default=psom.PATH)

    parser.add_argument('--psom_url', '-M', help='the url to the PSOM git repo',
                        default=psom.URL)

    parser.add_argument('--release_target', '-r', action='store_true',
                        help='If True, will push the target to the '
                             'repo and update Niak so niak_test_all point '
                             'to the target')

    parser.add_argument('--push_niak_release', '-n', action='store_true'
                        , help='Will only push niak to '
                               'url repo and create a new release '
                               'if this option is given')

    parser.add_argument('--force_niak_release', '-f', action='store_true',
                        help='Will push a Niak release even if the release '
                             'assets already exist')

    parser.add_argument('--no_target_recompute', '-R', action='store_false',
                        help='will not recompute target event if it is full of error. Useful when debugging')

    parser.add_argument('--target_path', '-T', help='the path to the target ',
                        default=target.PATH)

    parser.add_argument('--target_work_dir', help='the path to the target working/tmp directory',
                        default=target.WORK_DIR)

    parser.add_argument('--target_results', help='the path to the target results',
                        default=target.RESULT_DIR)

    parser.add_argument('--target_suffix', '-G', help='the tag name of the target ',
                        default=target.TAG_SUFFIX)




    parsed = parser.parse_args(args)

    if parsed.debug:
        parsed.no_target_recompute = False

    new_target = niakr.process.TargetRelease(dry_run=parsed.dry_run,
                                             niak_path=parsed.niak_path,
                                             niak_url=parsed.niak_url,
                                             target_path=parsed.target_path,
                                             target_suffix=parsed.target_suffix,
                                             release_target=parsed.release_target,
                                             psom_path=parsed.psom_path,
                                             psom_url=parsed.psom_url,
                                             new_niak_release=parsed.push_niak_release,
                                             force_niak_release=parsed.force_niak_release,
                                             recompute_target=parsed.no_target_recompute,
                                             niak_release_branch=parsed.branch,
                                             result_dir=parsed.target_results,
                                             target_work_dir=parsed.target_work_dir,
                                             niak_tag=parsed.niak_version,
                                             niak_release_from_branch=parsed.from_branch,
                                             niak_release_from_commit=parsed.from_commit)

    new_target.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()

