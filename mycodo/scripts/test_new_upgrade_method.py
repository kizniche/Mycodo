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
major_ver = 4


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


mycodo_releases = json_to_dict(mycodo_release_url)

print("List of all Mycodo Releases:")

all_versions = []
maj_versions =[]
for each_release in mycodo_releases:
    if re.match('v{maj}.*(\d\.\d)'.format(maj=major_ver),
                each_release['name']):
        maj_versions.append(each_release['name'][1:])
    if re.match('v.*(\d\.\d\.\d)', each_release['name']):
        all_versions.append(each_release['name'][1:])
    print("{ver} ".format(ver=each_release['name']))

all_versions_sorted = []
for each_version in all_versions:
    all_versions_sorted.append(each_version)
all_versions_sorted.sort(key=lambda s: list(map(int, s.split('.'))))
all_versions_sorted.reverse()

maj_versions_sorted = []
for each_version in maj_versions:
    maj_versions_sorted.append(each_version)
maj_versions_sorted.sort(key=lambda s: list(map(int, s.split('.'))))
maj_versions_sorted.reverse()

tar_url_latest = ''
for each_release in mycodo_releases:
    if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
            each_release['name'][1:] == all_versions_sorted[0]):
        tar_url_latest = each_release['tarball_url']

tar_url_maj = ''
for each_release in mycodo_releases:
    if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
            each_release['name'][1:] == maj_versions_sorted[0]):
        tar_url_maj = each_release['tarball_url']

for each_release in mycodo_releases:
    if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
            each_release['name'][1:] == all_versions_sorted[0]):
        print("\nLatest Version: {ver}"
              "\nTar URL: {url}".format(ver=each_release['name'],
                                        url=tar_url_latest))

for each_release in mycodo_releases:
    if (re.match('v.*(\d\.\d\.\d)', each_release['name']) and
            each_release['name'][1:] == maj_versions_sorted[0]):
        print("\nLatest v{maj} Version: {ver}"
              "\nTar URL: {url}".format(maj=major_ver,
                                        ver=each_release['name'],
                                        url=tar_url_maj))
