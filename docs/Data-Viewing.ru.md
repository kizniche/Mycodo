## Живые измерения

Page\: `Data -> Live Measurements`

Страница `Live Measurements` - это первая страница, которую видит пользователь после входа в Mycodo. На ней отображаются текущие измерения, получаемые от входных и функциональных контроллеров. Если на странице `Live` ничего не отображается, убедитесь, что входной или функциональный контроллер настроен правильно и активирован. Данные будут автоматически обновляться на этой странице из базы данных измерений.

## асинхронный

Page\: `Данные -> асинхронный`

Графическое отображение данных, полезное для просмотра наборов данных, охватывающих относительно длительные периоды времени (недели/месяцы/годы), просмотр которых в виде синхронного графика может потребовать больших затрат данных и процессора. Выберите временной интервал, и данные будут загружены из этого временного интервала, если он существует. Первый просмотр будет всего выбранного набора данных. Для каждого вида/масштаба будет загружено 700 точек данных. Если для выбранного временного интервала записано более 700 точек данных, 700 точек будут созданы на основе усреднения точек этого временного интервала. Это позволяет использовать гораздо меньше данных для навигации по большому набору данных. Например, данные за 4 месяца могут занимать 10 мегабайт, если загрузить их все. Однако при просмотре данных за 4 месяца невозможно увидеть каждую точку данных из этих 10 мегабайт, и объединение точек неизбежно. При асинхронной загрузке данных вы загружаете только то, что видите. Таким образом, вместо загрузки 10 мегабайт при каждой загрузке графика, будет загружаться только ~50 кб, пока не будет выбран новый уровень масштабирования, и тогда будет загружено еще ~50 кб.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## Панель управления

Page\: `Данные -> Панель управления`

Приборная панель может использоваться как для просмотра данных, так и для манипулирования системой благодаря многочисленным виджетам приборной панели. Можно создать несколько приборных панелей, а также заблокировать их для предотвращения изменения расположения.

## Widgets

Виджеты - это элементы приборной панели, которые могут использоваться для просмотра данных (графики, индикаторы, датчики и т.д.) или взаимодействия с системой (манипулирование выходами, изменение рабочего цикла ШИМ, запрос или изменение базы данных и т.д.). Виджеты можно легко переставлять и изменять их размер путем перетаскивания. Полный список поддерживаемых виджетов см. в [Supported Widgets](Supported-Widgets.md).

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
