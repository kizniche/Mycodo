## Mesures en direct

Page\: `Data -> Live Measurements`

La page `Live Measurements` est la première page qu'un utilisateur voit après s'être connecté à Mycodo. Elle affiche les mesures actuelles acquises par les contrôleurs d'entrée et de fonction. Si rien n'est affiché sur la page `Live`, assurez-vous qu'un contrôleur d'entrée ou de fonction est correctement configuré et activé. Les données seront automatiquement mises à jour sur la page à partir de la base de données des mesures.

## Graphique Asynchrone

Page\: `Les données -> Graphique Asynchrone`

Un affichage graphique des données qui est utile pour visualiser des ensembles de données couvrant des périodes relativement longues (semaines/mois/années), qui pourraient être très gourmands en données et en processeur pour être affichés sous forme de graphique synchrone. Sélectionnez une période de temps et les données seront chargées à partir de cette période, si elle existe. La première vue sera celle de l'ensemble des données sélectionnées. Pour chaque vue/zoom, 700 points de données seront chargés. S'il y a plus de 700 points de données enregistrés pour l'intervalle de temps sélectionné, 700 points seront créés à partir d'une moyenne des points de cet intervalle de temps. Cela permet d'utiliser beaucoup moins de données pour naviguer dans un grand ensemble de données. Par exemple, 4 mois de données peuvent représenter 10 mégaoctets si elles sont toutes téléchargées. Cependant, lorsqu'on visualise une période de 4 mois, il n'est pas possible de voir chaque point de données de ces 10 mégaoctets, et l'agrégation des points est inévitable. Avec le chargement asynchrone des données, vous ne téléchargez que ce que vous voyez. Ainsi, au lieu de télécharger 10 mégaoctets à chaque chargement de graphique, seuls ~50kb seront téléchargés jusqu'à ce qu'un nouveau niveau de zoom soit sélectionné, auquel moment seulement ~50kb supplémentaires seront téléchargés.

!!! note
    Les graphiques nécessitent des mesures, donc au moins une entrée/sortie/fonction/etc. doit être ajoutée et activée afin d'afficher les données.

## Tableau de bord

Page\: `Les données -> Tableau de bord`

Le tableau de bord peut être utilisé à la fois pour visualiser les données et pour manipuler le système, grâce aux nombreux widgets de tableau de bord disponibles. Il est possible de créer plusieurs tableaux de bord et de les verrouiller pour empêcher toute modification de leur agencement.

## Widgets

Les widgets sont des éléments du tableau de bord qui ont un certain nombre d'utilisations, telles que l'affichage de données (graphiques, indicateurs, jauges, etc.) ou l'interaction avec le système (manipulation des sorties, modification du cycle de fonctionnement du PWM, interrogation ou modification d'une base de données, etc.) Les widgets peuvent être facilement réorganisés et redimensionnés par glisser-déposer. Pour une liste complète des widgets pris en charge, voir [Widgets pris en charge](Supported-Widgets.md).

### Widgets personnalisés

Il existe un système d'importation de Widgets personnalisés dans Mycodo qui permet aux Widgets créés par les utilisateurs d'être utilisés dans le système Mycodo. Les widgets personnalisés peuvent être téléchargés sur la page `[Icône Gear] -> Configurer -> Widgets personnalisés`. Après importation, ils seront disponibles pour être utilisés sur la page `Setup -> Widget`.

Si vous développez un module fonctionnel, veuillez envisager de [créer un nouveau problème GitHub](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) ou une demande de retrait, et il pourra être inclus dans l'ensemble intégré.

Ouvrez l'un des modules Widget intégrés situés dans le répertoire [Mycodo/mycodo/widgets](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/) pour voir des exemples de formatage approprié. Il existe également des exemples de Widgets personnalisés dans le répertoire [Mycodo/mycodo/widgets/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/widgets/examples).

La création d'un module de widgets personnalisés nécessite souvent un placement et une exécution spécifiques de Javascript. Plusieurs variables ont été créées dans chaque module pour y remédier, et suivent la brève structure suivante de la page du tableau de bord qui serait générée avec l'affichage de plusieurs widgets.

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
