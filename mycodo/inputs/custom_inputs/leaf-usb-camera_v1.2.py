# -----------------------------------------------------------------------
# LEAF USB Camera MyCodo Module
# Built with OpenCV
# Version: 1.2
# Date: 09/15/2026
# Author: Joseph Kudia @ Luce Labs
# -----------------------------------------------------------------------

# coding=utf-8

import base64
import copy
import os
import re
import threading
import time

from mycodo.inputs.base_input import AbstractInput

# -----------------------------------------------------------------------
# Fixed USB port -> stable device path mapping for this Raspberry Pi.
#
# Confirmed by running identify_cameras.sh with one camera plugged into
# each of the 4 physical USB ports in turn -- each port enumerates under
# the same PCIe/USB controller path with only the final ".N" segment
# (1.1 / 1.2 / 1.3 / 1.4) changing per port. "video-index0" is the actual
# capture-capable node for these cameras (video-index1 is metadata-only).
#
# If this module is ever deployed on different Raspberry Pi hardware (a
# different Pi model can have a different PCIe/USB controller address),
# re-run identify_cameras.sh with one camera per port and update this
# template's prefix to match.
# -----------------------------------------------------------------------
USB_PORT_DEVICE_TEMPLATE = (
    "/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-"
    "usb-0:1.{port}:1.0-video-index0"
)

# -----------------------------------------------------------------------
# Measurement definitions (shown in Mycodo graphs/dashboards)
# -----------------------------------------------------------------------
measurements_dict = {
    0: {
        'measurement': 'boolean',
        'unit': 'bool',
        'name': 'Last Capture Success'
    },
    1: {
        'measurement': 'unitless',
        'unit': 'unitless',
        'name': 'Last Image Size (bytes)'
    },
    2: {
        'measurement': 'duration_time',
        'unit': 's',
        'name': 'Seconds Since Last Capture'
    }
}

