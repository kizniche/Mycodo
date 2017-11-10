# coding=utf-8
import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = 0

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames(opencv_device):
        if opencv_device is None:
            raise RuntimeError('Cannot stream: No opencv device selected')

        camera = cv2.VideoCapture(opencv_device)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()
