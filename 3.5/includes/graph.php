<?php
/*
*  graph.php - Formats graph display javascript
*
*  Copyright (C) 2015  Kyle T. Gabriel
*
*  This file is part of Mycodo
*
*  Mycodo is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 3 of the License, or
*  (at your option) any later version.
*
*  Mycodo is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
*
*  Contact at kylegabriel.com
*/

if ($_POST['Generate_Graph_Span'] == "all") {
    $time_start = "0";
    $time_end = "0";
    $title = "";
} else {
    if ($_POST['Generate_Graph_Span'] == "1h") $time_start = date('Y/m/d-H:i:s', strtotime('-1 hour'));
    else if ($_POST['Generate_Graph_Span'] == "3h") $time_start = date('Y/m/d-H:i:s', strtotime('-3 hour'));
    else if ($_POST['Generate_Graph_Span'] == "6h") $time_start = date('Y/m/d-H:i:s', strtotime('-6 hour'));
    else if ($_POST['Generate_Graph_Span'] == "12h") $time_start = date('Y/m/d-H:i:s', strtotime('-12 hour'));
    else if ($_POST['Generate_Graph_Span'] == "1d") $time_start = date('Y/m/d-H:i:s', strtotime('-1 day'));
    else if ($_POST['Generate_Graph_Span'] == "3d") $time_start = date('Y/m/d-H:i:s', strtotime('-3 day'));
    else if ($_POST['Generate_Graph_Span'] == "1w") $time_start = date('Y/m/d-H:i:s', strtotime('-1 week'));
    else if ($_POST['Generate_Graph_Span'] == "2w") $time_start = date('Y/m/d-H:i:s', strtotime('-2 week'));
    else if ($_POST['Generate_Graph_Span'] == "1m") $time_start = date('Y/m/d-H:i:s', strtotime('-1 month'));
    else if ($_POST['Generate_Graph_Span'] == "3m") $time_start = date('Y/m/d-H:i:s', strtotime('-3 month'));
    else if ($_POST['Generate_Graph_Span'] == "6m") $time_start = date('Y/m/d-H:i:s', strtotime('-6 month'));
    else if ($_POST['Generate_Graph_Span'] == "1y") $time_start = date('Y/m/d-H:i:s', strtotime('-1 year'));
    $time_end = date('Y/m/d-H:i:s');
    $title = "<br>" . $_POST['Generate_Graph_Span'] . ': ' . $time_start . ' - ' . $time_end;
}

$sensor_type = $_POST['Generate_Graph_Type'];

if ($sensor_type != 'all') {

    $sensor_log_first = "/var/www/mycodo/log/sensor-$sensor_type.log";
    $sensor_log_second = "/var/www/mycodo/log/sensor-$sensor_type-tmp.log";
    $sensor_log_generate = "/var/tmp/sensor-$sensor_type-$graph_id.log";
    shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh x $sensor_type $time_start $time_end $sensor_log_first $sensor_log_second $sensor_log_generate");
    $sensor_log_file_final = "file.php?span=graph&file=sensor-$sensor_type-$graph_id.log";

    $relay_log_first = "/var/www/mycodo/log/relay.log";
    $relay_log_second = "/var/www/mycodo/log/relay-tmp.log";
    $relay_log_generate = "/var/tmp/relay-$graph_id.log";
    shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh x relay $time_start $time_end $relay_log_first $relay_log_second $relay_log_generate");
    $relay_log_file_final = "file.php?span=graph&file=relay-$graph_id.log";

    $sensor_num_array = "sensor_{$sensor_type}_id";
}

