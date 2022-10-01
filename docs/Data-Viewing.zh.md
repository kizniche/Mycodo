## 实时测量

Page\: `Data -> Live Measurements`

实时测量 "页面是用户登录Mycodo后看到的第一个页面。它将显示当前从输入和功能控制器获得的测量结果。如果 "实时 "页面上没有显示，请确保输入或功能控制器配置正确并被激活。数据将从测量数据库中自动更新到该页面上。

## 异步

Page\: `数据 -> 异步`

一种图形化的数据显示，对于查看跨度相对较长的时间段（周/月/年）的数据集很有用，如果以同步图的形式查看，可能会非常耗费数据和处理器。选择一个时间框架，如果存在的话，数据将从该时间段加载。第一个视图将是整个选定的数据集。对于每个视图/缩放，700个数据点将被加载。如果所选的时间跨度有超过700个数据点，700个点将从该时间跨度的点的平均数中产生。这样就可以用少得多的数据来浏览一个大的数据集。例如，如果全部下载，4个月的数据可能是10兆字节。然而，当查看4个月的时间跨度时，不可能看到这10兆字节的每一个数据点，点的聚集是不可避免的。通过数据的异步加载，你只下载你所看到的东西。因此，每次加载图表都要下载10兆字节的数据，而在选择新的缩放级别之前，只下载约50kb的数据，这时又只下载约50kb的数据。

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## 仪表板

Page\: `数据 -> 仪表板`

由于有许多仪表盘部件可用，仪表盘既可用于查看数据，也可用于操纵系统。可以创建多个仪表盘，也可以锁定以防止改变安排。

## Widgets

部件是仪表板上的元素，有多种用途，如查看数据（图表、指标、仪表等）或与系统互动（操纵输出、改变PWM占空比、查询或修改数据库等）。小工具可以通过拖放轻松地重新安排和调整大小。关于支持的Widgets的完整列表，见[支持的[Widgets](Supported-Widgets.md)。

### Custom Widgets

There is a Custom Widget import system in Mycodo that allows user-created Widgets to be used in the Mycodo system. Custom Widgets can be uploaded on the `[Gear Icon] -> Configure -> Custom Widgets` page. After import, they will be available to use on the `Setup -> Widget` page.

If you develop a working module, please consider [creating a new GitHub issue](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) or pull request, and it may be included in the built-in set.

Open any of the built-in Widget modules located in the directory [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) for examples of the proper formatting. There are also example Custom Widgets in the directory [Mycodo/mycodo/widgets/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples).

Creating a custom widget module often requires specific placement and execution of Javascript. Several variables were created in each module to address this, and follow the following brief structure of the dashboard page that would be generated with multiple widgets being displayed.

```angular2html
<html>
<head>
  <title>Title</title>
  <script>
    {{ widget_1_dashboard_head }}
    {{ widget_2_dashboard_head }}
  </script>
</head>
<body>

<div id="widget_1">
  <div id="widget_1_titlebar">{{ widget_dashboard_title_bar }}</div>
  {{ widget_1_dashboard_body }}
  <script>
    $(document).ready(function() {
      {{ widget_1_dashboard_js_ready_end }}
    });
  </script>
</div>

<div id="widget_2">
  <div id="widget_2_titlebar">{{ widget_dashboard_title_bar }}</div>
  {{ widget_2_dashboard_body }}
  <script>
    $(document).ready(function() {
      {{ widget_2_dashboard_js_ready_end }}
    });
  </script>
</div>

<script>
  {{ widget_1_dashboard_js }}
  {{ widget_2_dashboard_js }}

  $(document).ready(function() {
    {{ widget_1_dashboard_js_ready }}
    {{ widget_2_dashboard_js_ready }}
  });
</script>

</body>
</html>
```
