Daemon Control Object
=====================

class mycodo_client.DaemonControl(uri='PYRO:mycodo.pyro_server@127.0.0.1:9090', pyro_timeout=None)
--------------------------------------------------------------------------------------------------

The mycodo client object implements a way to communicate with a mycodo daemon and query information from the influxdb database.

Parameters
^^^^^^^^^^

 - **uri** - the pyro5 uri to use to connect to the daemon
 - **pyro_timeout** - the pyro5 timeout period

controller_activate(controller_type, controller_id)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters
^^^^^^^^^^

-  **controller_type** - the type of controller being activated. Options are: Conditional, LCD, Input, Math, Output, PID, Trigger, Custom
-  **controller_id** - the unique ID of the controller to activate

controller_deactivate(controller_type, controller_id)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters
^^^^^^^^^^

-  **controller_type** - the type of controller being deactivated. Options are: Conditional, LCD, Input, Math, Output, PID, Trigger, Custom
-  **controller_id** - the unique ID of the controller to deactivate
