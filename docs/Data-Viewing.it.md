## Misure dal vivo

Page\: `Data -> Live Measurements`

La pagina `Misure in tempo reale` è la prima pagina che l'utente vede dopo aver effettuato l'accesso a Mycodo. Mostra le misure correnti acquisite dai controllori di ingresso e di funzione. Se non viene visualizzato nulla nella pagina `Live`, accertarsi che un controllore di ingresso o di funzione sia configurato correttamente e attivato. I dati saranno aggiornati automaticamente sulla pagina dal database delle misure.

## Grafici asincroni

Page\: `Dati -> Grafici asincroni`

Una visualizzazione grafica dei dati utile per visualizzare insiemi di dati che coprono periodi di tempo relativamente lunghi (settimane/mesi/anni), che potrebbero essere molto impegnativi in termini di dati e di processore se visualizzati come grafico sincrono. Selezionando un intervallo di tempo, i dati verranno caricati da quell'intervallo, se esistente. La prima visualizzazione sarà quella dell'intero set di dati selezionato. Per ogni vista/zoom, verranno caricati 700 punti di dati. Se sono stati registrati più di 700 punti di dati per l'intervallo di tempo selezionato, verranno creati 700 punti da una media dei punti di quell'intervallo di tempo. In questo modo è possibile utilizzare una quantità di dati molto inferiore per navigare in un set di dati di grandi dimensioni. Ad esempio, 4 mesi di dati potrebbero essere 10 megabyte se venissero scaricati tutti. Tuttavia, quando si visualizza un arco di tempo di 4 mesi, non è possibile vedere tutti i punti dati di quei 10 megabyte e l'aggregazione dei punti è inevitabile. Con il caricamento asincrono dei dati, si scarica solo ciò che si vede. Quindi, invece di scaricare 10 megabyte a ogni caricamento del grafico, verranno scaricati solo ~50kb fino a quando non viene selezionato un nuovo livello di zoom, a quel punto verranno scaricati solo altri ~50kb.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## Cruscotto

Page\: `Dati -> Cruscotto`

Il cruscotto può essere utilizzato sia per visualizzare i dati che per manipolare il sistema, grazie ai numerosi widget disponibili. È possibile creare più cruscotti e bloccarli per evitare di modificarne la disposizione.

## Widget

I widget sono elementi della Dashboard che possono essere utilizzati in vari modi, ad esempio per visualizzare i dati (grafici, indicatori, indicatori, ecc.) o per interagire con il sistema (manipolare le uscite, modificare il ciclo di lavoro PWM, interrogare o modificare un database, ecc.) I widget possono essere facilmente riorganizzati e ridimensionati trascinandoli. Per un elenco completo dei widget supportati, vedere [Widget supportati] (Supported-Widgets.md).

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
