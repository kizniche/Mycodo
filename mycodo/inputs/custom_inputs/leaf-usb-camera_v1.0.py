# coding=utf-8
"""
Mycodo Custom Input Module: USB Camera (OpenCV), local-only.

This module has NO network listener/publisher of its own. It only:
  - captures images with OpenCV on a schedule you control, and
  - keeps the most recent image + metadata in memory inside the Mycodo
    input controller process.

The only way to get data out of it externally is through Mycodo's own
REST API -- there is no MQTT, no HTTP server, no socket opened by this
module itself.

INSTALLATION
------------
Copy this file into your Mycodo custom inputs directory, e.g.:

    ~/Mycodo/mycodo/inputs/custom_inputs/usb_camera_local.py

Restart the Mycodo daemon/frontend so it's picked up, then add it from
Configure -> Inputs -> "USB Camera (OpenCV, Local Only)".

HOW TO GET IMAGES OUT VIA THE MYCODO REST API
-----------------------------------------------
This Input exposes two custom actions. Mycodo's REST API lets you trigger
any custom Input action and read back its text response, so that's the
transport used here -- no other channel exists.

    1. "Capture Now"            action id: capture_now
       Captures a fresh frame immediately and caches it. Returns a short
       text confirmation (dimensions + size), not the image itself --
       use this when you just want to force a fresh capture before
       fetching it.

    2. "Get Last Image (base64)" action id: get_last_image_base64
       Returns the most recently captured JPEG, base64-encoded, as the
       action's text response. Decode the base64 string client-side to
       get the raw JPEG bytes.

Typical REST calls (check Mycodo's own API docs/Swagger UI on your
instance for the exact current path and auth scheme -- this has moved
around a bit across Mycodo versions):

    POST /api/input/actions/<input_unique_id>/capture_now
    POST /api/input/actions/<input_unique_id>/get_last_image_base64

Example client-side decode (Python):

    import base64, requests
    resp = requests.post(
        "https://<mycodo-host>/api/input/actions/<input_unique_id>/get_last_image_base64",
        headers={"X-API-KEY": "<your Mycodo API key>"})
    b64_payload = resp.json()["message"]   # field name depends on your Mycodo version
    with open("frame.jpg", "wb") as f:
        f.write(base64.b64decode(b64_payload))

Also, plain numeric health measurements (last capture success, image
size, seconds since last capture) are available the normal way any
Mycodo Input measurement is -- via the Input's Live page, graphs, or the
standard /api/measurements endpoints.

WHAT THIS DOES NOT DO
----------------------
- No MQTT client, no broker connection.
- No custom HTTP/socket server -- nothing listens on any port that this
  module itself opens.
- Does not write files anywhere by default (optional local disk caching
  is available via a custom option below, purely for convenience/
  debugging -- it changes nothing about external access, which is still
  only via Mycodo's own REST API).

CAPTURE MODES
-------------
    on_demand  - only ever captures when "Capture Now" is triggered
                 (via the UI button, a Mycodo Function/Trigger, or the
                 REST action endpoint above).
    interval   - additionally captures automatically every N seconds on
                 a background timer, so "Get Last Image (base64)" always
                 has something reasonably fresh cached even if nobody
                 has called "Capture Now" recently.

NOTES / CAVEATS
----------------
- This module is written against the general shape of Mycodo's custom
  Input API (AbstractInput, INPUT_INFORMATION, custom_options,
  custom_actions). Exact method names/signatures have shifted slightly
  across Mycodo versions -- if something doesn't line up (e.g.
  `setup_custom_options`), check `mycodo/inputs/examples/` in your
  Mycodo install for the current base class API.
- Base64-encoding a JPEG inflates it by ~33%. If your Mycodo version
  caps action response/message length, very large/high-quality frames
  could get truncated -- lower jpeg_quality or resolution if you hit
  that limit.
- The CameraController class has no Mycodo dependency and can be
  imported/tested standalone.
"""
import base64
import copy
import threading
import time