if ($sensor_type == 't' && count(${$sensor_num_array}) > 0) {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(sensor_csv) {
            $.getJSON("<?php echo $relay_log_file_final; ?>", function(relay_csv) {
                function getSensorData(sensor) {
                    var sensordata = [];
                    var lines = sensor_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == sensor) sensordata.push([date,parseInt(items[1])]);
                    });
                    return sensordata;
                }
                function getRelayData(relay) {
                    var relaydata = [];
                    var num_relays = <?php echo count($relay_id); ?>;
                    var lines = relay_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == relay) relaydata.push([date,parseFloat(items[4])]);
                    });
                    return relaydata;
                }
                $('#container').highcharts('StockChart', {
                    chart: {
                        zoomType: 'x',
                    },
                    title: {
                        text: 'Temperature Sensor Data<?php echo $title; ?>'
                    },
                    legend: {
                        enabled: true,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        y: 75,
                        itemMarginBottom: 5
                    },
                    exporting: {
                        fallbackToExportServer: false,
                    },
                    yAxis: [{
                        title: {
                            text: 'Temperature (°C)',
                        },
                        labels: {
                            format: '{value}°C',
                        },
                        height: '60%',
                    }, {
                        title: {
                            text: 'Duration (sec)'
                        },
                        labels: {
                            format: '{value}sec',
                        },
                        top: '65%',
                        height: '35%',
                        offset: 0,
                        lineWidth: 2
                    }],
                    series: [<?php
                    $count = 0;
                    for ($i = 0; $i < count(${$sensor_num_array}); $i++) {
                    ?>{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_t_name[$i]; ?> °C',
                        color: Highcharts.getOptions().colors[0],
                        data: getSensorData(0),
                        tooltip: {
                            valueSuffix: ' °C',
                            valueDecimals: 0,
                        }
                    },<?php
                    }
                    for ($i = 0; $i < count($relay_id); $i++) {
                    ?>{
                        name: 'R<?php echo $i+1 . " " . $relay_name[$i]; ?>',
                        type: 'column',
                        dataGrouping: {
                            approximation: 'low',
                            groupPixelWidth: 3,
                        },
                        color: Highcharts.getOptions().colors[<?php echo $i+1; ?>],
                        data: getRelayData(<?php echo $i+1; ?>),
                        yAxis: 1,
                        tooltip: {
                            valueSuffix: ' sec',
                            valueDecimals: 0,
                        }
                    },<?php 
                    }
                    ?>],
                    exporting: {
                        buttons: {
                            custom: {
                                text: "Hide All",
                                align: 'right',
                                x: -40,
                                symbolFill: '#B5C9DF',
                                hoverSymbolFill: '#779ABF',
                                _titleKey: 'Balance',
                                onclick: function () {
                                    Click();
                                    if (this.series[0].visible) {
                                        this.exportSVGElements[2].attr({ text: 'Hide All' });
                                    } else {
                                        this.exportSVGElements[2].attr({ text: 'Show All' });
                                    }
                                }
                            }
                        }
                    },
                    rangeSelector: {
                        buttons: [{
                            type: 'hour',
                            count: 1,
                            text: '1h'
                        }, {
                            type: 'hour',
                            count: 3,
                            text: '3h'
                        }, {
                            type: 'hour',
                            count: 6,
                            text: '6h'
                        }, {
                            type: 'hour',
                            count: 12,
                            text: '12h'
                        }, {
                            type: 'day',
                            count: 1,
                            text: '1d'
                        }, {
                            type: 'day',
                            count: 3,
                            text: '3d'
                        }, {
                            type: 'week',
                            count: 1,
                            text: '1w'
                        }, {
                            type: 'week',
                            count: 2,
                            text: '2w'
                        }, {
                            type: 'month',
                            count: 1,
                            text: '1m'
                        }, {
                            type: 'month',
                            count: 2,
                            text: '2m'
                        }, {
                            type: 'month',
                            count: 3,
                            text: '3m'
                        }, {
                            type: 'month',
                            count: 6,
                            text: '6m'
                        }, {
                            type: 'year',
                            count: 1,
                            text: '1y'
                        }, {
                            type: 'all',
                            text: 'Full'
                        }],
                        selected: 13
                    },
                    credits: {
                        enabled: false,
                        href: "https://github.com/kizniche/Mycodo",
                        text: "Mycodo"
                    }
                });
                function Click() {
                    var chart = $('#container').highcharts();
                    var series = chart.series[0];
                    if (series.visible) {
                        $(chart.series).each(function(){
                            //this.hide();
                            this.setVisible(false, false);
                        });
                        chart.redraw();
                    } else {
                        $(chart.series).each(function(){
                            //this.show();
                            this.setVisible(true, false);
                        });
                        chart.redraw();
                    }
                }
            });
        });
    });
