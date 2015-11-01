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
$sensor_log_file_final = "image.php?span=graph&file=sensor-$sensor_type-$graph_id.log";


if ($sensor_type == 't') {
    ?>

<script type="text/javascript">
    $(document).ready(function() {
        var data1 = [];
        
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(csv) {
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
        });
    });
</script>

    <?php
    } else if ($sensor_type == 'ht' && count(${$sensor_num_array}) > 0) {

        $relay_log_first = "/var/www/mycodo/log/relay.log";
        $relay_log_second = "/var/www/mycodo/log/relay-tmp.log";
        $relay_log_generate = "/var/tmp/relay-$graph_id.log";
        shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh x relay 0 $relay_log_first $relay_log_second $relay_log_generate");
        $relay_log_file_final = "image.php?span=graph&file=relay-$graph_id.log";
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
                    legend: {
                        enabled: true,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        y: 75,
                    },
                    exporting: {
                        width: 1200,
                        scale: 1,
                        url: 'https://export.highcharts.com/',
                    },
                    title: {
                        text: 'Temperature/Humidity Sensor Data'
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
                            text: 'Duration (sec)'
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
            });
        });
    });
</script>

    <?php
    } else if ($sensor_type == 'co2') {

        $relay_log_first = "/var/www/mycodo/log/relay.log";
        $relay_log_second = "/var/www/mycodo/log/relay-tmp.log";
        $relay_log_generate = "/var/tmp/relay-$graph_id.log";
        shell_exec("/var/www/mycodo/cgi-bin/log-parser-chart.sh x relay 0 $relay_log_first $relay_log_second $relay_log_generate");
        $relay_log_file_final = "image.php?span=graph&file=relay-$graph_id.log";

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
                    legend: {
                        enabled: true,
                    },
                    title: {
                        text: 'CO2 Sensor Data'
                    },
                    yAxis: [{
                        title: {
                            text: 'CO2 (ppmv)',
                        },
                        labels: {
                            format: '{value}ppmv',
                            align: 'right',
                            x: -3
                        },
                        height: '60%',
                    }, {
                        title: {
                            text: 'Duration (sec)'
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
                    series: [{
                        name: '<?php echo $sensor_ht_name[$i]; ?> CO2',
                        color: Highcharts.getOptions().colors[0],
                        data: getSensorData(0),
                        tooltip: {
                            valueSuffix: ' ppmv',
                            valueDecimals: 0,
                        }
                    }<?php
                    for ($i = 0; $i < count($relay_id); $i++) {
                    ?>,{
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
                    }<?php 
                    }
                    ?>],
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
        
        $.getJSON("<?php echo $sensor_log_file_final; ?>", function(csv) {
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
                },
            });
        });
    });
</script>
<?php
}
