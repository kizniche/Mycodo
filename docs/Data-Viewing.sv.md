## Live mätningar

Page\: `Data -> Live Measurements`

Sidan `Live Measurements` är den första sidan som en användare ser efter att ha loggat in på Mycodo. Den visar de aktuella mätningar som erhålls från styrenheter för ingång och funktion. Om det inte visas något på sidan `Live` ska du se till att en ingångs- eller funktionsregulator är både korrekt konfigurerad och aktiverad. Data kommer automatiskt att uppdateras på sidan från mätningsdatabasen.

## Asynchronous Graphs

Page\: `Data -> Asynchronous Graphs`

En grafisk datavisning som är användbar för att visa datamängder som sträcker sig över relativt långa tidsperioder (veckor/månader/år), vilket kan vara mycket data- och processorkrävande att visa som en synkron graf. Välj en tidsram och data kommer att laddas från den tidsperioden, om den finns. Den första visningen kommer att vara av hela den valda datamängden. För varje vy/zoom kommer 700 datapunkter att laddas. Om det finns fler än 700 datapunkter registrerade för det valda tidsspannet kommer 700 punkter att skapas genom en genomsnittlig beräkning av punkterna i det tidsspannet. På så sätt kan mycket mindre data användas för att navigera i en stor datamängd. Exempelvis kan 4 månaders data vara 10 megabyte om alla data laddas ner. När man tittar på en 4-månadersperiod är det dock inte möjligt att se varje datapunkt i de 10 megabyte, och aggregering av punkter är oundviklig. Med asynkron laddning av data hämtar du bara det du ser. Så i stället för att ladda ner 10 megabyte varje gång grafen laddas, laddas endast ~50 kb ner tills en ny zoomnivå väljs, varvid endast ytterligare ~50 kb laddas ner.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## instrumentbräda

Page\: `Data -> instrumentbräda`

Instrumentpanelen kan användas både för att visa data och för att manipulera systemet, tack vare de många widgetar som finns tillgängliga. Flera instrumentpaneler kan skapas och låsas för att förhindra att arrangemanget ändras.

## Widgets

Widgets är element på instrumentpanelen som kan användas på olika sätt, t.ex. för att visa data (diagram, indikatorer, mätare osv.) eller för att interagera med systemet (manipulera utgångar, ändra PWM-tjänstgöringscykel, fråga eller ändra en databas osv.). Widgetar kan enkelt omorganiseras och ändras i storlek genom att dra och släppa dem. För en fullständig lista över widgets som stöds, se [Supported Widgets] (Supported-Widgets.md).

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
