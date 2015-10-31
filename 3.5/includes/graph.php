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

$sensor_type = $_POST['Generate_Graph'];
$sensor_num_array = "sensor_{$sensor_type}_id";
$number_lines = 0; // all
$sensor_log_first = "/var/www/mycodo/log/sensor-$sensor_type.log";
$sensor_log_second = "/var/www/mycodo/log/sensor-$sensor_type-tmp.log";
$sensor_log_generate = "/var/tmp/sensor-$sensor_type-$graph_id.log";
shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh x $sensor_type $number_lines $sensor_log_first $sensor_log_second $sensor_log_generate");

for ($i=0; $i < count(${$sensor_num_array}); $i++) {
    $sensor_log_generate = "/var/tmp/sensor-$sensor_type-$graph_id-$i.log";
    shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh $i $sensor_type $number_lines $sensor_log_first $sensor_log_second $sensor_log_generate");
}
$log_file_final = "image.php?span=graph_ht&file=sensor-$sensor_type-$graph_id.log";


if ($sensor_type == 't') {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        var data1 = [];
        
        $.getJSON("<?php echo $log_file_final; ?>", function(csv) {
            var lines = csv.split('\n');
            $.each(lines, function(lineNo,line) {
                if (line == "") return;
                var items = line.split(' ');
                var timeElements = items[0].split('-');
                var date = timeElements[0].split('/');
                var time = timeElements[1].split(':');
                var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                data1.push([date,parseFloat(items[1])]);
            });

            $('#container').highcharts('StockChart', {
                chart: {
                    renderTo: 'container',
                    zoomType: 'x',
                },
                legend: {
                    enabled: true
                },
                title: {
                    text: 'Temperature'
                },
                yAxis: {
                    title: {
                        text: 'Temperature (°C)',
                    },
                    labels: {
                        format: '{value}°C',
                    }
                },
                series: [{
                    name: 'Temperature',
                    color: Highcharts.getOptions().colors[0],
                    data: data1,
                    tooltip: {
                        valueSuffix: ' °C',
                        valueDecimals: 1
                    }
                }],
                rangeSelector: {
                    buttons: [{
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
                        count: 6,
                        text: '6m'
                    }, {
                        type: 'year',
                        count: 1,
                        text: '1y'
                    }, {
                        type: 'all',
                        text: 'All'
                    }],
                    selected: 8
                },

                credits: {
                    enabled: false,
                    href: "https://github.com/kizniche/Mycodo",
                    text: "Mycodo"
                }
            });
        });
    });
</script>

    <?php
    } else if ($sensor_type == 'ht') {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        var num_sensors = <?php echo count(${$sensor_num_array}); ?>;
        
        $.getJSON("<?php echo $log_file_final; ?>", function(csv) {
            function getData(sensor, condition) {
                var data = [];
                var lines = csv.split('\n');
                $.each(lines, function(lineNo,line) {
                    if (line == "") return;
                    var items = line.split(' ');
                    var timeElements = items[0].split('-');
                    var date = timeElements[0].split('/');
                    var time = timeElements[1].split(':');
                    var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                    if (condition == 'temperature' && parseInt(items[4]) == sensor) data.push([date,parseFloat(items[1])]);
                    if (condition == 'humidity' && parseInt(items[4]) == sensor) data.push([date,parseFloat(items[2])]);
                    if (condition == 'dewpoint' && parseInt(items[4]) == sensor) data.push([date,parseFloat(items[3])]);
                });
            return data;
            }

            $('#containerx').highcharts('StockChart', {
                chart: {
                    renderTo: 'container',
                    zoomType: 'x',
                    alignTicks: false
                },

                legend: {
                    enabled: true
                },

                title: {
                    text: 'All Temperature/Humidity Sensors Combined'
                },

                yAxis: [{ // Primary yAxis
                    title: {
                        text: 'Temperature (°C)',
                    },
                    labels: {
                        format: '{value}°C',
                    },
                    min: 10,
                    max: 35,
                    tickInterval: 5,
                    opposite: false
                }, { // Secondary yAxis
                    title: {
                        text: 'Humidity (%)',
                    },
                    labels: {
                        format: '{value} %',
                    },
                    min: 0,
                    max: 100,
                    gridLineWidth: 0,
                    tickInterval: 20,
                }],

                series: [<?php
                for ($i = 0; $i < count(${$sensor_num_array}); $i++) {
                ?>{
                        name: 'Humidity <?php echo $i+1; ?>',
                        color: Highcharts.getOptions().colors[0],
                        yAxis: 1,
                        data: getData(<?php echo $i; ?>, 'humidity'),
                        tooltip: {
                            valueSuffix: ' %',
                            valueDecimals: 1
                        }
                    },{
                        name: 'Temperature <?php echo $i+1; ?>',
                        color: Highcharts.getOptions().colors[5],
                        data: getData(<?php echo $i; ?>, 'temperature'),
                        tooltip: {
                            valueSuffix: '°C',
                            valueDecimals: 1
                        }
                    },{
                        name: 'Dew Point <?php echo $i+1; ?>',
                        color: Highcharts.getOptions().colors[2],
                        data: getData(<?php echo $i; ?>, 'dewpoint'),
                        tooltip: {
                            valueSuffix: ' °C',
                            valueDecimals: 1
                        }
                    },<?php 
                }
                ?>],
                rangeSelector: {
                    buttons: [{
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
                        count: 6,
                        text: '6m'
                    }, {
                        type: 'year',
                        count: 1,
                        text: '1y'
                    }, {
                        type: 'all',
                        text: 'All'
                    }],
                    selected: 8
                },
                credits: {
                    enabled: false,
                    href: "https://github.com/kizniche/Mycodo",
                    text: "Mycodo"
                }
            });
        });
    });
