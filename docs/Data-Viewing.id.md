## Live Measurements

Page\: `Data -> Live Measurements`

Halaman `Pengukuran Langsung` adalah halaman pertama yang dilihat pengguna setelah masuk ke Mycodo. Ini akan menampilkan pengukuran saat ini yang diperoleh dari pengontrol Input dan Fungsi. Jika tidak ada yang ditampilkan pada halaman `Live`, pastikan pengontrol Input atau Fungsi dikonfigurasi dengan benar dan diaktifkan. Data akan secara otomatis diperbarui pada halaman dari database pengukuran.

## Asynchronous Graphs

Page\: `data -> Asynchronous Graphs`

Tampilan data grafis yang berguna untuk melihat kumpulan data yang mencakup periode waktu yang relatif lama (minggu/bulan/tahun), yang bisa jadi sangat intensif data dan prosesor untuk dilihat sebagai Grafik Sinkron. Pilih kerangka waktu dan data akan dimuat dari rentang waktu tersebut, jika ada. Tampilan pertama adalah seluruh kumpulan data yang dipilih. Untuk setiap tampilan/zoom, 700 titik data akan dimuat. Jika terdapat lebih dari 700 titik data yang direkam untuk rentang waktu yang dipilih, 700 titik akan dibuat dari rata-rata titik dalam rentang waktu tersebut. Hal ini memungkinkan data yang jauh lebih sedikit digunakan untuk menavigasi kumpulan data yang besar. Misalnya, data 4 bulan mungkin 10 megabyte jika semuanya diunduh. Namun, ketika melihat rentang waktu 4 bulan, tidak mungkin untuk melihat setiap titik data dari 10 megabyte itu, dan pengumpulan titik-titik tidak dapat dihindari. Dengan pemuatan data secara asinkron, Anda hanya mengunduh apa yang Anda lihat. Jadi, alih-alih mengunduh 10 megabyte setiap pemuatan grafik, hanya ~50kb yang akan diunduh hingga tingkat zoom baru dipilih, dan pada saat itu hanya ~50kb lagi yang diunduh.

!!! note
    Graphs require measurements, therefore at least one Input/Output/Function/etc. needs to be added and activated in order to display data.

## Dasbor

Page\: `data -> Dasbor`

Dasbor dapat digunakan untuk melihat data dan memanipulasi sistem, berkat banyaknya widget dasbor yang tersedia. Beberapa dasbor dapat dibuat serta dikunci untuk mencegah perubahan pengaturan.

## Widgets

Widget adalah elemen pada Dasbor yang memiliki sejumlah kegunaan, seperti melihat data (grafik, indikator, pengukur, dll.) atau berinteraksi dengan sistem (memanipulasi output, mengubah siklus tugas PWM, menanyakan atau memodifikasi database, dll.). Widget dapat dengan mudah diatur ulang dan diubah ukurannya dengan menyeret dan menjatuhkan. Untuk daftar lengkap Widget yang didukung, lihat [Supported Widgets](Supported-Widgets.md).

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
