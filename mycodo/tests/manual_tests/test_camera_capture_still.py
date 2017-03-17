#!/usr/bin/python
# coding=utf-8
import cv2
import datetime
import sys


def count_cameras_opencv():
    num_cameras = 0
    for i in range(10):
        temp_camera = cv2.VideoCapture(i-1)
        ret, _ = temp_camera.read()
        if ret:
            num_cameras += 1
    return num_cameras


def main():
    #   0  CV_CAP_PROP_POS_MSEC Current position of the video file in milliseconds.
    #   1  CV_CAP_PROP_POS_FRAMES 0-based index of the frame to be decoded/captured next.
    #   2  CV_CAP_PROP_POS_AVI_RATIO Relative position of the video file
    #   3  CV_CAP_PROP_FRAME_WIDTH Width of the frames in the video stream.
    #   4  CV_CAP_PROP_FRAME_HEIGHT Height of the frames in the video stream.
    #   5  CV_CAP_PROP_FPS Frame rate.
    #   6  CV_CAP_PROP_FOURCC 4-character code of codec.
    #   7  CV_CAP_PROP_FRAME_COUNT Number of frames in the video file.
    #   8  CV_CAP_PROP_FORMAT Format of the Mat objects returned by retrieve() .
    #   9 CV_CAP_PROP_MODE Backend-specific value indicating the current capture mode.
    #   10 CV_CAP_PROP_BRIGHTNESS Brightness of the image (only for cameras).
    #   11 CV_CAP_PROP_CONTRAST Contrast of the image (only for cameras).
    #   12 CV_CAP_PROP_SATURATION Saturation of the image (only for cameras).
    #   13 CV_CAP_PROP_HUE Hue of the image (only for cameras).
    #   14 CV_CAP_PROP_GAIN Gain of the image (only for cameras).
    #   15 CV_CAP_PROP_EXPOSURE Exposure (only for cameras).
    #   16 CV_CAP_PROP_CONVERT_RGB Boolean flags indicating whether images should be converted to RGB.
    #   17 CV_CAP_PROP_WHITE_BALANCE Currently unsupported
    #   18 CV_CAP_PROP_RECTIFICATION Rectification flag for stereo cameras (note: only supported by DC1394 v 2.x backend currently)

    cap = cv2.VideoCapture(0)

    # Check if image can be read
    if not cap.read():
        print("Cannot detect camera")
        sys.exit()

    # cap.set(cv2.cv.CV_CAP_PROP_EXPOSURE, 1.0)
    # cap.set(cv2.cv.CV_CAP_PROP_GAIN, 4.0)
    # cap.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, 144.0)
    # cap.set(cv2.cv.CV_CAP_PROP_CONTRAST, 27.0)
    # cap.set(cv2.cv.CV_CAP_PROP_HUE, 13.0) # 13.0
    # cap.set(cv2.cv.CV_CAP_PROP_SATURATION, 0.0)

    # Read the current setting from the camera
    height = cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
    width = cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    brightness = cap.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS)
    contrast = cap.get(cv2.cv.CV_CAP_PROP_CONTRAST)
    saturation = cap.get(cv2.cv.CV_CAP_PROP_SATURATION)
    hue = cap.get(cv2.cv.CV_CAP_PROP_HUE)
    gain = cap.get(cv2.cv.CV_CAP_PROP_GAIN)
    exposure = cap.get(cv2.cv.CV_CAP_PROP_EXPOSURE)

    cap.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, brightness)
    cap.set(cv2.cv.CV_CAP_PROP_CONTRAST, contrast)
    cap.set(cv2.cv.CV_CAP_PROP_SATURATION, saturation)
    cap.set(cv2.cv.CV_CAP_PROP_HUE, hue)
    cap.set(cv2.cv.CV_CAP_PROP_GAIN, gain)
    cap.set(cv2.cv.CV_CAP_PROP_EXPOSURE, exposure)

    print("Height: {}".format(height))
    print("Width: {}".format(width))
    print("Brightness: {}".format(brightness))
    print("Contrast: {}".format(contrast))
    print("Saturation: {}".format(saturation))
    print("Hue: {}".format(hue))
    print("Gain: {}".format(gain))
    print("Exposure: {}".format(exposure))

    # Save image
    _, img = cap.read()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cv2.imwrite("camera_image_{ts}.bmp".format(ts=timestamp), img)
    cap.release()

    print("Cameras: {cams}".format(cams=count_cameras_opencv()))


if __name__ == '__main__':
    main()