from mycodo.inputs.base_input import AbstractInput

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
    'input_name_unique': 'CUSTOM_USB_CAMERA_OPENCV_LOCAL',
    'input_manufacturer': 'Custom',
    'input_name': 'USB Camera (OpenCV, Local Only)',
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
            'id': 'camera_device',
            'type': 'text',
            'default_value': '0',
            'required': True,
            'name': 'Camera Device',
            'phrase': 'OpenCV camera index (e.g. 0, 1) or device path (e.g. /dev/video0)'
        },
        {
            'id': 'camera_backend',
            'type': 'select',
            'default_value': 'AUTO',
            'options_select': [
                ('AUTO', 'Auto'),
                ('V4L2', 'Video4Linux2 (Linux)'),
                ('DSHOW', 'DirectShow (Windows)')
            ],
            'name': 'Camera Backend',
            'phrase': 'OpenCV capture backend hint'
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
            'default_value': 85,
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
            'default_value': False,
            'name': 'Also Save Last Image To Disk',
            'phrase': 'Convenience only -- does not change external access, which is REST-only'
        },
        {
            'id': 'save_path',
            'type': 'text',
            'default_value': '/home/mycodo_camera_last.jpg',
            'required': False,
            'name': 'Disk Save Path',
            'phrase': 'File path to overwrite with the latest capture, if enabled above'
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
class CameraController:
    """Wraps an OpenCV VideoCapture with basic settings + JPEG encode."""

    def __init__(self, logger, options):
        self.logger = logger
        self.opts = options
        self.cap = None

    def _device_arg(self):
        dev = str(self.opts['camera_device']).strip()
        try:
            return int(dev)
        except ValueError:
            return dev

    def _backend_flag(self):
        import cv2
        return {
            'V4L2': getattr(cv2, 'CAP_V4L2', 0),
            'DSHOW': getattr(cv2, 'CAP_DSHOW', 0),
            'AUTO': cv2.CAP_ANY
        }.get(self.opts.get('camera_backend', 'AUTO'), cv2.CAP_ANY)

    def open(self):
        import cv2
        device = self._device_arg()
        backend = self._backend_flag()
        self.cap = cv2.VideoCapture(device, backend) if backend else cv2.VideoCapture(device)

        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera device: {device}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.opts['resolution_width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.opts['resolution_height'])
        if self.opts.get('fps'):
            self.cap.set(cv2.CAP_PROP_FPS, self.opts['fps'])

        if self.opts.get('brightness', -1) >= 0:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.opts['brightness'])
        if self.opts.get('contrast', -1) >= 0:
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.opts['contrast'])
        if self.opts.get('saturation', -1) >= 0:
            self.cap.set(cv2.CAP_PROP_SATURATION, self.opts['saturation'])

        if self.opts.get('auto_exposure', True):
            # 3 = auto on most V4L2 backends, 0.75 on some UVC drivers
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        else:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            if self.opts.get('exposure', -1) >= 0:
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.opts['exposure'])

        self.logger.info(
            f"Camera opened: device={device} "
            f"{self.opts['resolution_width']}x{self.opts['resolution_height']}"
        )

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

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
        """Grab one frame, apply post-processing, return (jpeg_bytes, w, h)."""
        import cv2
        if self.cap is None or not self.cap.isOpened():
            self.open()

        # Flush a stale buffered frame, then grab a fresh one.
        self.cap.read()
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("Failed to read frame from camera")

        frame = self._post_process(frame)
        quality = int(self.opts.get('jpeg_quality', 85))
        ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            raise RuntimeError("Failed to JPEG-encode frame")

        h, w = frame.shape[:2]
        return buf.tobytes(), w, h


# =========================================================================
# Mycodo Input glue
# =========================================================================
class InputModule(AbstractInput):
    """Mycodo Input wrapper around CameraController, no networking of its own."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

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
        # (e.g. self.camera_device, self.jpeg_quality, ...) via this call
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
                if options.get('save_to_disk') and options.get('save_path'):
                    try:
                        with open(options['save_path'], 'wb') as f:
                            f.write(jpeg_bytes)
                    except OSError as e:
                        self.logger.error(f"Could not write image to disk cache: {e}")

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
