#!/usr/bin/env python

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

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


ret_dict = json_to_dict(mycodo_release_url)

print("List of Mycodo Releases:")

versions = []
for each_release in ret_dict:
    if re.match('v.*(\d\.\d\.\d)', each_release['name']):
        versions.append(each_release['name'][1:])
    print("\nRelease Version: {ver}"
          "\nRelease URL (tar): {rel_url}"
          "\nCommit URL: {com_url}\n".format(
                ver=each_release['name'],
                rel_url=each_release['tarball_url'],
                com_url=each_release['commit']['url']))

versions_sorted = []
for each_version in versions:
    versions_sorted.append(each_version)
versions_sorted.sort(key=lambda s: list(map(int, s.split('.'))))
versions_sorted.reverse()

release_url = ''
for each_release in ret_dict:
    if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
            each_release['name'][1:] == versions_sorted[0]):
        release_url = each_release['tarball_url']

print("Latest Mycodo Version: v{ver}\nRelease URL (tar): {rel_url}".format(
    ver=versions_sorted[0], rel_url=release_url))
