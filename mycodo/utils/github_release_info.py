# -*- coding: utf-8 -*-
import argparse
import json
import logging
import sys
from urllib.request import urlopen

import os
import re
from pkg_resources import parse_version

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from config import MYCODO_VERSION

logger = logging.getLogger("mycodo.release_info")

release_url = 'https://api.github.com/repos/kizniche/Mycodo/tags'


def json_to_dict(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    :return: dictionary of json data
    :rtype: dict

    :param url: website address
    :type url: str
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)


def github_releases(major_version):
    """ Return the tarball URL for the latest Mycodo release version """
    mycodo_releases = json_to_dict(release_url)
    all_versions = []
    for each_release in mycodo_releases:
        if re.match('v{maj}.*(\d\.\d)'.format(maj=major_version),
                    each_release['name']):
            all_versions.append(each_release['name'][1:])
    return sort_reverse_list(all_versions)


def github_latest_release():
    """ Return the latest Mycodo release version """
    mycodo_releases = json_to_dict(release_url)
    all_versions = []
    for each_release in mycodo_releases:
        if re.match('v.*(\d\.\d\.\d)', each_release['name']):
            all_versions.append(each_release['name'][1:])
    return sort_reverse_list(all_versions)[0]


def github_upgrade_exists():
    current_latest_release = github_latest_release()
    try:
        maj_version = int(MYCODO_VERSION.split('.')[0])
        releases = github_releases(maj_version)
        if releases:
            if parse_version(current_latest_release[0]) > parse_version(MYCODO_VERSION):
                return True
    except Exception:
        logger.error("Could not determine local mycodo version or "
                     "online release versions. Upgrade checks can "
                     "be disabled in the Mycodo configuration.")


def is_latest_installed(major_number):
    """
    Check if the latest Mycodo release version is installed.
    Return True if yes, False if no.
    """
    latest_version = return_maj_version_url(True, major_number)
    if latest_version == MYCODO_VERSION:
        return True
    return False


def sort_reverse_list(versions_unsorted):
    """
    Sort and reverse a list of strings representing Mycodo release version
    numbers in the format "x.x.x"

    :return: list of sorted version strings
    :rtype: list

    :param versions_unsorted: list of unsorted version strings
    :type versions_unsorted: list
    """
    versions_sorted = []
    for each_ver in versions_unsorted:
        versions_sorted.append(each_ver)
    versions_sorted.sort(key=lambda s: list(map(int, s.split('.'))))
    versions_sorted.reverse()
    return versions_sorted


def return_latest_version_url(version_only):
    """ Return the tarball URL for the latest Mycodo release version """
    mycodo_releases = json_to_dict(release_url)
    all_versions = []
    for each_release in mycodo_releases:
        if re.match('v.*(\d\.\d\.\d)', each_release['name']):
            all_versions.append(each_release['name'][1:])

    for each_release in mycodo_releases:
        if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
                each_release['name'][1:] == sort_reverse_list(all_versions)[0]):
            if version_only:
                return each_release['name'][1:]
            else:
                return each_release['tarball_url']


def return_maj_version_url(version_only, major_version):
    """
    Return the tarball URL for the Mycodo release version with the
    specified major number
    """
    mycodo_releases = json_to_dict(release_url)
    maj_versions = []
    for each_release in mycodo_releases:
        if re.match('v{maj}.*(\d\.\d)'.format(maj=major_version),
                    each_release['name']):
            maj_versions.append(each_release['name'][1:])

    for each_release in mycodo_releases:
        if (re.match('v{maj}.*(\d\.\d)'.format(maj=major_version), each_release['name']) and
                each_release['name'][1:] == sort_reverse_list(maj_versions)[0]):
            if version_only:
                return each_release['name'][1:]
            else:
                return each_release['tarball_url']


def version_information(version_only, major_version):
    """
    Print all Mycodo releases, and specific info about
    latest and major releases
    """
    mycodo_releases = json_to_dict(release_url)
    print("List of all Mycodo Releases:")

    for each_release in mycodo_releases:
        print("{ver} ".format(ver=each_release['name']))

    print(return_latest_version_url(version_only))
    print(return_maj_version_url(version_only, major_version))


def parseargs(p):
    p.add_argument('-c', '--currentversion', action='store_true',
                   help='Return the currently-installed version.')
    p.add_argument('-i', '--islatest', action='store_true',
                   help='Return True if the currently-installed '
                        'version is the latest.')
    p.add_argument('-l', '--latest', action='store_true',
                   help='Return the latest version URL.')
    p.add_argument('-m', '--majornumber', type=int,
                   help='Return the latest version URL with major '
                        'version number x in x.y.z.')
    p.add_argument('-v', '--version', action='store_true',
                   help='Return the latest version number.')
    return p.parse_args()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Returns information about Mycodo releases.')
    args = parseargs(parser)
    if args.islatest:
        print(is_latest_installed(args.majornumber))
    elif args.currentversion:
        print(MYCODO_VERSION)
    elif args.latest or args.majornumber:
        if args.latest and args.majornumber:
            print("Error: Can only use -l or -m, not both.")
            parser.print_help()
        else:
            if args.latest:
                print(return_latest_version_url(args.version))
            elif args.majornumber:
                print(return_maj_version_url(args.version, args.majornumber))
    else:
        parser.print_help()