# -----------------------------------------------------------------------
# Mycodo Input registration metadata
# -----------------------------------------------------------------------
INPUT_INFORMATION = {
    'input_name_unique': 'leaf_usb_camera_v1_2',
    'input_manufacturer': 'Luce Labs',
    'input_name': 'LEAF USB Camera',
    'input_library': 'opencv-python-headless',
    'measurements_name': 'Camera Status',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'options_enabled': [
        'custom_options',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'cv2', 'opencv-python-headless')
    ],

    'interfaces': ['Mycodo'],

    'custom_options': [
        # ---------------- Camera device ----------------
        {
            'id': 'usb_port',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', 'USB Port 1'),
                ('2', 'USB Port 2'),
                ('3', 'USB Port 3'),
                ('4', 'USB Port 4')
            ],
            'name': 'USB Port',
            'phrase':
                'See documentation for more info'
        },
        # ---------------- Basic camera settings ----------------
        {
            'id': 'resolution_width',
            'type': 'integer',
            'default_value': 1280,
            'required': True,
            'name': 'Resolution Width',
            'phrase': 'Capture width in pixels'
        },
        {
            'id': 'resolution_height',
            'type': 'integer',
            'default_value': 720,
            'required': True,
            'name': 'Resolution Height',
            'phrase': 'Capture height in pixels'
        },
        {
            'id': 'fps',
            'type': 'integer',
            'default_value': 15,
            'required': False,
            'name': 'FPS',
            'phrase': 'Requested capture frame rate (camera-dependent)'
        },
        {
            'id': 'brightness',
            'type': 'float',
            'default_value': -1,
            'required': False,
            'name': 'Brightness',
            'phrase': 'Camera brightness (-1 = leave at camera default)'
        },
        {
            'id': 'contrast',
            'type': 'float',
            'default_value': -1,
            'required': False,
            'name': 'Contrast',
            'phrase': 'Camera contrast (-1 = leave at camera default)'
        },
        {
            'id': 'saturation',
            'type': 'float',
            'default_value': -1,
            'required': False,
            'name': 'Saturation',
            'phrase': 'Camera saturation (-1 = leave at camera default)'
        },
        {
            'id': 'auto_exposure',
            'type': 'bool',
            'default_value': True,
            'name': 'Auto Exposure',
            'phrase': 'Enable camera auto-exposure'
        },
        {
            'id': 'exposure',
            'type': 'float',
            'default_value': -1,
            'required': False,
            'name': 'Manual Exposure',
            'phrase': 'Exposure value when Auto Exposure is disabled (-1 = leave at camera default)'
        },
        {
            'id': 'rotation',
            'type': 'select',
            'default_value': '0',
            'options_select': [
                ('0', '0 degrees'),
                ('90', '90 degrees clockwise'),
                ('180', '180 degrees'),
                ('270', '270 degrees clockwise')
            ],
            'name': 'Rotation',
            'phrase': 'Rotate captured image'
        },
        {
            'id': 'flip_horizontal',
            'type': 'bool',
            'default_value': False,
            'name': 'Flip Horizontal',
            'phrase': 'Mirror image left/right'
        },
        {
            'id': 'flip_vertical',
            'type': 'bool',
            'default_value': False,
            'name': 'Flip Vertical',
            'phrase': 'Mirror image top/bottom'
        },
        {
            'id': 'jpeg_quality',
            'type': 'integer',
            'default_value': 100,
            'required': True,
            'name': 'JPEG Quality',
            'phrase': 'JPEG encode quality, 1-100 (lower = smaller base64 payload)'
        },

        # ---------------- Capture mode (local only) ----------------
        {
            'id': 'capture_mode',
            'type': 'select',
            'default_value': 'interval',
            'options_select': [
                ('on_demand', 'On demand only (Capture Now / REST action)'),
                ('interval', 'On demand + automatic every X seconds')
            ],
            'name': 'Capture Mode',
            'phrase': 'Whether images are also captured automatically in the background'
        },
        {
            'id': 'capture_interval_seconds',
            'type': 'integer',
            'default_value': 60,
            'required': False,
            'name': 'Auto-Capture Interval (seconds)',
            'phrase': 'Used only when Capture Mode includes automatic capture'
        },

        # ---------------- Optional local disk cache ----------------
        {
            'id': 'save_to_disk',
            'type': 'bool',
            'default_value': True,
            'name': 'Also Save Last Image To Disk',
            'phrase':
                'Saves to the path derived from this Input\'s Name, '
                'which must be set to the format tentNN/towerNN/shelfNN/cameraNN '
                '(e.g. Camera Name: tent01/tower01/shelf01/camera01) -- saves to '
                '/home/tent01/tower01/shelf01/camera01/latest.jpeg'
        }
    ],

    'custom_actions_message':
        '"Capture Now" forces an immediate capture and reports its size. '
        '"Get Last Image (base64)" returns the most recent captured JPEG, '
        'base64-encoded, in the action response -- this is the only way '
        'image data leaves this module, and it only happens when this '
        'action is explicitly called (e.g. via the Mycodo REST API).',
    'custom_actions': [
        {
            'id': 'capture_now',
            'type': 'button',
            'name': 'Capture Now'
        },
        {
            'id': 'get_last_image_base64',
            'type': 'button',
            'name': 'Get Last Image (base64)'
        }
    ]
}


# =========================================================================
# Plain-Python helper class (no Mycodo dependency; reusable/testable)
# =========================================================================
# All 4 physical USB ports on this Pi share one upstream USB controller,
# so simultaneous captures from two different cameras can still corrupt
# both, the same way one persistently-open stream used to. This lock is
# process-wide (shared by every CameraController instance / every camera
# Input running in this Mycodo daemon), so at most one camera is ever
# mid-capture at a time, regardless of which USB port it's on.
_GLOBAL_USB_CAPTURE_LOCK = threading.Lock()


