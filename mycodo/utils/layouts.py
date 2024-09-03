# -*- coding: utf-8 -*-
#
#  layouts.py - Mycodo core utils
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

import logging
import os
import shutil

from mycodo.config import PATH_TEMPLATE_LAYOUT
from mycodo.config import PATH_TEMPLATE_LAYOUT_DEFAULT

logger = logging.getLogger("mycodo.utils.layouts")


def update_layout(custom_layout):
    try:
        if custom_layout:
            # Use custom layout
            with open(PATH_TEMPLATE_LAYOUT, "w") as template:
                template.write(custom_layout)
        else:
            # Use default layout
            if (os.path.exists(PATH_TEMPLATE_LAYOUT) and
                    not os.path.samefile(PATH_TEMPLATE_LAYOUT, PATH_TEMPLATE_LAYOUT_DEFAULT)):
                # Delete current layout if it's different from the default
                os.remove(PATH_TEMPLATE_LAYOUT)
            shutil.copy(PATH_TEMPLATE_LAYOUT_DEFAULT, PATH_TEMPLATE_LAYOUT)
    except:
        logger.exception("Generating layout")
