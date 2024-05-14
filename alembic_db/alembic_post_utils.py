# -*- coding: utf-8 -*-
#
# alembic_post_utils.py - Helper functions for alembic_post.py
#
import os
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from mycodo.config import ALEMBIC_UPGRADE_POST


def read_revision_file():
    try:
        with open(ALEMBIC_UPGRADE_POST, 'r') as fd:
            return fd.read().splitlines()
    except Exception:
        return []


def write_revision_post_alembic(revision):
    with open(ALEMBIC_UPGRADE_POST, 'a+') as versions_file:
        versions_file.write('{}\n'.format(revision))
