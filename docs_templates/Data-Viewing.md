## %%%Live Measurements%%%

Page\: `Data -> Live Measurements`

%%%text_1_1%%%

## %%%Asynchronous Graphs%%%

%%%Page%%%\: `%%%Data%%% -> %%%Asynchronous Graphs%%%`

%%%text_2_1%%%

!!! note
    %%%text_2_2%%%

## %%%Dashboard%%%

%%%Page%%%\: `%%%Data%%% -> %%%Dashboard%%%`

%%%text_3_1%%%

## %%%Widgets%%%

%%%text_4_1%%%

### %%%Custom Widgets%%%

%%%text_5_1%%%

%%%text_5_2%%%

%%%text_5_3%%%

%%%text_5_4%%%

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
