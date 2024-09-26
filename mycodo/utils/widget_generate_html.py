import grp
import logging
import os
import pwd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.realpath(__file__), '../../..')))

from mycodo.config import PATH_TEMPLATE_USER
from mycodo.utils.widgets import parse_widget_information

logger = logging.getLogger("mycodo.utils.widget_generate_html")


def set_user_grp(filepath, user, group):
    """Set the UID and GUID of a file."""
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    os.chown(filepath, uid, gid)


def assure_path_exists(path):
    """Create path if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        os.chmod(path, 0o774)
        set_user_grp(path, 'mycodo', 'mycodo')
    return path


def generate_widget_html():
    """Generate all HTML files for all widgets."""
    error = []
    dict_widgets = parse_widget_information()
    assure_path_exists(PATH_TEMPLATE_USER)

    for widget_name in dict_widgets:
        try:
            filename_head = f"widget_template_{widget_name}_head.html"
            path_head = os.path.join(PATH_TEMPLATE_USER, filename_head)
            with open(path_head, 'w') as fw:
                if 'widget_dashboard_head' in dict_widgets[widget_name]:
                    html_head = dict_widgets[widget_name]['widget_dashboard_head']
                else:
                    html_head = ""
                fw.write(html_head)
                fw.close()
            set_user_grp(path_head, 'mycodo', 'mycodo')

            filename_title_bar = f"widget_template_{widget_name}_title_bar.html"
            path_title_bar = os.path.join(PATH_TEMPLATE_USER, filename_title_bar)
            with open(path_title_bar, 'w') as fw:
                if 'widget_dashboard_title_bar' in dict_widgets[widget_name]:
                    html_title_bar = dict_widgets[widget_name]['widget_dashboard_title_bar']
                else:
                    html_title_bar = ""
                fw.write(html_title_bar)
                fw.close()
            set_user_grp(path_title_bar, 'mycodo', 'mycodo')

            filename_body = f"widget_template_{widget_name}_body.html"
            path_body = os.path.join(PATH_TEMPLATE_USER, filename_body)
            with open(path_body, 'w') as fw:
                if 'widget_dashboard_body' in dict_widgets[widget_name]:
                    html_body = dict_widgets[widget_name]['widget_dashboard_body']
                else:
                    html_body = ""
                fw.write(html_body)
                fw.close()
            set_user_grp(path_body, 'mycodo', 'mycodo')

            filename_configure_options = f"widget_template_{widget_name}_configure_options.html"
            path_configure_options = os.path.join(PATH_TEMPLATE_USER, filename_configure_options)
            with open(path_configure_options, 'w') as fw:
                if 'widget_dashboard_configure_options' in dict_widgets[widget_name]:
                    html_configure_options = dict_widgets[widget_name]['widget_dashboard_configure_options']
                else:
                    html_configure_options = ""
                fw.write(html_configure_options)
                fw.close()
            set_user_grp(path_configure_options, 'mycodo', 'mycodo')

            filename_js = f"widget_template_{widget_name}_js.html"
            path_js = os.path.join(PATH_TEMPLATE_USER, filename_js)
            with open(path_js, 'w') as fw:
                if 'widget_dashboard_js' in dict_widgets[widget_name]:
                    html_js = dict_widgets[widget_name]['widget_dashboard_js']
                else:
                    html_js = ""
                fw.write(html_js)
                fw.close()
            set_user_grp(path_js, 'mycodo', 'mycodo')

            filename_js_ready = f"widget_template_{widget_name}_js_ready.html"
            path_js_ready = os.path.join(PATH_TEMPLATE_USER, filename_js_ready)
            with open(path_js_ready, 'w') as fw:
                if 'widget_dashboard_js_ready' in dict_widgets[widget_name]:
                    html_js_ready = dict_widgets[widget_name]['widget_dashboard_js_ready']
                else:
                    html_js_ready = ""
                fw.write(html_js_ready)
                fw.close()
            set_user_grp(path_js_ready, 'mycodo', 'mycodo')

            filename_js_ready_end = f"widget_template_{widget_name}_js_ready_end.html"
            path_js_ready_end = os.path.join(PATH_TEMPLATE_USER, filename_js_ready_end)
            with open(path_js_ready_end, 'w') as fw:
                if 'widget_dashboard_js_ready_end' in dict_widgets[widget_name]:
                    html_js_ready_end = dict_widgets[widget_name]['widget_dashboard_js_ready_end']
                else:
                    html_js_ready_end = ""
                fw.write(html_js_ready_end)
                fw.close()
            set_user_grp(path_js_ready_end, 'mycodo', 'mycodo')
        except Exception as err:
            logger.exception(f"Generating widget HTML for widget: {widget_name}")
            error.append(f"Exception generating widget HTML for '{widget_name}' (see Web Log for full traceback): {err}")

    return error


if __name__ == "__main__":
    generate_widget_html()