</script>

    <?php
    } else if ($sensor_type == 'ht' && count(${$sensor_num_array}) > 0) {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(sensor_csv) {
            $.getJSON("<?php echo $relay_log_file_final; ?>", function(relay_csv) {
                function getSensorData(sensor, condition) {
                    var sensordata = [];
                    var lines = sensor_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (condition == 'temperature' && parseInt(items[4]) == sensor) sensordata.push([date,parseFloat(items[1])]);
                    if (condition == 'humidity' && parseInt(items[4]) == sensor) sensordata.push([date,parseFloat(items[2])]);
                    if (condition == 'dewpoint' && parseInt(items[4]) == sensor) sensordata.push([date,parseFloat(items[3])]);
                    });
                    return sensordata;
                }
                function getRelayData(relay) {
                    var relaydata = [];
                    var num_relays = <?php echo count($relay_id); ?>;
                    var lines = relay_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == relay) relaydata.push([date,parseFloat(items[4])]);
                    });
                    return relaydata;
                }
                $('#container').highcharts('StockChart', {
                    chart: {
                        zoomType: 'x',
                    },
                    title: {
                        text: 'Temperature/Humidity Sensor Data<?php echo $title; ?>'
                    },
                    legend: {
                        enabled: true,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        y: 75,
                        itemMarginBottom: 5
                    },
                    exporting: {
                        fallbackToExportServer: false,
                    },
                    yAxis: [{
                        title: {
                            text: 'Temperature (°C)',
                        },
                        labels: {
                            format: '{value}°C',
                            align: 'left',
                            x: -3
                        },
                        height: '60%',
                        minRange: 5,
                        opposite: false
                    },{
                        title: {
                            text: 'Humidity (%)',
                        },
                        labels: {
                            format: '{value}%',
                            align: 'right',
                            x: -3
                        },
                        height: '60%',
                        minRange: 10,
                    },{
                        title: {
                            text: 'Duration (sec)',
                        },
                        labels: {
                            format: '{value}sec',
                            align: 'right',
                            x: -3
                        },
                        top: '65%',
                        height: '35%',
                        offset: 0,
                        lineWidth: 2
                    }],
                    series: [<?php
                    $count = 0;
                    for ($i = 0; $i < count(${$sensor_num_array}); $i++) {
                    ?>{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_ht_name[$i]; ?> Humidity',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        yAxis: 1,
                        data: getSensorData(<?php echo $i; ?>, 'humidity'),
                        tooltip: {
                            valueSuffix: ' %',
                            valueDecimals: 1,
                        }
                    },{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_ht_name[$i]; ?> Temperature',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        data: getSensorData(<?php echo $i; ?>, 'temperature'),
                        tooltip: {
                            valueSuffix: '°C',
                            valueDecimals: 1,
                        }
                    },{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_ht_name[$i]; ?> Dew Point',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        data: getSensorData(<?php echo $i; ?>, 'dewpoint'),
                        tooltip: {
                            valueSuffix: ' °C',
                            valueDecimals: 1,
                        }
                    },<?php 
                    }
                    for ($i = 0; $i < count($relay_id); $i++) {
                    ?>{
                        name: 'R<?php echo $i+1 . " " . $relay_name[$i]; ?>',
                        type: 'column',
                        dataGrouping: {
                            approximation: 'low',
                            groupPixelWidth: 3,
                        },
                        color: Highcharts.getOptions().colors[<?php echo $i+1; ?>],
                        data: getRelayData(<?php echo $i+1; ?>),
                        yAxis: 2,
                        tooltip: {
                            valueSuffix: ' sec',
                            valueDecimals: 0,
                            shared: true,
                        }
                    },<?php 
                    }
                    ?>],
                    exporting: {
                        buttons: {
                            custom: {
                                text: "Hide All",
                                align: 'right',
                                x: -40,
                                symbolFill: '#B5C9DF',
                                hoverSymbolFill: '#779ABF',
                                _titleKey: 'Balance',
                                onclick: function () {
                                    Click();
                                    if (this.series[0].visible) {
                                        this.exportSVGElements[2].attr({ text: 'Hide All' });
                                    } else {
                                        this.exportSVGElements[2].attr({ text: 'Show All' });
                                    }
                                }
                            }
                        }
                    },
                    rangeSelector: {
                        buttons: [{
                            type: 'hour',
                            count: 1,
                            text: '1h'
                        }, {
                            type: 'hour',
                            count: 3,
                            text: '3h'
                        }, {
                            type: 'hour',
                            count: 6,
                            text: '6h'
                        }, {
                            type: 'hour',
                            count: 12,
                            text: '12h'
                        }, {
                            type: 'day',
                            count: 1,
                            text: '1d'
                        }, {
                            type: 'day',
                            count: 3,
                            text: '3d'
                        }, {
                            type: 'week',
                            count: 1,
                            text: '1w'
                        }, {
                            type: 'week',
                            count: 2,
                            text: '2w'
                        }, {
                            type: 'month',
                            count: 1,
                            text: '1m'
                        }, {
                            type: 'month',
                            count: 2,
                            text: '2m'
                        }, {
                            type: 'month',
                            count: 3,
                            text: '3m'
                        }, {
                            type: 'month',
                            count: 6,
                            text: '6m'
                        }, {
                            type: 'year',
                            count: 1,
                            text: '1y'
                        }, {
                            type: 'all',
                            text: 'Full'
                        }],
                        selected: 13
                    },
                    credits: {
                        enabled: false,
                        href: "https://github.com/kizniche/Mycodo",
                        text: "Mycodo"
                    }
                });
                function Click() {
                    var chart = $('#container').highcharts();
                    var series = chart.series[0];
                    if (series.visible) {
                        $(chart.series).each(function(){
                            //this.hide();
                            this.setVisible(false, false);
                        });
                        chart.redraw();
                    } else {
                        $(chart.series).each(function(){
                            //this.show();
                            this.setVisible(true, false);
                        });
                        chart.redraw();
                    }
                }
            });
        });
    });
