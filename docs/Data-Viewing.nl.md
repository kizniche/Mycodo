## Live metingen

Page\: `Data -> Live Measurements`

De `Live Measurements` pagina is de eerste pagina die een gebruiker ziet na het inloggen op Mycodo. Het toont de huidige metingen die worden verkregen van ingangs- en functiecontrollers. Als er niets wordt weergegeven op de `Live`-pagina, zorg er dan voor dat een ingangs- of functiecontroller correct is geconfigureerd en geactiveerd. Gegevens worden automatisch bijgewerkt op de pagina vanuit de meetdatabase.

## Asynchroon

Pagina\: `Gegevens -> Asynchroon`

Een grafische weergave van gegevens die nuttig is voor het bekijken van gegevensreeksen over relatief lange perioden (weken/maanden/jaren), die zeer gegevens- en processorintensief zouden kunnen zijn om te bekijken als een synchrone grafiek. Selecteer een tijdspanne en de gegevens worden geladen van die tijdspanne, als die bestaat. De eerste weergave betreft de gehele geselecteerde gegevensreeks. Voor elke weergave/zoom worden 700 datapunten geladen. Als er meer dan 700 datapunten zijn opgenomen voor de geselecteerde tijdspanne, worden 700 punten gecreëerd uit een gemiddelde van de punten in die tijdspanne. Hierdoor kunnen veel minder gegevens worden gebruikt om door een grote dataset te navigeren. Bijvoorbeeld, 4 maanden gegevens kunnen 10 megabytes zijn als ze allemaal werden gedownload. Bij het bekijken van een periode van 4 maanden is het echter niet mogelijk elk gegevenspunt van die 10 megabyte te zien, en is het samenvoegen van punten onvermijdelijk. Met asynchroon laden van gegevens downloadt u alleen wat u ziet. Dus in plaats van 10 megabyte te downloaden bij elke grafieklading, wordt slechts ~50kb gedownload tot een nieuw zoomniveau wordt geselecteerd, waarna nog eens ~50kb wordt gedownload.

!!! note
    Grafieken vereisen metingen, daarom moet ten minste één ingang/uitgang/functie/etc. worden toegevoegd en geactiveerd om gegevens weer te geven.

## Dashboard

Pagina\: `Gegevens -> Dashboard`

Het dashboard kan zowel worden gebruikt om gegevens te bekijken als om het systeem te manipuleren, dankzij de talrijke beschikbare dashboardwidgets. Er kunnen meerdere dashboards worden aangemaakt en vergrendeld om de indeling niet te wijzigen.

## Widgets

Widgets zijn elementen op het Dashboard die een aantal toepassingen hebben, zoals het bekijken van gegevens (grafieken, indicatoren, meters, enz.) of interactie met het systeem (uitgangen manipuleren, PWM duty cycle wijzigen, een database opvragen of wijzigen, enz.) Widgets kunnen gemakkelijk worden herschikt en van grootte veranderd door ze te verslepen. Voor een volledige lijst van ondersteunde Widgets, zie [Ondersteunde Widgets](Supported-Widgets.md).

### Aangepaste Widgets

Er is een systeem voor het importeren van aangepaste Widgets in Mycodo waarmee door gebruikers gemaakte Widgets in het Mycodo-systeem kunnen worden gebruikt. Aangepaste Widgets kunnen worden geüpload op de pagina `[Versnellingspictogram] -> Configuratie -> Aangepaste Widgets`. Na het importeren zijn ze beschikbaar voor gebruik op de pagina `Instellen -> Widget`.

Als je een werkende module ontwikkelt, overweeg dan [een nieuw GitHub issue aanmaken](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) of een pull request, en het kan worden opgenomen in de ingebouwde set.

Open een van de ingebouwde Widget-modules in de directory [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) voor voorbeelden van de juiste opmaak. Er zijn ook voorbeelden van aangepaste Widgets in de map [Mycodo/mycodo/widgets/voorbeelden](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples).

Het maken van een aangepaste widgetmodule vereist vaak specifieke plaatsing en uitvoering van Javascript. In elke module werden verschillende variabelen gemaakt om dit aan te pakken, en de volgende korte structuur te volgen van de dashboardpagina die zou worden gegenereerd met meerdere widgets die worden weergegeven.

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