class CameraController:
    """Wraps an OpenCV VideoCapture with basic settings + JPEG encode."""

    def __init__(self, logger, options):
        self.logger = logger
        self.opts = options

    def _device_arg(self):
        port = str(self.opts['usb_port']).strip()
        return USB_PORT_DEVICE_TEMPLATE.format(port=port)

    def _configure(self, cap):
        import cv2
        # Request MJPG (compressed) rather than the raw default -- this
        # cuts the USB bandwidth needed per stream substantially, which
        # matters a lot here since all 4 physical USB ports share one
        # upstream USB controller on this Pi. Must be set before
        # width/height for it to take effect on most UVC cameras.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.opts['resolution_width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.opts['resolution_height'])
        if self.opts.get('fps'):
            cap.set(cv2.CAP_PROP_FPS, self.opts['fps'])

        if self.opts.get('brightness', -1) >= 0:
            cap.set(cv2.CAP_PROP_BRIGHTNESS, self.opts['brightness'])
        if self.opts.get('contrast', -1) >= 0:
            cap.set(cv2.CAP_PROP_CONTRAST, self.opts['contrast'])
        if self.opts.get('saturation', -1) >= 0:
            cap.set(cv2.CAP_PROP_SATURATION, self.opts['saturation'])

        if self.opts.get('auto_exposure', True):
            # 3 = auto on most V4L2 backends, 0.75 on some UVC drivers
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        else:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            if self.opts.get('exposure', -1) >= 0:
                cap.set(cv2.CAP_PROP_EXPOSURE, self.opts['exposure'])

    def open(self):
        """Validate the device opens and configures cleanly, then close it
        again immediately. Used only as a fail-fast check on Input
        activation -- actual captures open/close the device fresh each
        time (see capture_jpeg), so this does not leave anything open.
        """
        import cv2
        device = self._device_arg()
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Could not open camera device: {device}")

        self._configure(cap)
        cap.release()

        self.logger.info(
            f"Camera check OK: device={device} "
            f"{self.opts['resolution_width']}x{self.opts['resolution_height']}"
        )

    def close(self):
        # No persistent handle is kept open anymore (see capture_jpeg),
        # so there is nothing to release here. Kept as a no-op for
        # interface compatibility with the Input controller's stop_input().
        pass

    def _post_process(self, frame):
        import cv2
        rotation = int(self.opts.get('rotation', 0))
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        if self.opts.get('flip_horizontal') and self.opts.get('flip_vertical'):
            frame = cv2.flip(frame, -1)
        elif self.opts.get('flip_horizontal'):
            frame = cv2.flip(frame, 1)
        elif self.opts.get('flip_vertical'):
            frame = cv2.flip(frame, 0)

        return frame

    def capture_jpeg(self):
        """Open the device fresh, grab one frame, close it again, return
        (jpeg_bytes, w, h).

        Opening/closing per capture (rather than holding the device open
        continuously) means each of the 4 cameras on this Pi only holds
        USB bandwidth for the brief moment it's actually grabbing a
        frame, instead of all 4 permanently reserving bandwidth on the
        shared upstream USB controller -- which is what was causing
        corrupted/green frames on whichever camera activated last.

        The whole sequence is also serialized process-wide via
        _GLOBAL_USB_CAPTURE_LOCK, so two different cameras can never be
        mid-capture at the same instant either -- without this, two
        cameras with similar capture intervals could eventually drift
        into firing at the same moment and corrupt each other even with
        the open-per-capture change above.
        """
        with _GLOBAL_USB_CAPTURE_LOCK:
            return self._do_capture_jpeg()

    def _do_capture_jpeg(self):
        import cv2
        device = self._device_arg()
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

        try:
            if not cap.isOpened():
                raise RuntimeError(f"Could not open camera device: {device}")

            self._configure(cap)

            # Discard a couple of frames while auto-exposure/gain settle
            # and the format switch takes effect, then grab the real one.
            for _ in range(2):
                cap.read()
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("Failed to read frame from camera")

            frame = self._post_process(frame)
            quality = int(self.opts.get('jpeg_quality', 85))
            ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            if not ok:
                raise RuntimeError("Failed to JPEG-encode frame")

            h, w = frame.shape[:2]
            return buf.tobytes(), w, h
        finally:
            cap.release()


