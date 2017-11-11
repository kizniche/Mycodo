# -*- coding: utf-8 -*-
#
# From https://github.com/miguelgrinberg/flask-video-streaming
#
import cv2
import imutils
import time
from base_camera import BaseCamera


class Camera(BaseCamera):
    camera_options = None

    @staticmethod
    def set_camera_options(camera_options):
        Camera.camera_options = camera_options

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(Camera.camera_options.opencv_device)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, Camera.camera_options.width)
        camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, Camera.camera_options.height)
        camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE, Camera.camera_options.exposure)
        camera.set(cv2.cv.CV_CAP_PROP_GAIN, Camera.camera_options.gain)
        camera.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, Camera.camera_options.brightness)
        camera.set(cv2.cv.CV_CAP_PROP_CONTRAST, Camera.camera_options.contrast)
        camera.set(cv2.cv.CV_CAP_PROP_HUE, Camera.camera_options.hue)
        camera.set(cv2.cv.CV_CAP_PROP_SATURATION, Camera.camera_options.saturation)

        while True:
            # read current frame
            _, img = camera.read()
            camera.release()

            if Camera.camera_options.hflip and Camera.camera_options.vflip:
                img = cv2.flip(img, -1)
            elif Camera.camera_options.hflip:
                img = cv2.flip(img, 1)
            elif Camera.camera_options.vflip:
                img = cv2.flip(img, 0)

            if Camera.camera_options.rotation:
                img = imutils.rotate_bound(
                    img, Camera.camera_options.rotation)

            time.sleep(0.1)

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()