</script>

    <?php
    } else if ($sensor_type == 'co2' && count(${$sensor_num_array}) > 0) {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(sensor_csv) {
            $.getJSON("<?php echo $relay_log_file_final; ?>", function(relay_csv) {
                function getSensorData(sensor) {
                    var sensordata = [];
                    var lines = sensor_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == sensor) sensordata.push([date,parseInt(items[1])]);
                    });
                    return sensordata;
                }
                function getRelayData(relay) {
                    var relaydata = [];
                    var num_relays = <?php echo count($relay_id); ?>;
                    var lines = relay_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == relay) relaydata.push([date,parseFloat(items[4])]);
                    });
                    return relaydata;
                }
                $('#container').highcharts('StockChart', {
                    chart: {
                        zoomType: 'x',
                    },
                    title: {
                        text: 'CO<sub>2</sub> Sensor Data<?php echo $title; ?>',
                        useHTML: true
                    },
                    legend: {
                        enabled: true,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        y: 75,
                        useHTML:true,
                        itemMarginBottom: 5
                    },
                    exporting: {
                        fallbackToExportServer: false,
                    },
                    yAxis: [{
                        title: {
                            text: 'CO<sub>2</sub> (ppmv)',
                            useHTML: true
                        },
                        labels: {
                            format: '{value}ppmv',
                        },
                        height: '60%',
                    }, {
                        title: {
                            text: 'Duration (sec)'
                        },
                        labels: {
                            format: '{value}sec',
                        },
                        top: '65%',
                        height: '35%',
                        offset: 0,
                        lineWidth: 2
                    }],
                    series: [<?php
                    $count = 0;
                    for ($i = 0; $i < count(${$sensor_num_array}); $i++) {
                    ?>{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_co2_name[$i]; ?> CO<sub>2</sub>',
                        color: Highcharts.getOptions().colors[0],
                        data: getSensorData(0),
                        tooltip: {
                            valueSuffix: ' ppmv',
                            valueDecimals: 0
                        }
                    },<?php
                    }
                    for ($i = 0; $i < count($relay_id); $i++) {
                    ?>{
                        name: 'R<?php echo $i+1 . " " . $relay_name[$i]; ?>',
                        type: 'column',
                        dataGrouping: {
                            approximation: 'low',
                            groupPixelWidth: 3
                        },
                        color: Highcharts.getOptions().colors[<?php echo $i+1; ?>],
                        data: getRelayData(<?php echo $i+1; ?>),
                        yAxis: 1,
                        tooltip: {
                            valueSuffix: ' sec',
                            valueDecimals: 0
                        }
                    },<?php 
                    }
                    ?>],
                    exporting: {
                        buttons: {
                            custom: {
                                text: "Hide All",
                                align: 'right',
                                x: -40,
                                symbolFill: '#B5C9DF',
                                hoverSymbolFill: '#779ABF',
                                _titleKey: 'Balance',
                                onclick: function () {
                                    Click();
                                    if (this.series[0].visible) {
                                        this.exportSVGElements[2].attr({ text: 'Hide All' });
                                    } else {
                                        this.exportSVGElements[2].attr({ text: 'Show All' });
                                    }
                                }
                            }
                        }
                    },
                    rangeSelector: {
                        buttons: [{
                            type: 'hour',
                            count: 1,
                            text: '1h'
                        }, {
                            type: 'hour',
                            count: 3,
                            text: '3h'
                        }, {
                            type: 'hour',
                            count: 6,
                            text: '6h'
                        }, {
                            type: 'hour',
                            count: 12,
                            text: '12h'
                        }, {
                            type: 'day',
                            count: 1,
                            text: '1d'
                        }, {
                            type: 'day',
                            count: 3,
                            text: '3d'
                        }, {
                            type: 'week',
                            count: 1,
                            text: '1w'
                        }, {
                            type: 'week',
                            count: 2,
                            text: '2w'
                        }, {
                            type: 'month',
                            count: 1,
                            text: '1m'
                        }, {
                            type: 'month',
                            count: 2,
                            text: '2m'
                        }, {
                            type: 'month',
                            count: 3,
                            text: '3m'
                        }, {
                            type: 'month',
                            count: 6,
                            text: '6m'
                        }, {
                            type: 'year',
                            count: 1,
                            text: '1y'
                        }, {
                            type: 'all',
                            text: 'Full'
                        }],
                        selected: 13
                    },
                    credits: {
                        enabled: false,
                        href: "https://github.com/kizniche/Mycodo",
                        text: "Mycodo"
                    }
                });
                function Click() {
                    var chart = $('#container').highcharts();
                    var series = chart.series[0];
                    if (series.visible) {
                        $(chart.series).each(function(){
                            //this.hide();
                            this.setVisible(false, false);
                        });
                        chart.redraw();
                    } else {
                        $(chart.series).each(function(){
                            //this.show();
                            this.setVisible(true, false);
                        });
                        chart.redraw();
                    }
                }
            });
        });
    });
