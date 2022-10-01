## Pomiary żywo

Page\: `Data -> Live Measurements`

Strona `Pomiary na żywo` jest pierwszą stroną, którą widzi użytkownik po zalogowaniu się do Mycodo. Wyświetla ona aktualne pomiary uzyskane z kontrolerów wejścia i funkcji. Jeśli nic nie jest wyświetlane na stronie `Live`, upewnij się, że kontroler wejścia lub funkcji jest poprawnie skonfigurowany i aktywowany. Dane będą automatycznie aktualizowane na stronie z bazy danych pomiarów.

## Wykresy asynchroniczne

Page\: `Dane -> Wykresy asynchroniczne`

Graficzne wyświetlanie danych przydatne do przeglądania zestawów danych obejmujących stosunkowo długie okresy czasu (tygodnie/miesiące/roki), których wyświetlanie w postaci wykresu synchronicznego mogłoby wymagać dużej ilości danych i procesora. Po wybraniu przedziału czasowego zostaną wczytane dane z tego przedziału, jeśli istnieje. Pierwszy widok będzie dotyczył całego wybranego zestawu danych. Dla każdego widoku/powiększenia zostanie załadowanych 700 punktów danych. Jeśli dla wybranego przedziału czasowego zarejestrowano więcej niż 700 punktów danych, 700 punktów zostanie utworzonych z uśrednienia punktów w tym przedziale czasowym. Umożliwia to wykorzystanie znacznie mniejszej ilości danych do nawigacji po dużym zbiorze danych. Na przykład, 4 miesiące danych mogą mieć rozmiar 10 megabajtów, jeśli wszystkie zostaną pobrane. Jednak podczas przeglądania 4-miesięcznego okresu nie jest możliwe zobaczenie każdego punktu danych z tych 10 megabajtów, a agregacja punktów jest nieunikniona. Przy asynchronicznym ładowaniu danych, pobierasz tylko to, co widzisz. Tak więc, zamiast pobierać 10 megabajtów przy każdym ładowaniu wykresu, tylko ~50kb zostanie pobrane do momentu wybrania nowego poziomu powiększenia, w którym to momencie pobierane jest tylko kolejne ~50kb.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## Pulpit

Page\: `Dane -> Pulpit`

Dashboard może służyć zarówno do przeglądania danych, jak i do manipulowania systemem, dzięki licznym dostępnym widżetom dashboardowym. Można tworzyć wiele dashboardów, jak również zablokować je, aby uniemożliwić zmianę układu.

## widgety

Widżety to elementy na pulpicie nawigacyjnym, które mają wiele zastosowań, takich jak wyświetlanie danych (wykresy, wskaźniki, mierniki itp.) lub interakcja z systemem (manipulowanie wyjściami, zmiana cyklu pracy PWM, odpytywanie lub modyfikowanie bazy danych itp.) Widżety można łatwo zmieniać układ i rozmiar poprzez przeciąganie i upuszczanie. Pełna lista obsługiwanych Widżetów znajduje się w [Obsługiwane Widżety](Supported-Widgets.md).

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