</script>

    <?php
        for ($i=0; $i < count(${$sensor_num_array}); $i++) {
            $log_file_final = "image.php?span=graph_ht&file=sensor-$sensor_type-$graph_id-$i.log";
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        var data1 = [],
            data2 = [],
            data3 = [];
        
        $.getJSON("<?php echo $log_file_final; ?>", function(csv) {
            var lines = csv.split('\n');
            $.each(lines, function(lineNo,line) {
                if (line == "") return;
                var items = line.split(' ');
                var timeElements = items[0].split('-');
                var date = timeElements[0].split('/');
                var time = timeElements[1].split(':');
                var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                data1.push([date,parseFloat(items[1])]);
                data2.push([date,parseFloat(items[2])]);
                data3.push([date,parseFloat(items[3])]);
            });

            $('#container<?php echo $i+1; ?>').highcharts('StockChart', {
                chart: {
                    renderTo: 'container',
                    zoomType: 'x',
                    alignTicks: false
                },

                legend: {
                    enabled: true
                },

                title: {
                    text: 'Temperature/Humidity Sensor <?php echo $i+1 . " (" . $sensor_ht_name[$i] . ")"; ?>'
                },

                yAxis: [{ // Primary yAxis
                    title: {
                        text: 'Temperature (°C)',
                    },
                    labels: {
                        format: '{value}°C',
                    },
                    min: 10,
                    max: 35,
                    tickInterval: 5,
                    opposite: false
                }, { // Secondary yAxis
                    title: {
                        text: 'Humidity (%)',
                    },
                    labels: {
                        format: '{value} %',
                    },
                    min: 0,
                    max: 100,
                    gridLineWidth: 0,
                    tickInterval: 20,
                }],

                series: [{
                    name: 'Humidity',
                    color: Highcharts.getOptions().colors[0],
                    yAxis: 1,
                    data: data2,
                    tooltip: {
                        valueSuffix: ' %',
                        valueDecimals: 1
                    }
                },{
                    name: 'Temperature',
                    color: Highcharts.getOptions().colors[5],
                    data: data1,
                    tooltip: {
                        valueSuffix: '°C',
                        valueDecimals: 1
                    }
                },{
                    name: 'Dew Point',
                    color: Highcharts.getOptions().colors[2],
                    data: data3,
                    tooltip: {
                        valueSuffix: ' °C',
                        valueDecimals: 1
                    }
                }],
                rangeSelector: {
                    buttons: [{
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
                        count: 6,
                        text: '6m'
                    }, {
                        type: 'year',
                        count: 1,
                        text: '1y'
                    }, {
                        type: 'all',
                        text: 'All'
                    }],
                    selected: 8
                },
                credits: {
                    enabled: false,
                    href: "https://github.com/kizniche/Mycodo",
                    text: "Mycodo"
                }
            });
        });
    });
