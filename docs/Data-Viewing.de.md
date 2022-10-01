## Live Messungen

Page\: `Data -> Live Measurements`

Die Seite "Live-Messungen" ist die erste Seite, die ein Benutzer nach dem Einloggen in Mycodo sieht. Sie zeigt die aktuellen Messungen an, die von Eingangs- und Funktionscontrollern erfasst werden. Wenn auf der Seite "Live" nichts angezeigt wird, vergewissern Sie sich, dass ein Eingangs- oder Funktionsregler korrekt konfiguriert und aktiviert ist. Die Daten werden auf der Seite automatisch aus der Messdatenbank aktualisiert.

## Asynchrone Diagramme

Page\: `Daten -> Asynchrone Diagramme`

Eine grafische Datenanzeige, die für die Anzeige von Datensätzen über relativ lange Zeiträume (Wochen/Monate/Jahre) nützlich ist, deren Anzeige als Synchrondiagramm sehr daten- und prozessorintensiv sein könnte. Wählen Sie einen Zeitraum aus, und die Daten werden aus dieser Zeitspanne geladen, sofern sie vorhanden sind. In der ersten Ansicht wird der gesamte ausgewählte Datensatz angezeigt. Für jede Ansicht/Zoom werden 700 Datenpunkte geladen. Wenn mehr als 700 Datenpunkte für die ausgewählte Zeitspanne aufgezeichnet wurden, werden 700 Punkte aus einer Mittelung der Punkte in dieser Zeitspanne erstellt. Auf diese Weise können viel weniger Daten verwendet werden, um durch einen großen Datensatz zu navigieren. So können beispielsweise 4 Monate an Daten 10 Megabyte umfassen, wenn sie vollständig heruntergeladen werden. Bei der Betrachtung einer 4-monatigen Zeitspanne ist es jedoch nicht möglich, jeden Datenpunkt dieser 10 Megabyte zu sehen, und eine Aggregation der Punkte ist unvermeidlich. Beim asynchronen Laden von Daten laden Sie nur das herunter, was Sie sehen. Anstatt also bei jedem Laden des Diagramms 10 Megabyte herunterzuladen, werden nur ~50kb heruntergeladen, bis eine neue Vergrößerungsstufe ausgewählt wird, woraufhin nur weitere ~50kb heruntergeladen werden.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## Dashboard

Page\: `Daten -> Dashboard`

Dank der zahlreichen Dashboard-Widgets kann das Dashboard sowohl zur Anzeige von Daten als auch zur Manipulation des Systems verwendet werden. Es können mehrere Dashboards erstellt und gesperrt werden, um eine Änderung der Anordnung zu verhindern.

## Widgets

Widgets sind Elemente auf dem Dashboard, die für verschiedene Zwecke verwendet werden können, z. B. zur Anzeige von Daten (Diagramme, Indikatoren, Messgeräte usw.) oder zur Interaktion mit dem System (Manipulation von Ausgängen, Änderung des PWM-Tastverhältnisses, Abfrage oder Änderung einer Datenbank usw.). Widgets lassen sich durch Ziehen und Ablegen leicht neu anordnen und in der Größe verändern. Eine vollständige Liste der unterstützten Widgets finden Sie unter [Unterstützte Widgets](Supported-Widgets.md).

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
