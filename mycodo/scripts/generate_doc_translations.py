# -*- coding: utf-8 -*-
"""Generate markdown file of Action information to be inserted into the manual."""
import gettext
import os
import sys

mycodo_root = os.path.abspath(os.path.join(__file__, "../../.."))
sys.path.append(mycodo_root)

from mycodo.config import LANGUAGES
from mycodo.config_translations_docs import TRANSLATIONS

str_encase = '%%%'


def replace_contents(contents, _, english=False):
    while contents.find(str_encase) != -1:
        start = contents.find(str_encase) + len(str_encase)
        end = contents.find(str_encase, start)
        str_translate = contents[start:end]
        str_replace = contents[start - len(str_encase):end + len(str_encase)]

        if str_translate in TRANSLATIONS[each_doc_file]:
            str_translation_found = TRANSLATIONS[each_doc_file][str_translate]
            if english:
                contents = contents.replace(str_replace, str(str_translation_found), 1)
            else:
                contents = contents.replace(str_replace, _(str(str_translation_found)), 1)
        else:
            if english:
                contents = contents.replace(str_replace, str(str_translate), 1)
            else:
                contents = contents.replace(str_replace, _(str_translate), 1)
    return contents


if __name__ == "__main__":
    for each_doc_file in TRANSLATIONS:
        with open(f'{mycodo_root}/docs_templates/{each_doc_file}', 'r') as f:
            contents = f.read()
            contents = replace_contents(contents, _=None, english=True)
            with open(f'{mycodo_root}/docs/{each_doc_file}', 'w') as file1:
                file1.write(contents)

        for each_lang in LANGUAGES:
            if each_lang == 'en':
                continue

            translate = gettext.translation(
                'messages',
                localedir=f'{mycodo_root}/mycodo/mycodo_flask/translations',
                languages=[each_lang])
            _ = translate.gettext

            contents = None
            with open(f'{mycodo_root}/docs_templates/{each_doc_file}', 'r') as f:
                contents = f.read()

            if contents:
                contents = replace_contents(contents, _)

                file_split = each_doc_file.split(".")
                new_file = f'{file_split[0]}.{each_lang}.md'
                with open(f'{mycodo_root}/docs/{new_file}', 'w') as file1:
                    file1.write(contents)