</script>

    <?php
        } else if ($sensor_type == 'press' && count(${$sensor_num_array}) > 0) {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(sensor_csv) {
            $.getJSON("<?php echo $relay_log_file_final; ?>", function(relay_csv) {
                function getSensorData(sensor, condition) {
                    var sensordata = [];
                    var lines = sensor_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (condition == 'temperature' && parseInt(items[4]) == sensor) sensordata.push([date,parseFloat(items[1])]);
                    if (condition == 'pressure' && parseInt(items[4]) == sensor) sensordata.push([date,parseFloat(items[2])]);
                    });
                    return sensordata;
                }
                function getRelayData(relay) {
                    var relaydata = [];
                    var num_relays = <?php echo count($relay_id); ?>;
                    var lines = relay_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == relay) relaydata.push([date,parseFloat(items[4])]);
                    });
                    return relaydata;
                }
                $('#container').highcharts('StockChart', {
                    chart: {
                        zoomType: 'x',
                    },
                    title: {
                        text: 'Pressure Sensor Data<?php echo $title; ?>'
                    },
                    legend: {
                        enabled: true,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        y: 75,
                        itemMarginBottom: 5
                    },
                    exporting: {
                        fallbackToExportServer: false,
                    },
                    yAxis: [{
                        title: {
                            text: 'Temperature (°C)',
                        },
                        labels: {
                            format: '{value}°C',
                            align: 'left',
                            x: -3
                        },
                        height: '60%',
                        minRange: 5,
                        opposite: false
                    },{
                        title: {
                            text: 'Pressure (kPa)',
                        },
                        labels: {
                            format: '{value}kPa',
                            align: 'right',
                            x: -3
                        },
                        height: '60%',
                    },{
                        title: {
                            text: 'Duration (sec)',
                        },
                        labels: {
                            format: '{value}sec',
                            align: 'right',
                            x: -3
                        },
                        top: '65%',
                        height: '35%',
                        offset: 0,
                        lineWidth: 2
                    }],
                    series: [<?php
                    $count = 0;
                    for ($i = 0; $i < count(${$sensor_num_array}); $i++) {
                    ?>{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_press_name[$i]; ?> Pressure',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        yAxis: 1,
                        data: getSensorData(<?php echo $i; ?>, 'pressure'),
                        tooltip: {
                            valueSuffix: ' kPa',
                            valueDecimals: 0
                        }
                    },{
                        name: '<?php echo "S" . ($i+1) . " " . $sensor_press_name[$i]; ?> Temperature',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        data: getSensorData(<?php echo $i; ?>, 'temperature'),
                        tooltip: {
                            valueSuffix: '°C',
                            valueDecimals: 1
                        }
                    },<?php 
                    }
                    for ($i = 0; $i < count($relay_id); $i++) {
                    ?>{
                        name: 'R<?php echo $i+1 . " " . $relay_name[$i]; ?>',
                        type: 'column',
                        dataGrouping: {
                            approximation: 'low',
                            groupPixelWidth: 3,
                        },
                        color: Highcharts.getOptions().colors[<?php echo $i+1; ?>],
                        data: getRelayData(<?php echo $i+1; ?>),
                        yAxis: 2,
                        tooltip: {
                            valueSuffix: ' sec',
                            valueDecimals: 0,
                            shared: true,
                        }
                    },<?php 
                    }
                    ?>],
                    exporting: {
                        buttons: {
                            custom: {
                                text: "Hide All",
                                align: 'right',
                                x: -40,
                                symbolFill: '#B5C9DF',
                                hoverSymbolFill: '#779ABF',
                                _titleKey: 'Balance',
                                onclick: function () {
                                    Click();
                                    if (this.series[0].visible) {
                                        this.exportSVGElements[2].attr({ text: 'Hide All' });
                                    } else {
                                        this.exportSVGElements[2].attr({ text: 'Show All' });
                                    }
                                }
                            }
                        }
                    },
                    rangeSelector: {
                        buttons: [{
                            type: 'hour',
                            count: 1,
                            text: '1h'
                        }, {
                            type: 'hour',
                            count: 3,
                            text: '3h'
                        }, {
                            type: 'hour',
                            count: 6,
                            text: '6h'
                        }, {
                            type: 'hour',
                            count: 12,
                            text: '12h'
                        }, {
                            type: 'day',
                            count: 1,
                            text: '1d'
                        }, {
                            type: 'day',
                            count: 3,
                            text: '3d'
                        }, {
                            type: 'week',
                            count: 1,
                            text: '1w'
                        }, {
                            type: 'week',
                            count: 2,
                            text: '2w'
                        }, {
                            type: 'month',
                            count: 1,
                            text: '1m'
                        }, {
                            type: 'month',
                            count: 2,
                            text: '2m'
                        }, {
                            type: 'month',
                            count: 3,
                            text: '3m'
                        }, {
                            type: 'month',
                            count: 6,
                            text: '6m'
                        }, {
                            type: 'year',
                            count: 1,
                            text: '1y'
                        }, {
                            type: 'all',
                            text: 'Full'
                        }],
                        selected: 13
                    },
                    credits: {
                        enabled: false,
                        href: "https://github.com/kizniche/Mycodo",
                        text: "Mycodo"
                    }
                });
                function Click() {
                    var chart = $('#container').highcharts();
                    var series = chart.series[0];
                    if (series.visible) {
                        $(chart.series).each(function(){
                            //this.hide();
                            this.setVisible(false, false);
                        });
                        chart.redraw();
                    } else {
                        $(chart.series).each(function(){
                            //this.show();
                            this.setVisible(true, false);
                        });
                        chart.redraw();
                    }
                }
            });
        });
    });
