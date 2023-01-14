## Valores en Vivo

Page\: `Data -> Live Measurements`

La página `Mediciones en vivo` es la primera página que ve un usuario después de iniciar sesión en Mycodo. En ella se muestran las mediciones actuales que se están adquiriendo de los controladores de Entrada y Función. Si no se muestra nada en la página `Live`, asegúrese de que un controlador de Entrada o Función está configurado correctamente y activado. Los datos se actualizarán automáticamente en la página desde la base de datos de mediciones.

## Asíncrono

Página\: `Datos -> Asíncrono`

Una visualización gráfica de datos que resulta útil para ver conjuntos de datos que abarcan periodos de tiempo relativamente largos (semanas/meses/años), cuya visualización en forma de gráfico sincrónico podría requerir muchos datos y un gran número de procesadores. Seleccione un periodo de tiempo y se cargarán los datos de ese periodo, si existen. La primera vista será de todo el conjunto de datos seleccionado. Para cada vista/zoom, se cargarán 700 puntos de datos. Si hay más de 700 puntos de datos registrados para el lapso de tiempo seleccionado, se crearán 700 puntos a partir de un promedio de los puntos de ese lapso de tiempo. Esto permite utilizar muchos menos datos para navegar por un conjunto de datos grande. Por ejemplo, 4 meses de datos pueden ser 10 megabytes si se descargan todos. Sin embargo, al visualizar un lapso de 4 meses, no es posible ver todos los puntos de datos de esos 10 megabytes, y la agregación de puntos es inevitable. Con la carga asíncrona de datos, sólo se descarga lo que se ve. Así, en lugar de descargar 10 megabytes cada vez que se carga el gráfico, sólo se descargarán ~50kb hasta que se seleccione un nuevo nivel de zoom, momento en el que sólo se descargarán otros ~50kb.

!!! note
    Los gráficos requieren mediciones, por lo que es necesario añadir y activar al menos una Entrada/Salida/Función/etc. para poder mostrar los datos.

## Tablero

Página\: `Datos -> Tablero`

El cuadro de mandos puede utilizarse tanto para ver los datos como para manipular el sistema, gracias a los numerosos widgets del cuadro de mandos disponibles. Se pueden crear múltiples cuadros de mando, así como bloquearlos para evitar que se modifique su disposición.

## Widgets

Los widgets son elementos del cuadro de mandos que tienen una serie de usos, como la visualización de datos (gráficos, indicadores, medidores, etc.) o la interacción con el sistema (manipular salidas, cambiar el ciclo de trabajo PWM, consultar o modificar una base de datos, etc.). Los widgets se pueden reorganizar y cambiar de tamaño fácilmente arrastrando y soltando. Para obtener una lista completa de los widgets admitidos, consulte [Widgets admitidos](Supported-Widgets.md).

### Widgets personalizados

Existe un sistema de importación de Widgets personalizados en Mycodo que permite utilizar Widgets creados por el usuario en el sistema Mycodo. Los widgets personalizados pueden cargarse en la página `[Icono del engranaje] -> Configurar -> Widgets personalizados`. Una vez importados, estarán disponibles para su uso en la página `Configuración -> Widget`.

Si desarrollas un módulo que funcione, considera la posibilidad de [crear una nueva incidencia en GitHub](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) o una solicitud de extracción, y puede que se incluya en el conjunto incorporado.

Abra cualquiera de los módulos de widgets incorporados ubicados en el directorio [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) para ver ejemplos del formato adecuado. También hay ejemplos de Widgets personalizados en el directorio [Mycodo/mycodo/widgets/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples).

La creación de un módulo de widgets personalizados suele requerir una colocación y ejecución específica de Javascript. Se crearon varias variables en cada módulo para abordar esto, y siguen la siguiente estructura breve de la página del tablero de instrumentos que se generaría con múltiples widgets que se muestran.

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