# =========================================================================
# Mycodo Input glue
# =========================================================================
class InputModule(AbstractInput):
    """Mycodo Input wrapper around CameraController, no networking of its own."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        # Stored explicitly so self.input_dev.name (the Input's standard
        # Mycodo "Name" field) is reliably available later, regardless of
        # whether the base class also stores it under the same attribute.
        self.input_dev = input_dev

        self.camera = None
        self.interval_thread = None
        self.stop_event = threading.Event()
        self.capture_lock = threading.Lock()

        self.last_image_bytes = None
        self.last_image_width = None
        self.last_image_height = None
        self.last_success = None
        self.last_capture_time = None

        # Custom option fields become attributes named after their 'id'
        # (e.g. self.usb_port, self.jpeg_quality, ...) via this call
        # in most recent Mycodo versions. If your Mycodo version instead
        # exposes them only through self.input_dev.custom_options, replace
        # this with the appropriate parsing call from
        # mycodo/inputs/examples/.
        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        options = self._collect_options()

        location_id = self._get_location_id()
        save_path = self._build_save_path(location_id)
        self.logger.info(f"Location identifier for this camera: {location_id}")
        if options.get('save_to_disk'):
            self.logger.info(f"Images will be saved to: {save_path}")

        self.camera = CameraController(self.logger, options)
        self.camera.open()

        # Always do one capture on activation so there's something cached
        # immediately, regardless of capture_mode.
        self._capture_and_cache()

        if options['capture_mode'] == 'interval':
            self._start_interval_thread(options['capture_interval_seconds'])

    def _collect_options(self):
        """Pull all declared custom_options off self into a plain dict."""
        options = {}
        for opt in INPUT_INFORMATION['custom_options']:
            options[opt['id']] = getattr(self, opt['id'], opt.get('default_value'))
        return options

    def _get_location_id(self):
        """Derive the location identifier directly from this Input's own
        Mycodo 'Name' field, which must be set to the format
        tentNN/towerNN/shelfNN/cameraNN (e.g. tent02/tower02/shelf03/camera02).

        Reading self.input_dev.name is a standard, safe operation for any
        Mycodo Input module (unlike writing to it, which isn't supported
        from within a custom Input) -- so this direction works reliably.
        """
        name = (getattr(self.input_dev, 'name', None) or '').strip()
        pattern = r'^tent\d+/tower\d+/shelf\d+/camera\d+$'
        if not re.match(pattern, name, re.IGNORECASE):
            self.logger.warning(
                f"This Input's Name ('{name}') doesn't match the expected "
                f"format 'tentNN/towerNN/shelfNN/cameraNN' (e.g. "
                f"'tent02/tower02/shelf03/camera02'). Disk save path (if "
                f"enabled) will use the Name as-is, which may not produce "
                f"the intended directory structure. Rename the Input to fix."
            )
        return name

    @staticmethod
    def _build_save_path(location_id):
        """e.g. 'tent02/tower02/shelf03/camera02' -> '/home/tent02/tower02/shelf03/camera02/latest.jpeg'"""
        return f"/home/{location_id}/latest.jpeg"

    def _start_interval_thread(self, interval_seconds):
        interval_seconds = max(1, int(interval_seconds or 60))

        def loop():
            while not self.stop_event.wait(interval_seconds):
                try:
                    self._capture_and_cache()
                except Exception as e:
                    self.logger.error(f"Interval capture failed: {e}")

        self.interval_thread = threading.Thread(target=loop, daemon=True)
        self.interval_thread.start()
        self.logger.info(f"Automatic background capture started: every {interval_seconds}s")

    def _capture_and_cache(self):
        """Capture one frame and store it in memory (and optionally disk).

        Thread-safe: shared by the interval thread, the Capture Now
        action, and Mycodo's own get_measurement() polling.
        """
        with self.capture_lock:
            try:
                jpeg_bytes, w, h = self.camera.capture_jpeg()
                self.last_image_bytes = jpeg_bytes
                self.last_image_width = w
                self.last_image_height = h
                self.last_success = True
                self.last_capture_time = time.time()
                self.logger.debug(f"Captured image: {w}x{h}, {len(jpeg_bytes)} bytes")

                options = self._collect_options()
                if options.get('save_to_disk'):
                    location_id = self._get_location_id()
                    save_path = self._build_save_path(location_id)
                    try:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(jpeg_bytes)
                    except OSError as e:
                        self.logger.error(f"Could not write image to disk cache ({save_path}): {e}")

                return jpeg_bytes, w, h
            except Exception as e:
                self.last_success = False
                self.logger.error(f"Capture failed: {e}")
                raise

    # ---- Mycodo Action button / REST action: "Capture Now" ----
    def capture_now(self, args_dict=None):
        try:
            _, w, h = self._capture_and_cache()
            size = len(self.last_image_bytes)
            return f"Captured {w}x{h} image, {size} bytes", 0
        except Exception as e:
            return f"Capture failed: {e}", 1

    # ---- Mycodo Action button / REST action: "Get Last Image (base64)" ----
    def get_last_image_base64(self, args_dict=None):
        if self.last_image_bytes is None:
            return "No image captured yet", 1
        encoded = base64.b64encode(self.last_image_bytes).decode('ascii')
        return encoded, 0

    # ---- Mycodo periodic measurement callback ----
    def get_measurement(self):
        self.return_dict = copy.deepcopy(measurements_dict)

        self.value_set(0, 1 if self.last_success else 0)
        if self.last_image_bytes is not None:
            self.value_set(1, len(self.last_image_bytes))
        if self.last_capture_time is not None:
            self.value_set(2, round(time.time() - self.last_capture_time, 1))

        return self.return_dict

    def stop_input(self):
        self.stop_event.set()
        if self.interval_thread is not None:
            self.interval_thread.join(timeout=5)
        if self.camera is not None:
            self.camera.close()
        super().stop_input()
