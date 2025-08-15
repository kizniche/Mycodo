Custom Input Modules for Mycodo

This folder is where you can place your own Input modules without modifying the core Mycodo source. Files here are preserved across upgrades.

Quick start (summary of the official guide):

1) Read the full guide
   - Wiki: https://github.com/kizniche/Mycodo/wiki/Building-a-Custom-Input-Module

2) Copy the template
   - Copy custom_input_template.py to a new file (e.g., my_sensor.py) in this same directory.

3) Edit metadata and measurements
   - In your new file, set INPUT_INFORMATION with:
     - input_name_unique: A globally unique string for your input.
     - input_manufacturer, input_name, input_name_short, input_library.
     - measurements_dict: Define which measurements (and units) your input provides.
     - options_enabled/options_disabled: Which built-in UI options to expose.
     - custom_options (optional): Extra user-configurable options in the UI.

4) Implement your InputModule
   - class InputModule(AbstractInput):
     - initialize(self): import any dependencies and set up hardware/clients.
     - get_measurement(self): acquire data and set values using self.value_set(channel, value).
   - Only import external libraries inside initialize() to avoid import errors during discovery.

5) Channels and measurements
   - The channels correspond to the keys of measurements_dict (0, 1, 2, ...).
   - Use self.is_enabled(channel) to avoid computing/saving disabled measurements.
   - If you compute a dependent measurement (e.g., dewpoint from temp+humidity), ensure the needed channels are enabled and set.

6) Save timestamps correctly
   - self.value_set() will set timestamp_utc automatically unless you pass a timestamp.
   - If your input produces multiple measurements at the same instant, consider setting
     INPUT_INFORMATION['measurements_use_same_timestamp'] = True.

7) UI dependencies and options
   - If your Input requires extra Python packages, list them in INPUT_INFORMATION['dependencies_module'].
   - If you have per-channel options, use custom_channel_options and setup_custom_channel_options_json().

8) Test
   - Activate your new Input in the Mycodo web UI.
   - Watch logs for errors (enable Debug on the Input for more detail).

Notes
- See mycodo/inputs/examples for more complete examples:
  - minimal_humidity_temperature.py
  - example_all_options_temperature.py
- Keep the template import-side-effect free. Do not import hardware libs at the top of the file.
