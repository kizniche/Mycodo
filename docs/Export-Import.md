`More -> Export Import`

Measurements that fall within the selected date/time frame may be exported as CSV with their corresponding timestamps.

Additionally, the entire measurement database (influxdb) may be exported as a ZIP archive backup. This ZIP may be imported back in any Mycodo system to restore these measurements.

!!! warning
    An import will override the current data (i.e. destroying it).

Mycodo settings may be exported as a ZIP file containing the Mycodo settings database (sqlite). This ZIP file may be used to restore the settings database to another Mycodo install, as long as the Mycodo version and database versions are the same. Future support for installing older (or newer) databases and performing an automatic upgrade/downgrade is in the works.
