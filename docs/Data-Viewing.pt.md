## Medições ao vivo

Page\: `Data -> Live Measurements`

A página "Medições em directo" é a primeira página que um utilizador vê depois de entrar no Mycodo. Irá mostrar as medidas actuais que estão a ser adquiridas dos controladores de Entrada e Função. Se não houver nada exibido na página `Vivo`, certifique-se de que um controlador de Entrada ou de Função está configurado correctamente e activado. Os dados serão automaticamente actualizados na página a partir da base de dados de medições.

## Assíncrono

Página\: `Dados -> Assíncrono`

Uma visualização gráfica de dados que é útil para visualizar conjuntos de dados que abrangem períodos de tempo relativamente longos (semanas/meses/anos), que podem ser muito exigentes em termos de dados e de processador para serem visualizados como um Gráfico Síncrono. Seleccione um período de tempo e os dados serão carregados a partir desse período de tempo, se este existir. A primeira vista será de todo o conjunto de dados seleccionado. Para cada vista/zoom, 700 pontos de dados serão carregados. Se houver mais de 700 pontos de dados registados para o intervalo de tempo seleccionado, serão criados 700 pontos a partir de uma média dos pontos nesse intervalo de tempo. Isto permite que muito menos dados sejam utilizados para navegar num grande conjunto de dados. Por exemplo, 4 meses de dados podem ser de 10 megabytes se todos os dados forem descarregados. Contudo, ao visualizar um período de 4 meses, não é possível ver todos os pontos de dados desses 10 megabytes, e a agregação de pontos é inevitável. Com o carregamento assíncrono de dados, só é possível descarregar o que se vê. Assim, em vez de descarregar 10 megabytes por cada carga gráfica, apenas ~50kb serão descarregados até ser seleccionado um novo nível de zoom, altura em que apenas outros ~50kb serão descarregados.

!!! note
    Os gráficos requerem medições, pelo que pelo menos uma Entrada/Saída/Função/etc. precisa de ser adicionada e activada para exibir os dados.

## painel de controle

Página\: `Dados -> painel de controle`

O tablier pode ser utilizado tanto para visualizar dados como para manipular o sistema, graças aos numerosos widgets de tablier disponíveis. Podem ser criados vários painéis de instrumentos, bem como bloqueados para impedir a alteração da disposição.

## Widgets

Os Widgets são elementos do Painel que têm várias utilizações, tais como visualizar dados (gráficos, indicadores, medidores, etc.) ou interagir com o sistema (manipular saídas, alterar o ciclo de funcionamento do PWM, consultar ou modificar uma base de dados, etc.). Os widgets podem ser facilmente rearranjados e redimensionados por arrastar e largar. Para uma lista completa de Widgets suportados, ver [Supported Widgets](Supported-Widgets.md).

### Widgets personalizados

Existe um sistema personalizado de importação de Widgets em Mycodo que permite a utilização de Widgets criados pelo utilizador no sistema Mycodo. Os Widgets Personalizados podem ser carregados na página `[Ícone do Equipamento] -> Configurar -> Widgets Personalizados'. Após a importação, estarão disponíveis para utilização na página `Setup -> Widget`.

Se desenvolver um módulo de trabalho, considere [criar uma nova edição do GitHub](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) ou faça um pedido, e este pode ser incluído no conjunto integrado.

Abrir qualquer um dos módulos Widget integrados localizados no directório [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) para exemplos da formatação adequada. Há também exemplos de Widgets personalizados no directório [Mycodo/mycodo/widgets/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples).

A criação de um módulo widget personalizado requer frequentemente a colocação e execução específicas de Javascript. Várias variáveis foram criadas em cada módulo para tratar disto, e seguir a seguinte breve estrutura da página do painel que seria gerada com múltiplos widgets a serem exibidos.

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
