# -*- coding: utf-8 -*-
# From https://github.com/miguelgrinberg/flask-video-streaming
import time

import io
import picamera

from mycodo.mycodo_flask.camera.base_camera import BaseCamera


class Camera(BaseCamera):
    camera_options = None

    def set_camera_options(self, camera_options):
        self.camera_options = camera_options

    def frames(self):
        with picamera.PiCamera() as camera:
            camera.resolution = (self.camera_options.width,
                                 self.camera_options.height)
            camera.hflip = self.camera_options.hflip
            camera.vflip = self.camera_options.vflip
            camera.brightness = int(self.camera_options.brightness)
            camera.contrast = int(self.camera_options.contrast)
            camera.exposure_compensation = int(self.camera_options.exposure)
            camera.saturation = int(self.camera_options.saturation)
            camera.shutter_speed = self.camera_options.picamera_shutter_speed
            camera.sharpness = self.camera_options.picamera_sharpness
            camera.iso = self.camera_options.picamera_iso
            camera.awb_mode = self.camera_options.picamera_awb
            if self.camera_options.picamera_awb == 'off':
                camera.awb_gains = (
                    self.camera_options.picamera_awb_gain_red,
                    self.camera_options.picamera_awb_gain_blue)
            camera.exposure_mode = self.camera_options.picamera_exposure_mode
            camera.meter_mode = self.camera_options.picamera_meter_mode
            camera.image_effect = self.camera_options.picamera_image_effect

            # let camera warm up
            time.sleep(2)

            stream = io.BytesIO()
            for _ in camera.capture_continuous(
                    stream, 'jpeg', use_video_port=True):
                # return current frame
                stream.seek(0)
                time.sleep(0.3)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
