# Mycodo 3.5-beta (experimental)

This is an experimental branch of mycodo. Unless I have been in direct contact with you regarding testing of this branch, I will not be providing technical support for any issues with this version. Instead, I recommend you check out the v3.0 stable branch.

### Goals

- [X] K30 CO2 sensor support (complete)
- [X] SQLite database support (debugging)
- [ ] Email notification or audible alarm during critical failure or condition (working on)
- [ ] O2 sensor support
- [ ] More graph generation options
- [ ] Set electrical current draw of each device and prevent exceeding total current limit with different combinations of devices on
- [ ] Capture series of photos at different ISOs, combine to make HDR photo
- [ ] Timelapse video creation ability (define start, end, duration between, etc.)

### New Dependencies

`sudo apt-get install php5-sqlite sqlite3`