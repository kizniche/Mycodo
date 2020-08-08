Page\: `Data -> Dashboard`

For a full list of supported Widgets, see [Supported Widgets](Supported-Widgets.md).

Widgets are how data is presented to the user and how the user can control aspects of the system from the dashboard. These include graphs, gauges, indicators, and more.

## Custom Widgets

There is a Custom Widget import system in Mycodo that allows user-created Widgets to be created an used in the Mycodo system. Custom Widgets can be uploaded and imported from the `[Gear Icon] -> Configure -> Custom Widgets` page. After import, they will be available to use on the `Data -> Dashboard` pages.

If you desire an Widget that is not currently supported by Mycodo, you can build your own Widget module and import it into Mycodo. All information about an Widget is contained within the Widget module. Open any of the built-in modules located in the [widgets directory](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) for examples of the proper formatting. There's also a [minimal widget module template as an example](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples/custom_widget_example_simple.py).