</script>

    <?php
        }
    } else if ($sensor_type == 'co2') {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        var data1 = [];
        
        $.getJSON("<?php echo $log_file_final; ?>", function(csv) {
            var lines = csv.split('\n');
            $.each(lines, function(lineNo,line) {
                if (line == "") return;
                var items = line.split(' ');
                var timeElements = items[0].split('-');
                var date = timeElements[0].split('/');
                var time = timeElements[1].split(':');
                var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                data1.push([date,parseInt(items[1])]);
            });

            $('#container').highcharts('StockChart', {
                chart: {
                    renderTo: 'container',
                    zoomType: 'x',
                },
                legend: {
                    enabled: true
                },
                title: {
                    text: 'CO2'
                },
                yAxis: {
                    title: {
                        text: 'CO2 (ppmv)',
                    },
                    labels: {
                        format: '{value}ppmv',
                    }
                },
                series: [{
                    name: 'CO2',
                    color: Highcharts.getOptions().colors[0],
                    data: data1,
                    tooltip: {
                        valueSuffix: ' ppmv',
                        valueDecimals: 0
                    }
                }],
                rangeSelector: {
                    buttons: [{
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
                        count: 6,
                        text: '6m'
                    }, {
                        type: 'year',
                        count: 1,
                        text: '1y'
                    }, {
                        type: 'all',
                        text: 'All'
                    }],
                    selected: 8
                },

                credits: {
                    enabled: false,
                    href: "https://github.com/kizniche/Mycodo",
                    text: "Mycodo"
                }
            });
        });
    });
</script>

    <?php
    } else if ($sensor_type == 'press') {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        var data1 = [],
            data2 = [];
        
        $.getJSON("<?php echo $log_file_final; ?>", function(csv) {
            var lines = csv.split('\n');
            $.each(lines, function(lineNo,line) {
                if (line == "") return;
                var items = line.split(' ');
                var timeElements = items[0].split('-');
                var date = timeElements[0].split('/');
                var time = timeElements[1].split(':');
                var date = Date.UTC(date[0], date[1]-1, date[2], time[0], time[1], time[2], 0);
                data1.push([date,parseFloat(items[1])]);
                data2.push([date,parseInt(items[2])]);
            });

            $('#container').highcharts('StockChart', {
                chart: {
                    renderTo: 'container',
                    zoomType: 'x',
                    alignTicks: false
                },

                legend: {
                    enabled: true
                },

                title: {
                    text: 'Pressure Sensor'
                },

                yAxis: [{ // Primary yAxis
                    title: {
                        text: 'Temperature (°C)',
                    },
                    labels: {
                        format: '{value}°C',
                    },
                    min: 10,
                    max: 35,
                    tickInterval: 5,
                    opposite: false
                }, { // Secondary yAxis
                    title: {
                        text: 'Pressure (kPa)',
                    },
                    labels: {
                        format: '{value} kPa',
                    },
                    min: 96000,
                    max: 100000,
                    gridLineWidth: 0,
                    tickInterval: 500,
                }],

                series: [{
                    name: 'Pressure',
                    color: Highcharts.getOptions().colors[0],
                    yAxis: 1,
                    data: data2,
                    tooltip: {
                        valueSuffix: ' kPa',
                        valueDecimals: 0
                    }
                },{
                    name: 'Temperature',
                    color: Highcharts.getOptions().colors[5],
                    data: data1,
                    tooltip: {
                        valueSuffix: '°C',
                        valueDecimals: 1
                    }
                }],
                rangeSelector: {
                    buttons: [{
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
                        count: 6,
                        text: '6m'
                    }, {
                        type: 'year',
                        count: 1,
                        text: '1y'
                    }, {
                        type: 'all',
                        text: 'All'
                    }],
                    selected: 8
                },

                credits: {
                    enabled: false,
                    href: "https://github.com/kizniche/Mycodo",
                    text: "Mycodo"
                },
            });
        });
    });
</script>
<?php
}
