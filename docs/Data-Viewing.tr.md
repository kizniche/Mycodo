## Live Measurements

Page\: `Data -> Live Measurements`

Canlı Ölçümler sayfası, bir kullanıcının Mycodo'ya giriş yaptıktan sonra gördüğü ilk sayfadır. Giriş ve Fonksiyon kontrolörlerinden alınan mevcut ölçümleri görüntüler. Canlı` sayfasında hiçbir şey görüntülenmiyorsa, bir Giriş veya Fonksiyon kontrolörünün hem doğru yapılandırıldığından hem de etkinleştirildiğinden emin olun. Veriler ölçüm veritabanından otomatik olarak sayfada güncellenecektir.

## Asynchronous Graphs

Page\: `Veri -> Asynchronous Graphs`

Senkron Grafik olarak görüntülemek için çok veri ve işlemci yoğun olabilecek nispeten uzun zaman dilimlerini (haftalar/aylar/yıllar) kapsayan veri kümelerini görüntülemek için yararlı olan bir grafik veri ekranı. Bir zaman dilimi seçtiğinizde, eğer varsa, o zaman aralığındaki veriler yüklenecektir. İlk görünüm seçilen veri setinin tamamına ait olacaktır. Her görünüm/yakınlaştırma için 700 veri noktası yüklenecektir. Seçilen zaman aralığı için 700'den fazla veri noktası kaydedilmişse, 700 nokta o zaman aralığındaki noktaların ortalamasından oluşturulacaktır. Bu, büyük bir veri setinde gezinmek için çok daha az verinin kullanılmasını sağlar. Örneğin, 4 aylık verinin tamamı indirilirse 10 megabayt olabilir. Ancak, 4 aylık bir süreyi görüntülerken, bu 10 megabaytın her veri noktasını görmek mümkün değildir ve noktaların toplanması kaçınılmazdır. Eşzamansız veri yüklemesi ile yalnızca gördüğünüz kadarını indirirsiniz. Böylece, her grafik yüklemesinde 10 megabayt indirmek yerine, yeni bir yakınlaştırma seviyesi seçilene kadar yalnızca ~50kb indirilir ve bu sırada yalnızca ~50kb daha indirilir.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## Gösterge Tablosu

Page\: `Veri -> Gösterge Tablosu`

Gösterge paneli, mevcut çok sayıda gösterge paneli widget'ı sayesinde hem verileri görüntülemek hem de sistemi manipüle etmek için kullanılabilir. Birden fazla gösterge tablosu oluşturulabilir ve düzenlemenin değiştirilmesini önlemek için kilitlenebilir.

## Widgets

Pencere öğeleri, Gösterge Tablosunda veri görüntüleme (grafikler, göstergeler, göstergeler, vb.) veya sistemle etkileşim (çıkışları manipüle etme, PWM görev döngüsünü değiştirme, bir veritabanını sorgulama veya değiştirme, vb.) Pencere öğeleri sürüklenip bırakılarak kolayca yeniden düzenlenebilir ve yeniden boyutlandırılabilir. Desteklenen Pencere Araçlarının tam listesi için [Desteklenen Pencere Araçları](Supported-Widgets.md) bölümüne bakın.

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
