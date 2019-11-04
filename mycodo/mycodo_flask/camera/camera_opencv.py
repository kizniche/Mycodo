# -*- coding: utf-8 -*-
# From https://github.com/miguelgrinberg/flask-video-streaming
import logging
import time

import cv2

from mycodo.mycodo_flask.camera.base_camera import BaseCamera

logger = logging.getLogger(__name__)


class Camera(BaseCamera):
    camera_options = None

    @staticmethod
    def set_camera_options(camera_options):
        logger.info("Setting camera options")
        Camera.camera_options = camera_options

    @staticmethod
    def frames():
        settings = Camera.camera_options

        camera = cv2.VideoCapture(settings.opencv_device)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings.resolution_stream_width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.resolution_stream_height)
        camera.set(cv2.CAP_PROP_EXPOSURE, settings.exposure)
        camera.set(cv2.CAP_PROP_GAIN, settings.gain)
        camera.set(cv2.CAP_PROP_BRIGHTNESS, settings.brightness)
        camera.set(cv2.CAP_PROP_CONTRAST, settings.contrast)
        camera.set(cv2.CAP_PROP_HUE, settings.hue)
        camera.set(cv2.CAP_PROP_SATURATION, settings.saturation)

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            time.sleep(0.05)
            yield cv2.imencode('.jpg', img)[1].tobytes()
