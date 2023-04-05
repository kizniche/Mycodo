# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os

from mycodo.config import PATH_CAMERAS
from mycodo.databases.models import CustomController
from mycodo.mycodo_flask.utils.utils_general import bytes2human
from mycodo.utils.database import db_retrieve_table_daemon

logger = logging.getLogger("mycodo.camera_functions")


def get_camera_function_paths(unique_id):
    """Retrieve still/timelapse paths for the given camera function ID"""
    camera_path = os.path.join(PATH_CAMERAS, unique_id)

    function = db_retrieve_table_daemon(
        CustomController, unique_id=unique_id)

    try:
        custom_options = json.loads(function.custom_options)
    except:
        custom_options = {}

    if 'custom_path_still' in custom_options and custom_options['custom_path_still']:
        still_path = custom_options['custom_path_still']
    else:
        still_path = os.path.join(camera_path, 'still')

    if 'custom_path_video' in custom_options and custom_options['custom_path_video']:
        video_path = custom_options['custom_path_video']
    else:
        video_path = os.path.join(camera_path, 'video')

    if 'custom_path_timelapse' in custom_options and custom_options['custom_path_timelapse']:
        tl_path = custom_options['custom_path_timelapse']
    else:
        tl_path = os.path.join(camera_path, 'timelapse')

    return still_path, video_path, tl_path


def get_camera_function_image_info(unique_id):
    """Retrieve information about the latest camera images."""
    latest_img_still_ts = None
    latest_img_still_size = None
    latest_img_still = None
    latest_img_video_ts = None
    latest_img_video_size = None
    latest_img_video = None
    latest_img_tl_ts = None
    latest_img_tl_size = None
    latest_img_tl = None
    time_lapse_imgs = None

    still_path, video_path, tl_path = get_camera_function_paths(unique_id)

    function = db_retrieve_table_daemon(
        CustomController, unique_id=unique_id)

    try:
        custom_options = json.loads(function.custom_options)
    except:
        custom_options = {}

    if (('still_last_file' in custom_options and custom_options['still_last_file']) and
            ('still_last_ts' in custom_options and custom_options['still_last_ts'])):
        latest_img_still_ts = datetime.datetime.fromtimestamp(
            custom_options['still_last_ts']).strftime("%Y-%m-%d %H:%M:%S")
        latest_img_still = custom_options['still_last_file']
        file_still_path = os.path.join(still_path, custom_options['still_last_file'])
        if os.path.exists(file_still_path):
            latest_img_still_size = bytes2human(os.path.getsize(file_still_path))
    else:
        latest_img_still = None


    if (('video_last_file' in custom_options and custom_options['video_last_file']) and
            ('video_last_ts' in custom_options and custom_options['video_last_ts'])):
        latest_img_video_ts = datetime.datetime.fromtimestamp(
            custom_options['video_last_ts']).strftime("%Y-%m-%d %H:%M:%S")
        latest_img_video = custom_options['video_last_file']
        file_video_path = os.path.join(video_path, custom_options['video_last_file'])
        if os.path.exists(file_video_path):
            latest_img_video_size = bytes2human(os.path.getsize(file_video_path))
    else:
        latest_img_video = None

    try:
        # Get list of timelapse filename sets for generating a video from images
        time_lapse_imgs = []
        for i in os.listdir(tl_path):
            if (os.path.isfile(os.path.join(tl_path, i)) and
                    i[:-10] not in time_lapse_imgs):
                time_lapse_imgs.append(i[:-10])
        time_lapse_imgs.sort()
    except Exception:
        pass

    if (('tl_last_file' in custom_options and custom_options['tl_last_file']) and
            ('tl_last_ts' in custom_options and custom_options['tl_last_ts'])):
        latest_img_tl_ts = datetime.datetime.fromtimestamp(
            custom_options['tl_last_ts']).strftime("%Y-%m-%d %H:%M:%S")
        latest_img_tl = custom_options['tl_last_file']
        file_tl_path = os.path.join(tl_path, custom_options['tl_last_file'])
        if os.path.exists(file_tl_path):
            latest_img_tl_size = bytes2human(os.path.getsize(file_tl_path))
    else:
        latest_img_tl = None

    return (latest_img_still_ts, latest_img_still_size, latest_img_still,
            latest_img_video_ts, latest_img_video_size, latest_img_video,
            latest_img_tl_ts, latest_img_tl_size, latest_img_tl, time_lapse_imgs)
