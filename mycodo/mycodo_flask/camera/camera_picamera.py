# -*- coding: utf-8 -*-
#
# From https://github.com/miguelgrinberg/flask-video-streaming
#
import io
import time
import picamera
from base_camera import BaseCamera


class Camera(BaseCamera):
    camera_options = None

    @staticmethod
    def set_camera_options(camera_options):
        Camera.camera_options = camera_options

    @staticmethod
    def frames():
        with picamera.PiCamera() as camera:
            camera.resolution = (Camera.camera_options.width,
                                 Camera.camera_options.height)
            camera.hflip = Camera.camera_options.hflip
            camera.vflip = Camera.camera_options.vflip
            camera.brightness = int(Camera.camera_options.brightness)
            camera.contrast = int(Camera.camera_options.contrast)
            camera.exposure_compensation = int(Camera.camera_options.exposure)
            camera.saturation = int(Camera.camera_options.saturation)

            # let camera warm up
            time.sleep(2)

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, 'jpeg',
                                               use_video_port=True):
                # return current frame
                stream.seek(0)
                time.sleep(0.1)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
