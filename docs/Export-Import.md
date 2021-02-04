Page\: `More -> Export Import`

Measurements that fall within the selected date/time frame may be exported as CSV with their corresponding timestamps.

Additionally, the entire measurement database (influxdb) may be exported as a ZIP archive backup. This ZIP may be imported back in any Mycodo system to restore these measurements.

!!! note
    Measurements are associated with specific IDs that correspond to the Inputs/Outputs/etc. of your specific system. If you import measurements without also importing the associated Inputs/Outputs/etc., you will not see these measurements (e.g. on Dashboard Graphs). Therefore, it is recommended to export both Measurements and Settings at the same time so when you import them at a later time, you will have the devices associated with the measurements available on the system you're importing to. 

!!! note
    Importing measurement data will not destroy old data and will be added to the current measurement data.

Mycodo settings may be exported as a ZIP file containing the Mycodo settings database (sqlite) and any custom Inputs, Outputs, Functions, and Widgets. This ZIP file may be used to restore these to another Mycodo install, as long as the Mycodo and database versions being imported are equal or less than the system you are installing them to. Additionally, you can only import to a system with the same major version number (the first number in the version format x.x.x). For instance, you can export settings from Mycodo 8.5.0 and import them into Mycodo 8.8.0, however you can not import them into Mycodo 8.2.0 (earlier version with same major version number), 7.0.0 (not the same major version number), or 9.0.0 (not the same major version number).

!!! warning
    An import will override the current settings and custom controller data (i.e. destroying it). It is advised to make a Mycodo backup prior to attempting an import.
