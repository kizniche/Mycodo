#!/usr/bin/env python

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import argparse
import json
import re

mycodo_release_url = "https://api.github.com/repos/kizniche/Mycodo/tags"


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


def sort_reverse_list(versions_unsorted):
    """
    Sort and reverse a list of strings representing version numbers in
    the format "x.x.x"

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


def return_latest_version_url():
    """Return the tarball URL for the latest version"""
    mycodo_releases = json_to_dict(mycodo_release_url)
    all_versions = []
    for each_release in mycodo_releases:
        if re.match('v.*(\d\.\d\.\d)', each_release['name']):
            all_versions.append(each_release['name'][1:])

    for each_release in mycodo_releases:
        if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
                each_release['name'][1:] == sort_reverse_list(all_versions)[0]):
            # print("\nLatest Version: {ver}"
            #       "\nTar URL: {url}".format(ver=each_release['name'],
            #                                 url=each_release['tarball_url']))
            # return each_release['name'][1:], each_release['tarball_url']
            return each_release['tarball_url']


def return_maj_version_url(major_version):
    """Return the tarball URL for the version with the specified major number"""
    mycodo_releases = json_to_dict(mycodo_release_url)
    maj_versions = []
    for each_release in mycodo_releases:
        if re.match('v{maj}.*(\d\.\d)'.format(maj=major_version),
                    each_release['name']):
            maj_versions.append(each_release['name'][1:])

    for each_release in mycodo_releases:
        if (re.match('v{maj}.*(\d\.\d)'.format(maj=major_version), each_release['name']) and
                each_release['name'][1:] == sort_reverse_list(maj_versions)[0]):
            # print("\nLatest v{maj} Version: {ver}"
            #       "\nTar URL: {url}".format(maj=major_version,
            #                                 ver=each_release['name'],
            #                                 url=each_release['tarball_url']))
            # return each_release['name'][1:], each_release['tarball_url']
            return each_release['tarball_url']


def version_information(major_version):
    """Print all releases, and specific info about latest and major releases"""
    mycodo_releases = json_to_dict(mycodo_release_url)
    print("List of all Mycodo Releases:")

    for each_release in mycodo_releases:
        print("{ver} ".format(ver=each_release['name']))

    print(return_latest_version_url())
    print(return_maj_version_url(major_version))


def parseargs(parser):
    parser.add_argument('-m', '--majorversion', type=int,
                        help='Return the latest version URL with major version'
                             ' number x in x.y.z.',
                        required=False)
    parser.add_argument('-l', '--latest', action='store_true',
                        help='Return the latest version URL.')
    return parser.parse_args()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns a github release URL'
                                                 ' to download Mycodo.')
    args = parseargs(parser)
    if args.latest:
        print(return_latest_version_url())
    elif args.majorversion:
        print(return_maj_version_url(args.majorversion))
    else:
        parser.print_help()
