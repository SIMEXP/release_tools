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


# @TODO Write doc!
__author__ = 'Pierre-Olivier Quirion <pioliqui@gmail.com>'

def main(args=None):


    if args is None:
        args = sys.argv[1:]

    example = """Example:
A Typical release including a new target and an new Niak release would be
    > ./release_new_target.py -rn

To release only a new niak
    > ./release_new_target.py -n

To release only a new target
    > ./release_new_target.py -r
               """

    parser = argparse.ArgumentParser(description='Create and release new Niak target.', epilog=example,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--branch', '-b', help='the niak branch where to put the version')

    parser.add_argument('--dry_run', '-d', action='store_true', help='no commit no push!')

    parser.add_argument('--niak_path', '-N', help='the path to the Niak repo',
                        default=niakr.config.NIAK.PATH)

    parser.add_argument('--niak_url', '-O', help='the url to the Niak git repo',
                        default=niakr.config.NIAK.URL)

    parser.add_argument('--psom_path', '-P', help='the path to the PSOM repo',
                        default=niakr.config.PSOM.PATH)

    parser.add_argument('--psom_url', '-M', help='the url to the PSOM git repo',
                        default=niakr.config.PSOM.URL)

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

    parser.add_argument('--recompute_target', '-R', action='store_true',
                        help='will recompute target event if already present')

    parser.add_argument('--target_path', '-T', help='the path to the target ',
                        default=niakr.config.TARGET.PATH)

    parser.add_argument('--target_url', '-U', help='the url to the target',
                        default=niakr.config.TARGET.URL)

    parser.add_argument('--target_name', '-G', help='the tag name of the target ',
                        default=niakr.config.TARGET.TAG_NAME)




    parsed = parser.parse_args(args)

    new_target = niakr.process.TargetRelease(dry_run=parsed.dry_run,
                                       niak_path=parsed.niak_path,
                                       niak_url=parsed.niak_url,
                                       target_path=parsed.target_path,
                                       target_name=parsed.target_name,
                                       release_target=parsed.release_target,
                                       psom_path=parsed.psom_path,
                                       psom_url=parsed.psom_url,
                                       push_niak_release=parsed.push_niak_release,
                                       force_niak_release=parsed.force_niak_release,
                                       recompute_target=parsed.recompute_target)


    new_target.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()

