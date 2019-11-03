# -*- coding: utf-8 -*-
# From https://github.com/miguelgrinberg/flask-video-streaming
import logging
import time

import io
import picamera

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
        with picamera.PiCamera() as camera:
            camera.resolution = (settings.resolution_stream_width,
                                 settings.resolution_stream_height)
            camera.hflip = settings.hflip
            camera.vflip = settings.vflip
            camera.rotation = settings.rotation
            camera.brightness = int(settings.brightness)
            camera.contrast = int(settings.contrast)
            camera.exposure_compensation = int(settings.exposure)
            camera.saturation = int(settings.saturation)
            camera.shutter_speed = settings.picamera_shutter_speed
            camera.sharpness = settings.picamera_sharpness
            camera.iso = settings.picamera_iso
            camera.awb_mode = settings.picamera_awb
            if settings.picamera_awb == 'off':
                camera.awb_gains = (settings.picamera_awb_gain_red,
                                    settings.picamera_awb_gain_blue)
            camera.exposure_mode = settings.picamera_exposure_mode
            camera.meter_mode = settings.picamera_meter_mode
            camera.image_effect = settings.picamera_image_effect

            # let camera warm up
            time.sleep(2)

            stream = io.BytesIO()
            for _ in camera.capture_continuous(
                    stream, 'jpeg', use_video_port=True):
                # return current frame
                stream.seek(0)
                time.sleep(0.05)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
