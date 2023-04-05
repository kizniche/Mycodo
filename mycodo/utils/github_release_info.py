# -*- coding: utf-8 -*-
import argparse
import json
import logging
import os
import re
import sys
from urllib.request import urlopen

from pkg_resources import parse_version

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir) + '/..'))

from mycodo.config import MYCODO_VERSION, TAGS_URL

logger = logging.getLogger("mycodo.github_release_info")


class MycodoRelease:
    def __init__(self, tag_uri=TAGS_URL, access_token=None):
        self.mycodo_tags = []
        self.tag_uri = tag_uri
        self.access_token = access_token
        self.update_mycodo_tags()

    def update_mycodo_tags(self):
        """Populate the list of Mycodo tags."""
        response_tags = []
        parsed_tags = []
        try:
            try:
                response = urlopen(self.tag_uri)
                data = response.read().decode("utf-8")
                response_tags = json.loads(data)
            except Exception as err:
                logger.exception(f"Github API Response")
            for each_tag in response_tags:
                if "ref" in each_tag and "/" in each_tag['ref']:
                    tag_full = each_tag['ref'].split('/')
                    if len(tag_full) == 3 and re.match('v(\d+)\.(\d+)\.\d+', tag_full[2]):
                        parsed_tags.append(tag_full[2])
        except Exception:
            logger.exception("update_mycodo_tags()")
        self.mycodo_tags = parsed_tags

    def github_releases(self, major_version):
        """Return a reversed list of Mycodo release versions with a Major revision number"""
        all_versions = []
        try:
            for each_tag in self.mycodo_tags:
                if re.match(f'v{major_version}.*(\d\.\d)', each_tag):
                    all_versions.append(each_tag[1:])
        except Exception:
            logger.exception("github_releases()")

        return self.sort_reverse_list(all_versions)

    def github_latest_release(self):
        """Return the latest Mycodo release version."""
        all_versions = []
        try:
            for each_tag in self.mycodo_tags:
                if each_tag:
                    # logger.info(f"Tag: {each_tag}, version: {each_tag[1:]}")
                    all_versions.append(each_tag[1:])
        
            if all_versions:
                latest_release = self.sort_reverse_list(all_versions)[0]
                # logger.info(f"Found latest release: {latest_release}")
                return latest_release
        except Exception:
            logger.exception("github_latest_release()")
        return None

    def github_upgrade_exists(self):
        errors = []
        upgrade_exists = False
        releases = []
        current_latest_tag = None

        if not self.mycodo_tags:
            errors.append(
                "Could not download latest Mycodo version information. "
                "You may be rate-limited. Wait a while and try again.")
        try:
            current_latest_tag = self.github_latest_release()
            current_maj_version = int(MYCODO_VERSION.split('.')[0])
            releases = self.github_releases(current_maj_version)

            if releases:
                if (parse_version(releases[0]) > parse_version(MYCODO_VERSION) or
                        parse_version(current_latest_tag[0]) > parse_version(MYCODO_VERSION)):
                    upgrade_exists = True
        except Exception:
            logger.exception("github_upgrade_exists()")
            errors.append(
                "Could not determine local mycodo version or "
                "online release versions. Upgrade checks can "
                "be disabled in the Mycodo configuration.")
        return upgrade_exists, releases, self.mycodo_tags, current_latest_tag, errors

    def is_latest_installed(self):
        """
        Check if the latest Mycodo release version is installed.
        Return True if yes, False if no.
        """
        try:
            maj_revision = int(MYCODO_VERSION.split(".")[0])
            latest_version = self.return_latest_maj_version_url(True, maj_revision)
            if latest_version == MYCODO_VERSION:
                return True
            return False
        except Exception:
            logger.exception("is_latest_installed()")

    @staticmethod
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
        try:
            for each_ver in versions_unsorted:
                versions_sorted.append(each_ver)
            versions_sorted.sort(key=lambda s: list(map(int, s.split('.'))))
            versions_sorted.reverse()
        except Exception:
            logger.exception("sort_reverse_list()")
        return versions_sorted

    def return_latest_version_url(self, version_only):
        """Return the tarball URL for the latest Mycodo release version."""
        all_versions = []
        try:
            for each_tag in self.mycodo_tags:
                if each_tag:
                    all_versions.append(each_tag[1:])

            for each_tag in self.mycodo_tags:
                if each_tag and each_tag[1:] == self.sort_reverse_list(all_versions)[0]:
                    if version_only:
                        return each_tag[1:]
                    else:
                        return f"https://github.com/kizniche/Mycodo/tarball/{each_tag}"
        except Exception:
            logger.exception("return_latest_version_url()")

    def return_latest_maj_version_url(self, version_only, major_version):
        """
        Return the tarball URL for the Mycodo release version with the
        specified major number
        """
        maj_versions = []
        try:
            for each_tag in self.mycodo_tags:
                if re.match(f'v{major_version}.*(\d\.\d)', each_tag):
                    maj_versions.append(each_tag[1:])

            for each_tag in self.mycodo_tags:
                if (re.match(f'v{major_version}.*(\d\.\d)', each_tag) and
                        each_tag[1:] == self.sort_reverse_list(maj_versions)[0]):
                    if version_only:
                        return each_tag[1:]
                    else:
                        return f"https://github.com/kizniche/Mycodo/tarball/{each_tag}"
        except Exception:
            logger.exception("return_latest_maj_version_url()")

    def version_information(self, version_only):
        """
        Print all Mycodo releases, and specific info about
        latest and major releases
        """
        print(f"List of all Mycodo Release tags: {', '.join(self.mycodo_tags)}")
        print(f"Latest release tarball URL: {self.return_latest_version_url(version_only)}")


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
    p.add_argument('-p', '--printall', action='store_true',
                   help='Return all version information.')
    p.add_argument('-v', '--version', action='store_true',
                   help='Return the latest version number.')
    return p.parse_args()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Returns information about Mycodo releases.')
    args = parseargs(parser)

    if args.islatest:
        mycodo_release = MycodoRelease()
        print(mycodo_release.is_latest_installed())
    elif args.currentversion:
        print(MYCODO_VERSION)
    elif args.latest or args.majornumber:
        if args.latest and args.majornumber:
            print("Error: Can only use -l or -m, not both.")
            parser.print_help()
        else:
            mycodo_release = MycodoRelease()
            if args.latest:
                print(mycodo_release.return_latest_version_url(args.version))
            elif args.majornumber:
                print(mycodo_release.return_latest_maj_version_url(args.version, args.majornumber))
    elif args.printall:
        mycodo_release = MycodoRelease()
        mycodo_release.version_information(version_only=False)
    elif args.version:
        mycodo_release = MycodoRelease()
        print(mycodo_release.github_latest_release())
    else:
        parser.print_help()