</script>

<?php
    } else if ($sensor_type == 'all') {
        $sensor_type_list = ['t','ht','co2','press'];
        $files = array();
        for ($i=0; $i < count($sensor_type_list); $i++) {
            $sensor_type = $sensor_type_list[$i];
            $sensor_num_array = "sensor_{$sensor_type}_id";
            $sensor_log_first = "/var/www/mycodo/log/sensor-$sensor_type.log";
            $sensor_log_second = "/var/www/mycodo/log/sensor-$sensor_type-tmp.log";
            $sensor_log_generate = "/var/tmp/sensor-all-$sensor_type-$graph_id.log";
            $files[] = $sensor_log_generate;
            shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh $sensor_type all $time_start $time_end $sensor_log_first $sensor_log_second $sensor_log_generate");
        }
        $out = array();
        foreach($files as $file) {
            $name = "/var/tmp/sensor-final-all-$graph_id.log";
            if (!isset($out[$name])) {
                $out[$name] = fopen($name, "w");
            }
            fwrite($out[$name], file_get_contents($file));
        }
        foreach ($out as $f) {
            fclose($f);
        }
        $sensor_log_file_final = "file.php?span=graph&file=sensor-final-all-$graph_id.log";
        $relay_log_first = "/var/www/mycodo/log/relay.log";
        $relay_log_second = "/var/www/mycodo/log/relay-tmp.log";
        $relay_log_generate = "/var/tmp/relay-$graph_id.log";
        shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh x relay $time_start $time_end $relay_log_first $relay_log_second $relay_log_generate");
        $relay_log_file_final = "file.php?span=graph&file=relay-$graph_id.log";
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(sensor_csv) {
            $.getJSON("<?php echo $relay_log_file_final; ?>", function(relay_csv) {
                function getSensorData(sensor, type, condition) {
                    var sensordata = [];
                    var lines = sensor_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[1].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (type == 't') {
                            if (parseInt(items[3]) == sensor && items[0] == 't') sensordata.push([date,parseInt(items[2])]);
                        } else if (type == 'ht') {
                            if (condition == 'temp' && parseInt(items[5]) == sensor && items[0] == 'ht') sensordata.push([date,parseFloat(items[2])]);
                            if (condition == 'hum' && parseInt(items[5]) == sensor && items[0] == 'ht') sensordata.push([date,parseFloat(items[3])]);
                            if (condition == 'dp' && parseInt(items[5]) == sensor && items[0] == 'ht') sensordata.push([date,parseFloat(items[4])]);
                        } else if (type == 'co2') {
                            if (parseInt(items[3]) == sensor && items[0] == 'co2') sensordata.push([date,parseInt(items[2])]);
                        } else if (type == 'press') {
                            if (condition == 'temp' && parseInt(items[5]) == sensor && items[0] == 'press') sensordata.push([date,parseFloat(items[2])]);
                            if (condition == 'press' && parseInt(items[5]) == sensor && items[0] == 'press') sensordata.push([date,parseFloat(items[3])]);
                        }
                    });
                    return sensordata;
                }
                function getRelayData(relay) {
                    var relaydata = [];
                    var num_relays = <?php echo count($relay_id); ?>;
                    var lines = relay_csv.split('\n');
                    $.each(lines, function(lineNo,line) {
                        if (line == "") return;
                        var items = line.split(' ');
                        var timeElements = items[0].split('-');
                        var date = timeElements[0].split('/');
                        var time = timeElements[1].split(':');
                        var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                        if (parseInt(items[2]) == relay) relaydata.push([date,parseFloat(items[4])]);
                    });
                    return relaydata;
                }
                $('#container').highcharts('StockChart', {
                    chart: {
                        zoomType: 'x',
                    },
                    title: {
                        text: 'All Sensors and Relay Data<?php echo $title; ?>'
                    },
                    legend: {
                        enabled: true,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        y: 75,
                        itemMarginBottom: 5
                    },
                    exporting: {
                        fallbackToExportServer: false,
                    },
                    yAxis: [<?php
                    if (array_sum($sensor_t_id) || array_sum($sensor_ht_id) || array_sum($sensor_press_id)) {
                    ?>{
                        title: {
                            text: 'Temperature (°C)',
                        },
                        labels: {
                            format: '{value}°C',
                        },
                        height: '60%',
                        minRange: 5,
                        opposite: false
                    },<?php
                    } 
                    if (array_sum($sensor_co2_id)) {
                    ?>{
                        title: {
                            text: 'CO<sub>2</sub> (ppmv)',
                            useHTML: true
                        },
                        labels: {
                            format: '{value}ppmv',
                        },
                        height: '60%',
                        opposite: false
                    },<?php
                    }
                    if (array_sum($sensor_ht_id)) {
                    ?>{
                        title: {
                            text: 'Humidity (%)',
                        },
                        labels: {
                            format: '{value}%',
                        },
                        height: '60%',
                        minRange: 10,
                    },<?php
                    }
                    if (array_sum($sensor_press_id)) {
                    ?>{
                        title: {
                            text: 'Pressure (kPa)',
                        },
                        labels: {
                            format: '{value}kPa',
                        },
                        height: '60%',
                    },<?php
                    }
                    if (array_sum($relay_id)) {
                    ?>{
                        title: {
                            text: 'Duration (sec)',
                        },
                        labels: {
                            format: '{value}sec',
                        },
                        top: '65%',
                        height: '35%',
                        offset: 0,
                        lineWidth: 2
                    }<?php
                    }
                    ?>],
                    series: [<?php
                    $count = 0;
                    for ($i = 0; $i < count($relay_id); $i++) {
                    ?>{
                        name: 'R<?php echo $i+1 . " " . $relay_name[$i]; ?>',
                        type: 'column',
                        dataGrouping: {
                            approximation: 'low',
                            groupPixelWidth: 3,
                        },
                        color: Highcharts.getOptions().colors[<?php echo $i+1; ?>],
                        data: getRelayData(<?php echo $i+1; ?>),
                        yAxis: 4,
                        tooltip: {
                            valueSuffix: ' sec',
                            valueDecimals: 0,
                            shared: true,
                        }
                    },<?php 
                    }
                    for ($i = 0; $i < count($sensor_t_id); $i++) {
                        if ($sensor_t_graph[$i]) {
                    ?>{
                        name: '<?php echo "T" . ($i+1) . " " . $sensor_t_name[$i]; ?> Temperature',
                        color: Highcharts.getOptions().colors[0],
                        data: getSensorData(<?php echo $i; ?>, 't', 0),
                        tooltip: {
                            valueSuffix: ' °C',
                            valueDecimals: 0,
                        }
                    },<?php
                        }
                    }
                    for ($i = 0; $i < count($sensor_ht_id); $i++) {
                        if ($sensor_ht_graph[$i]) {
                    ?>{
                        name: '<?php echo "HT" . ($i+1) . " " . $sensor_ht_name[$i]; ?> Humidity',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        yAxis: 2,
                        data: getSensorData(<?php echo $i; ?>, 'ht', 'hum'),
                        tooltip: {
                            valueSuffix: ' %',
                            valueDecimals: 1,
                        }
                    },{
                        name: '<?php echo "HT" . ($i+1) . " " . $sensor_ht_name[$i]; ?> Temperature',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        data: getSensorData(<?php echo $i; ?>, 'ht', 'temp'),
                        tooltip: {
                            valueSuffix: '°C',
                            valueDecimals: 1,
                        }
                    },{
                        name: '<?php echo "HT" . ($i+1) . " " . $sensor_ht_name[$i]; ?> Dew Point',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        data: getSensorData(<?php echo $i; ?>, 'ht', 'dp'),
                        tooltip: {
                            valueSuffix: ' °C',
                            valueDecimals: 1,
                        }
                    },<?php
                        }
                    }
                    for ($i = 0; $i < count($sensor_co2_id); $i++) {
                        if ($sensor_co2_graph[$i]) {
                    ?>{
                        name: '<?php echo "CO2" . ($i+1) . " " . $sensor_co2_name[$i]; ?> CO<sub>2</sub>',
                        color: Highcharts.getOptions().colors[0],
                        yAxis: 1,
                        data: getSensorData(<?php echo $i; ?>, 'co2', 0),
                        tooltip: {
                            valueSuffix: ' ppmv',
                            valueDecimals: 0
                        }
                    },<?php
                        }
                    }
                    for ($i = 0; $i < count($sensor_press_id); $i++) {
                        if ($sensor_press_graph[$i]) {
                    ?>{
                        name: '<?php echo "Press" . ($i+1) . " " . $sensor_press_name[$i]; ?> Pressure',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        yAxis: 3,
                        data: getSensorData(<?php echo $i; ?>, 'press', 'press'),
                        tooltip: {
                            valueSuffix: ' kPa',
                            valueDecimals: 0
                        }
                    },{
                        name: '<?php echo "Press" . ($i+1) . " " . $sensor_press_name[$i]; ?> Temperature',
                        color: Highcharts.getOptions().colors[<?php echo $count; $count++; ?>],
                        data: getSensorData(<?php echo $i; ?>, 'press', 'temp'),
                        tooltip: {
                            valueSuffix: '°C',
                            valueDecimals: 1
                        }
                    },<?php
                        }
                    }
                    ?>],
                    exporting: {
                        buttons: {
                            custom: {
                                text: "Hide All",
                                align: 'right',
                                x: -40,
                                symbolFill: '#B5C9DF',
                                hoverSymbolFill: '#779ABF',
                                _titleKey: 'Balance',
                                onclick: function () {
                                    Click();
                                    if (this.series[0].visible) {
                                        this.exportSVGElements[2].attr({ text: 'Hide All' });
                                    } else {
                                        this.exportSVGElements[2].attr({ text: 'Show All' });
                                    }
                                }
                            }
                        }
                    },
                    rangeSelector: {
                        buttons: [{
                            type: 'hour',
                            count: 1,
                            text: '1h'
                        }, {
                            type: 'hour',
                            count: 3,
                            text: '3h'
                        }, {
                            type: 'hour',
                            count: 6,
                            text: '6h'
                        }, {
                            type: 'hour',
                            count: 12,
                            text: '12h'
                        }, {
                            type: 'day',
                            count: 1,
                            text: '1d'
                        }, {
                            type: 'day',
                            count: 3,
                            text: '3d'
                        }, {
                            type: 'week',
                            count: 1,
                            text: '1w'
                        }, {
                            type: 'week',
                            count: 2,
                            text: '2w'
                        }, {
                            type: 'month',
                            count: 1,
                            text: '1m'
                        }, {
                            type: 'month',
                            count: 2,
                            text: '2m'
                        }, {
                            type: 'month',
                            count: 3,
                            text: '3m'
                        }, {
                            type: 'month',
                            count: 6,
                            text: '6m'
                        }, {
                            type: 'year',
                            count: 1,
                            text: '1y'
                        }, {
                            type: 'all',
                            text: 'Full'
                        }],
                        selected: 13
                    },
                    credits: {
                        enabled: false,
                        href: "https://github.com/kizniche/Mycodo",
                        text: "Mycodo"
                    }
                });
                function Click() {
                    var chart = $('#container').highcharts();
                    var series = chart.series[0];
                    if (series.visible) {
                        $(chart.series).each(function(){
                            //this.hide();
                            this.setVisible(false, false);
                        });
                        chart.redraw();
                    } else {
                        $(chart.series).each(function(){
                            //this.show();
                            this.setVisible(true, false);
                        });
                        chart.redraw();
                    }
                }
            });
        });
    });
</script>

<?php
}
foreach(glob("/var/tmp/sensor-all-*") as $f) {
    unlink($f);
}
