#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  mycodoGraph.py - Mycodo Graph Module
#
#  Copyright (C) 2015  Kyle T. Gabriel
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com

install_directory = "/var/www/mycodo"

import datetime
import fileinput
import logging
import os
import subprocess

log_path = "%s/log" % install_directory # Where generated logs are stored
image_path = "%s/images" % install_directory # Where generated graphs are stored

# Logs that are on the tempfs and are written to every sensor read
sensor_t_log_file_tmp = "%s/sensor-t-tmp.log" % log_path
sensor_ht_log_file_tmp = "%s/sensor-ht-tmp.log" % log_path
sensor_co2_log_file_tmp = "%s/sensor-co2-tmp.log" % log_path
relay_log_file_tmp = "%s/relay-tmp.log" % log_path

# Logs that are periodically concatenated (every 6 hours) to the SD card
sensor_t_log_file = "%s/sensor-t.log" % log_path
sensor_ht_log_file = "%s/sensor-ht.log" % log_path
sensor_co2_log_file = "%s/sensor-co2.log" % log_path
relay_log_file = "%s/relay.log" % log_path

#################################################
#                Graph Generation               #
#################################################

# Generate gnuplot graph
def generate_graph(sensor_type, graph_type, graph_span, graph_id, sensor_number, sensor_t_name, sensor_t_graph, sensor_t_period, pid_t_temp_relay_high, pid_t_temp_relay_low, sensor_ht_name, sensor_ht_graph, sensor_ht_period, pid_ht_temp_relay_high, pid_ht_temp_relay_low, pid_ht_hum_relay_high, pid_ht_hum_relay_low, sensor_co2_name, sensor_co2_graph, sensor_co2_period, pid_co2_relay_high, pid_co2_relay_low, relay_name):
    logging.debug("[Generate Graph] Parsing logs...")
    sensor_t_log_final = [0] * 5
    sensor_ht_log_final = [0] * 5
    sensor_co2_log_final = [0] * 5
    tmp_path = "/var/tmp"
    h = 0
    d = 0
    seconds = None
    cmd = None

    # Calculate a past date from a number of hours or days ago
    if graph_span == "1h":
        h = 1
        seconds = 3600
        time_ago = '1 Hour'
    elif graph_span == "6h":
        h = 6
        seconds = 21600
        time_ago = '6 Hours'
    elif graph_span == "12h":
        h = 12
        seconds = 43200
        time_ago = '12 Hours'
    elif graph_span == "1d" or graph_span == "default":
        d = 1
        seconds = 86400
        time_ago = '1 Day'
    elif graph_span == "3d":
        d = 3
        seconds = 259200
        time_ago = '3 Days'
    elif graph_span == "1w":
        d = 7
        seconds = 604800
        time_ago = '1 Week'
    elif graph_span == "1m":
        d = 30
        seconds = 2592000
        time_ago = '1 Month'
    elif graph_span == "3m":
        d = 90
        seconds = 7776000
        time_ago = '3 Months'
    elif graph_span == "legend-full":
        h = 6
        seconds = 21600
        time_ago = '6 Hours'
    date_now = datetime.datetime.now().strftime("%Y %m %d %H %M %S")
    date_now_disp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
    date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%d/%m/%Y %H:%M:%S")

    relay_log_files_combine = [relay_log_file, relay_log_file_tmp]
    relay_log_generate = "%s/relay-logs-combined.log" % tmp_path
    with open(relay_log_generate, 'w') as fout:
        for line in fileinput.input(relay_log_files_combine):
            fout.write(line)

    # only combined graphs get logs concatentated here. Separate graph logs are 
    # concatenated by the php code (to prevent redundant combining of log data)
    if graph_span == "default":
        if sensor_type == "t":
            sensor_t_log_generate = "%s/sensor-%s-logs-%s.log" % (
                tmp_path, sensor_type, graph_span)
            lines = 86400
            sensor_t_log_final[1] = "%s/sensor-%s-logs-%s-%s-%s-day.log" %  (
                tmp_path, sensor_type, graph_span, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_t_log_generate, sensor_t_log_final[1])
            logging.debug("[Generate Graph] cmd: %s", cmd)
            os.system(cmd)

            lines = 604800
            sensor_t_log_final[2] = "%s/sensor-%s-logs-%s-%s-%s-week.log" %  (
                tmp_path, sensor_type, graph_span, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_t_log_generate, sensor_t_log_final[2])
            logging.debug("[Generate Graph] cmd: %s", cmd)
            os.system(cmd)

        if sensor_type == "ht":
            sensor_ht_log_generate = "%s/sensor-%s-logs-%s.log" % (
                tmp_path, sensor_type, graph_span)
            lines = 86400
            sensor_ht_log_final[1] = "%s/sensor-%s-logs-%s-%s-%s-day.log" %  (
                tmp_path, sensor_type, graph_span, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_ht_log_generate, sensor_ht_log_final[1])
            logging.debug("[Generate Graph] cmd: %s", cmd)
            os.system(cmd)

            lines = 604800
            sensor_ht_log_final[2] = "%s/sensor-%s-logs-%s-%s-%s-week.log" %  (
                tmp_path, sensor_type, graph_span, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_ht_log_generate, sensor_ht_log_final[2])
            logging.debug("[Generate Graph] cmd: %s", cmd)
            os.system(cmd)

        if sensor_type == "co2":
            sensor_co2_log_generate = "%s/sensor-%s-logs-%s.log" % (
                tmp_path, sensor_type, graph_span)
            lines = 86400
            sensor_co2_log_final[1] = "%s/sensor-%s-logs-%s-%s-%s-day.log" %  (
                tmp_path, sensor_type, graph_span, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_co2_log_generate, sensor_co2_log_final[1])
            logging.debug("[Generate Graph] cmd: %s", cmd)
            os.system(cmd)

            lines = 604800
            sensor_co2_log_final[2] = "%s/sensor-%s-logs-%s-%s-%s-week.log" %  (
                tmp_path, sensor_type, graph_span, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_co2_log_generate, sensor_co2_log_final[2])
            logging.debug("[Generate Graph] cmd: %s", cmd)
            os.system(cmd)

    elif graph_type == "combined":
        # Combine sensor and relay logs on SD card with sensor and relay logs in /tmp
        if sum(sensor_t_graph):
            sensor_t_log_files_combine = [sensor_t_log_file, sensor_t_log_file_tmp]
            sensor_t_log_generate = "%s/sensor-%s-logs-%s.log" % (tmp_path, 't', graph_type)
            with open(sensor_t_log_generate, 'w') as fout:
                for line in fileinput.input(sensor_t_log_files_combine):
                    fout.write(line)
        else:
            sensor_t_log_generate = None

        if sum(sensor_ht_graph):
            sensor_ht_log_files_combine = [sensor_ht_log_file, sensor_ht_log_file_tmp]
            sensor_ht_log_generate = "%s/sensor-%s-logs-%s.log" % (tmp_path, 'ht', graph_type)
            with open(sensor_ht_log_generate, 'w') as fout:
                for line in fileinput.input(sensor_ht_log_files_combine):
                    fout.write(line)
        else:
            sensor_ht_log_generate = None

        if sum(sensor_co2_graph):
            sensor_co2_log_files_combine = [sensor_co2_log_file, sensor_co2_log_file_tmp]
            sensor_co2_log_generate = "%s/sensor-%s-logs-%s.log" % (tmp_path, 'co2', graph_type)
            with open(sensor_co2_log_generate, 'w') as fout:
                for line in fileinput.input(sensor_co2_log_files_combine):
                    fout.write(line)
        else:
            sensor_co2_log_generate = None

        for i in range(0, len(sensor_t_name)):
            lines = seconds/sensor_t_period[i]
            if sensor_t_graph[i]:
                sensor_t_log_final[i] = "%s/sensor-%s-logs-%s-%s-%s.log" %  (
                    tmp_path, 't', graph_type, graph_id, i)
                cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                    i, 't', lines, sensor_t_log_generate, sensor_t_log_final[i])
                logging.debug("[Generate Graph] cmd: %s", cmd)
                os.system(cmd)

        for i in range(0, len(sensor_ht_name)):
            lines = seconds/sensor_ht_period[i]
            if sensor_ht_graph[i]:
                sensor_ht_log_final[i] = "%s/sensor-%s-logs-%s-%s-%s.log" %  (
                    tmp_path, 'ht', graph_type, graph_id, i)
                cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                    i, 'ht', lines, sensor_ht_log_generate, sensor_ht_log_final[i])
                logging.debug("[Generate Graph] cmd: %s", cmd)
                os.system(cmd)

        for i in range(0, len(sensor_co2_name)):
            lines = seconds/sensor_co2_period[i]
            if sensor_co2_graph[i]:
                sensor_co2_log_final[i] = "%s/sensor-%s-logs-%s-%s-%s.log" %  (
                    tmp_path, 'co2', graph_type, graph_id, i)
                cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                    i, 'co2', lines, sensor_co2_log_generate, sensor_co2_log_final[i])
                logging.debug("[Generate Graph] cmd: %s", cmd)
                os.system(cmd)

    elif graph_type == "separate":
        sensor_log_generate = "%s/sensor-%s-logs-%s.log" % (tmp_path, sensor_type, graph_type)
        if sensor_type == "t":
            lines = seconds/sensor_t_period[int(sensor_number)]
            sensor_t_log_final[1] = "%s/sensor-%s-logs-%s-%s-%s.log" % (
                tmp_path, sensor_type, graph_type, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_log_generate, sensor_t_log_final[1])
        if sensor_type == "ht":
            lines = seconds/sensor_ht_period[int(sensor_number)]
            sensor_ht_log_final[1] = "%s/sensor-%s-logs-%s-%s-%s.log" % (
                tmp_path, sensor_type, graph_type, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_log_generate, sensor_ht_log_final[1])
        if sensor_type == "co2":
            lines = seconds/sensor_co2_period[int(sensor_number)]
            sensor_co2_log_final[1] = "%s/sensor-%s-logs-%s-%s-%s.log" % (
                tmp_path, sensor_type, graph_type, graph_id, sensor_number)
            cmd = "/var/www/mycodo/cgi-bin/log-parser.sh %s %s %s %s %s" % (
                sensor_number, sensor_type, lines, sensor_log_generate, sensor_co2_log_final[1])
        logging.debug("[Generate Graph] cmd: %s", cmd)
        os.system(cmd)

    logging.debug("[Generate Graph] Generating Graph...")

    # Write the following output to a file that will be executed with gnuplot
    gnuplot_graph = "%s/plot-%s-%s-%s-%s-%s.gnuplot" % (
        tmp_path, sensor_type, graph_type, graph_span, graph_id, sensor_number)
    plot = open(gnuplot_graph, 'w')

    plot.write('reset\n')
    plot.write('set xdata time\n')
    plot.write('set timefmt \"%Y %m %d %H %M %S\"\n')

    #
    # Graph image size
    #
    if bool(sensor_ht_graph):
        ht_graphs = 2
    else:
        ht_graphs = 0

    num_graphs = sum([bool(sum(sensor_t_graph)), ht_graphs, bool(sum(sensor_co2_graph))]) 
    
    if graph_span == "default":
        graph_width = 1000
        graph_height = 1000
    elif graph_type == "combined":
        graph_width = 1000
        graph_height = (500*num_graphs)
    elif graph_type == "separate":
        if (((sensor_type == "t") and (int(pid_t_temp_relay_high[int(sensor_number)]) != 0 or
            int(pid_t_temp_relay_low[int(sensor_number)]) != 0)) or

            ((sensor_type == "ht") and (int(pid_ht_temp_relay_high[int(sensor_number)]) != 0 or
            int(pid_ht_temp_relay_low[int(sensor_number)]) != 0 or 
            int(pid_ht_hum_relay_high[int(sensor_number)]) != 0 or
            int(pid_ht_hum_relay_low[int(sensor_number)]) != 0)) or

            ((sensor_type == "co2") and (int(pid_co2_relay_high[int(sensor_number)]) != 0 or
            int(pid_co2_relay_low[int(sensor_number)]) != 0))):

            graph_width = 1000
            graph_height = 800
        else:
            graph_width = 1000
            graph_height = 600

    plot.write('set terminal png size ' + str(graph_width) + ',' + str(graph_height) + '\n')


    #
    # Output file
    #
    if graph_span == 'default':
        graph_type = 'default'

    plot.write('set output \"' + image_path + '/graph-' + sensor_type + graph_type + graph_span + '-' + graph_id + '-' + sensor_number + '.png\"\n')


    #
    # Axes ranges
    #
    y1_min = '0'
    y1_max = '35'

    if sensor_type == "co2":
        y1_min = '0'
        y1_max = '5000'

    plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
    plot.write('set format x \"%H:%M\\n%m/%d\"\n')
    plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')


    #
    # Ticks
    #
    if (((graph_type == "combined" and sum(sensor_t_graph)) and sensor_type == "x") or
        sensor_type == "t"):
        plot.write('set ytics 5\n')
        plot.write('set mytics 5\n')

    elif sensor_type == "ht":
        y2_min = '0'
        y2_max = '100'
        plot.write('set y2range [' + y2_min + ':' + y2_max + ']\n')
        plot.write('set ytics 5\n')
        plot.write('set mytics 5\n')
        plot.write('set y2tics 10\n')
        plot.write('set my2tics 5\n')

    elif (((graph_type == "combined" and sum(sensor_co2_graph)) and sensor_type == "x") or
        sensor_type == "co2"):
        plot.write('set ytics 500\n')
        plot.write('set mytics 5\n')
   
    #
    # Styling
    #
    graph_colors = ['#D55E00', '#0072B2', '#009E73',
                    '#7164a3', '#599e86', '#c3ae4f', '#CC79A7', '#957EF9', '#CC8D9C', '#717412', '#0B479B',
                    ]

    plot.write('set tics nomirror\n')
    plot.write('set style line 11 lc rgb \'#808080\' lt 1\n')
    plot.write('set border 3 back ls 11\n')
    plot.write('set style line 12 lc rgb \'#808080\' lt 0 lw 1\n')
    plot.write('set grid xtics ytics back ls 12\n')
    # Horizontal lines: separate temperature, humidity, and dewpoint
    plot.write('set style line 1 lc rgb \'' + graph_colors[0] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 2 lc rgb \'' + graph_colors[1] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 3 lc rgb \'' + graph_colors[2] + '\' pt 0 ps 1 lt 1 lw 2\n')
    # Vertical lines: relays 1 - 8
    plot.write('set style line 4 lc rgb \'' + graph_colors[3] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 5 lc rgb \'' + graph_colors[4] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 6 lc rgb \'' + graph_colors[5] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 7 lc rgb \'' + graph_colors[6] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 8 lc rgb \'' + graph_colors[7] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 9 lc rgb \'' + graph_colors[8] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 10 lc rgb \'' + graph_colors[9] + '\' pt 0 ps 1 lt 1 lw 1\n')
    plot.write('set style line 11 lc rgb \'' + graph_colors[10] + '\' pt 0 ps 1 lt 1 lw 1\n')
    # Horizontal lines: combined temperatures and humidities
    plot.write('set style line 12 lc rgb \'' + graph_colors[3] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 13 lc rgb \'' + graph_colors[4] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 14 lc rgb \'' + graph_colors[5] + '\' pt 0 ps 1 lt 1 lw 2\n')
    plot.write('set style line 15 lc rgb \'' + graph_colors[6] + '\' pt 0 ps 1 lt 1 lw 2\n')
    #plot.write('unset key\n')
    plot.write('set key left top\n')


    #
    # Combined: Generate graph with all temperatures and one graph with all humidities
    #
    if graph_type == "combined" and  graph_span != "default":
        multiplot_num = 1
        plot.write('set multiplot layout ' + str(num_graphs) + ',1\n')

        if sum(sensor_t_graph):
            plot.write('set origin 0.0,%.2f\n' % float(1-((1/float(num_graphs))*float(multiplot_num))))
            multiplot_num += 1
            plot.write('set title \"Combined T Temperatures: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot ')
            for i in range(0, len(sensor_t_name)):
                if sensor_t_graph[i]:
                    plot.write('\"' + sensor_t_log_final[i] + '" u 1:7 index 0 title \"' + sensor_t_name[i] + '\" w lp ls ' + str(i+11) + ' axes x1y1')
                if i != (len(sensor_t_graph) - 1) - sensor_t_graph[::-1].index(1):
                    plot.write(', ')

            plot.write(' \n')

        if sum(sensor_ht_graph):
            plot.write('\nset origin 0.0,%.2f\n' % float(1-((1/float(num_graphs))*float(multiplot_num))))
            multiplot_num += 1
            plot.write('set title \"Combined HT Temperatures: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot ')
            for i in range(0, len(sensor_ht_name)):
                if sensor_ht_graph[i]:
                    plot.write('\"' + sensor_ht_log_final[i] + '" u 1:7 index 0 title \"' + sensor_ht_name[i] + '\" w lp ls ' + str(i+11) + ' axes x1y1')
                if i != (len(sensor_ht_graph) - 1) - sensor_ht_graph[::-1].index(1):
                    plot.write(', ')

            plot.write(' \n')

        if sum(sensor_ht_graph):
            y1_max = '100'
            plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
            plot.write('set ytics 10\n')
            plot.write('set mytics 5\n')
            plot.write('\nset origin 0.0,%.2f\n' % float(1-((1/float(num_graphs))*float(multiplot_num))))
            multiplot_num += 1
            plot.write('set title \"Combined HT Humidities: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot ')
            for i in range(0, len(sensor_ht_name)):
                if sensor_ht_graph[i]:
                    plot.write('\"' + sensor_ht_log_final[i] + '" u 1:8 index 0 title \"' + sensor_ht_name[i] + '\" w lp ls ' + str(i+11) + ' axes x1y1')
                if i != (len(sensor_ht_graph) - 1) - sensor_ht_graph[::-1].index(1):
                    plot.write(', ')

            plot.write(' \n')

        if sum(sensor_co2_graph):
            y1_max = '5000'
            plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
            plot.write('set ytics 500\n')
            plot.write('unset y2tics\n')
            plot.write('set origin 0.0,%.2f\n' % float(1-((1/float(num_graphs))*float(multiplot_num))))
            plot.write('set termopt enhanced\n') 
            plot.write('set title \"Combined CO_2s: ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot ')
            for i in range(0, len(sensor_co2_name)):
                if sensor_co2_graph[i]:
                    plot.write('\"' + sensor_co2_log_final[i] + '" u 1:7 index 0 title \"' + sensor_co2_name[i] + '\" w lp ls ' + str(i+11) + ' axes x1y1')
                if i != (len(sensor_co2_graph) - 1) - sensor_co2_graph[::-1].index(1):
                    plot.write(', ')

            plot.write(' \n')

        plot.write('unset multiplot\n')


    #
    # Separate: Generate a graph with temp, hum, and dew point for each sensor
    #
    if graph_type == "separate" and  graph_span != "default":
        
        if sensor_type == "t":
            if (int(pid_t_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_t_temp_relay_low[int(sensor_number)]) != 0):
                plot.write('set multiplot\n')
                plot.write('set size 0.989,0.6\n')
                plot.write('set origin 0.011,0.4\n')
                plot.write('set format x \"\"\n')
                
            plot.write('set key at graph 0.02, graph 0.98\n')
            plot.write('set title \"Temp Sensor ' + sensor_number + ': ' + sensor_t_name[int(float(sensor_number))] + ' - ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot \"' + sensor_t_log_final[1] + '\" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y1\n')

            if (int(pid_t_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_t_temp_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 1.0,0.4\n')
                plot.write('set origin 0.0,0.0\n')
                plot.write('set key at graph 0.0, graph 0.97\n')
                plot.write('set format x \"%H:%M\\n%m/%d\"\n')
                plot.write('unset y2tics\n')
                y1_min = '-100'
                y1_max = '100'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 25\n')
                plot.write('set mytics 5\n')
                plot.write('set xzeroaxis linetype 1 linecolor rgb \'#000000\' linewidth 1\n')
                plot.write('unset title\n')
                plot.write('plot \"<awk \'$15 == ' + sensor_number + '\' ' + relay_log_generate + '"')

                first = True
                if int(pid_t_temp_relay_high[int(sensor_number)]) != 0:
                    plot.write(' u 1:' + str(pid_t_temp_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_t_temp_relay_high[int(sensor_number)])-1] + '\" w impulses ls 4 axes x1y1')
                    first = False
                
                if int(pid_t_temp_relay_low[int(sensor_number)]) != 0:
                    if not first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_t_temp_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_t_temp_relay_low[int(sensor_number)])-1] + '\" w impulses ls 5 axes x1y1')
                    first = False

                plot.write(' \n')

        if sensor_type == "ht":
            if (int(pid_ht_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_temp_relay_low[int(sensor_number)]) != 0 or 
                int(pid_ht_hum_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_hum_relay_low[int(sensor_number)]) != 0):
                plot.write('set multiplot\n')
                plot.write('set size 0.989,0.6\n')
                plot.write('set origin 0.011,0.4\n')
                plot.write('set format x \"\"\n')
                plot.write('set mytics 5\n')
                plot.write('set my2tics 5\n')

            plot.write('set key at graph 0.02, graph 0.98\n')
            plot.write('set title \"Hum/Temp Sensor ' + sensor_number + ': ' + sensor_ht_name[int(float(sensor_number))] + ' - ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot \"' + sensor_ht_log_final[1] + '\" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y1, \\\n')
            plot.write('\"\" u 1:8 index 0 title \"RH\" w lp ls 2 axes x1y2, \\\n')
            plot.write('\"\" u 1:9 index 0 title \"DP\" w lp ls 3 axes x1y1\n')
            
            if (int(pid_ht_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_temp_relay_low[int(sensor_number)]) != 0 or 
                int(pid_ht_hum_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_hum_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.93,0.4\n')
                plot.write('set origin 0.0,0.0\n')
                plot.write('set format x \"%H:%M\\n%m/%d\"\n')
                plot.write('set key at graph 0.01, graph 0.97\n')
                plot.write('unset y2tics\n')
                y1_min = '-100'
                y1_max = '100'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 25\n')
                plot.write('set mytics 5\n')
                plot.write('set xzeroaxis linetype 1 linecolor rgb \'#000000\' linewidth 1\n')
                plot.write('unset title\n')
                plot.write('plot \"<awk \'$15 == ' + sensor_number + '\' ' + relay_log_generate + '"')
                
                first = 0
                if int(pid_ht_temp_relay_high[int(sensor_number)]) != 0:
                    plot.write(' u 1:' + str(pid_ht_temp_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_temp_relay_high[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')
                    first += 1
                
                if int(pid_ht_temp_relay_low[int(sensor_number)]) != 0:
                    if first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_ht_temp_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_temp_relay_low[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')
                    first += 1
                
                if int(pid_ht_hum_relay_high[int(sensor_number)]) != 0:
                    if first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_ht_hum_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_hum_relay_high[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')
                    first += 1
                
                if int(pid_ht_hum_relay_low[int(sensor_number)]) != 0:
                    if first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_ht_hum_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_hum_relay_low[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')

                plot.write('\n')

        if sensor_type == "co2":
            if (int(pid_co2_relay_high[int(sensor_number)]) != 0 or
                int(pid_co2_relay_low[int(sensor_number)]) != 0):
                plot.write('set multiplot\n')
                plot.write('set size 1.0,0.6\n')
                plot.write('set origin 0.0,0.4\n')
                plot.write('set format x \"\"\n')

            plot.write('set termopt enhanced\n')
            plot.write('set key at graph 0.035, graph 0.98\n')
            plot.write('set title \"CO_2 Sensor ' + sensor_number + ': ' + sensor_co2_name[int(float(sensor_number))] + ' - ' + time_ago + ': ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot \"' + sensor_co2_log_final[1] + '" u 1:7 index 0 title \"CO_2\" w lp ls 1 axes x1y1\n')

            if (int(pid_co2_relay_high[int(sensor_number)]) != 0 or
                int(pid_co2_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.989,0.4\n')
                plot.write('set origin 0.011,0.0\n')
                plot.write('set format x \"%H:%M\\n%m/%d\"\n')
                plot.write('set key at graph 0.01, graph 0.97\n')
                plot.write('unset y2tics\n')
                y1_min = '-100'
                y1_max = '100'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 25\n')
                plot.write('set mytics 5\n')
                plot.write('set xzeroaxis linetype 1 linecolor rgb \'#000000\' linewidth 1\n')
                plot.write('unset title\n')
                plot.write('plot \"<awk \'$15 == ' + sensor_number + '\' ' + relay_log_generate + '"')
                
                first = True
                if int(pid_co2_relay_high[int(sensor_number)]) != 0:
                    plot.write(' u 1:' + str(pid_co2_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_co2_relay_high[int(sensor_number)])-1] + '\" w impulses ls 4 axes x1y1')
                    first = False

                if int(pid_co2_relay_low[int(sensor_number)]) != 0:
                    if not first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_co2_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_co2_relay_low[int(sensor_number)])-1] + '\" w impulses ls 5 axes x1y1\n')

                plot.write(' \n')


    #
    # Default: Generate a graph of the past day and week periods for each sensor
    #
    if graph_span == "default":

        if sensor_type == "t":
            plot.write('set multiplot\n')
            # Top graph - day
            if (int(pid_t_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_t_temp_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.989,0.4\n')
                plot.write('set origin 0.011,0.6\n')
                plot.write('set key at graph 0.025, graph 0.98\n')
                plot.write('set format x ""\n')
            else:
                plot.write('set size 1.0,0.5\n')
                plot.write('set origin 0.0,0.5\n')
                plot.write('set key at graph 0.025, graph 0.98\n')

            plot.write('set title \"Temp Sensor ' + sensor_number + ': ' + sensor_t_name[int(float(sensor_number))] + ' - Past Day: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot \"' + sensor_t_log_final[1] + '" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y1\n')

            if (int(pid_t_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_t_temp_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 1.0,0.2\n')
                plot.write('set origin 0.0,0.4\n')
                plot.write('set key at graph 0.015, graph 0.95\n')
                plot.write('set format x \"%H:%M\\n%m/%d\"\n')
                y1_min = '-100'
                y1_max = '100'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 50\n')
                plot.write('set mytics 2\n')
                plot.write('set xzeroaxis linetype 1 linecolor rgb \'#000000\' linewidth 1\n')
                plot.write('unset title\n')
                plot.write('plot \"<awk \'$15 == ' + sensor_number + '\' ' + relay_log_generate + '"')
                
                first = True
                if int(pid_t_temp_relay_high[int(sensor_number)]) != 0:
                    plot.write(' u 1:' + str(pid_t_temp_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_t_temp_relay_high[int(sensor_number)])-1] + '\" w impulses ls 4 axes x1y1')
                    first = False
                
                if int(pid_t_temp_relay_low[int(sensor_number)]) != 0:
                    if not first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_t_temp_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_t_temp_relay_low[int(sensor_number)])-1] + '\" w impulses ls 5 axes x1y1')
                    first = False

                plot.write(' \n')

            # Bottom graph - week
            d = 7
            time_ago = '1 Week'
            date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
            date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y/%m/%d %H:%M:%S")
            if (int(pid_t_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_t_temp_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.989,0.4\n')
                plot.write('set origin 0.011,0.0\n')
                y1_min = '0'
                y1_max = '35'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 5\n')
                plot.write('set mytics 5\n')
            else:
                plot.write('set size 1.0,0.5\n')
                plot.write('set origin 0.0,0.0\n')

            plot.write('unset xzeroaxis\n')
            plot.write('set title \"Temp Sensor ' + sensor_number + ': ' + sensor_t_name[int(float(sensor_number))] + ' - Past Week: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('set format x \"%a\\n%m/%d\"\n')
            plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
            plot.write('plot \"' + sensor_t_log_final[2] + '" u 1:7 index 0 notitle w lp ls 1 axes x1y1\n')
            plot.write('unset multiplot\n')


        if sensor_type == "ht":
            plot.write('set multiplot\n')
            # Top graph - day
            if (int(pid_ht_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_temp_relay_low[int(sensor_number)]) != 0 or 
                int(pid_ht_hum_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_hum_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.989,0.4\n')
                plot.write('set origin 0.011,0.6\n')
                plot.write('set key at graph 0.025, graph 0.98\n')
                plot.write('set format x ""\n')
            else:
                plot.write('set size 1.0,0.5\n')
                plot.write('set origin 0.0,0.5\n')
                plot.write('set key at graph 0.025, graph 0.98\n')

            plot.write('set title \"Hum/Temp Sensor ' + sensor_number + ': ' + sensor_ht_name[int(float(sensor_number))] + ' - Past Day: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot \"' + sensor_ht_log_final[1] + '" u 1:7 index 0 title \"T\" w lp ls 1 axes x1y1, ')
            plot.write('\"\" u 1:8 index 0 title \"RH\" w lp ls 2 axes x1y2, ')
            plot.write('\"\" u 1:9 index 0 title \"DP\" w lp ls 3 axes x1y1\n')

            if (int(pid_ht_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_temp_relay_low[int(sensor_number)]) != 0 or 
                int(pid_ht_hum_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_hum_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.935,0.2\n')
                plot.write('set origin 0.0,0.4\n')
                plot.write('set key at graph 0.0, graph 0.95\n')
                plot.write('set format x \"%H:%M\\n%m/%d\"\n')
                y1_min = '-100'
                y1_max = '100'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 50\n')
                plot.write('set mytics 2\n')
                plot.write('set xzeroaxis linetype 1 linecolor rgb \'#000000\' linewidth 1\n')
                plot.write('unset y2tics\n')
                plot.write('unset title\n')
                plot.write('plot \"<awk \'$15 == ' + sensor_number + '\' ' + relay_log_generate + '"')

                first = 0
                if int(pid_ht_temp_relay_high[int(sensor_number)]) != 0:
                    plot.write(' u 1:' + str(pid_ht_temp_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_temp_relay_high[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')
                    first += 1
                
                if int(pid_ht_temp_relay_low[int(sensor_number)]) != 0:
                    if first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_ht_temp_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_temp_relay_low[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')
                    first += 1
                
                if int(pid_ht_hum_relay_high[int(sensor_number)]) != 0:
                    if first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_ht_hum_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_hum_relay_high[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')
                    first += 1
                
                if int(pid_ht_hum_relay_low[int(sensor_number)]) != 0:
                    if first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_ht_hum_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_ht_hum_relay_low[int(sensor_number)])-1] + '\" w impulses ls ' + str(first+4) + ' axes x1y1')

                plot.write('\n')

            # Bottom graph - week
            d = 7
            time_ago = '1 Week'
            date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
            date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y/%m/%d %H:%M:%S")
            if (int(pid_ht_temp_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_temp_relay_low[int(sensor_number)]) != 0 or 
                int(pid_ht_hum_relay_high[int(sensor_number)]) != 0 or
                int(pid_ht_hum_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.989,0.4\n')
                plot.write('set origin 0.011,0.0\n')
                y1_min = '0'
                y1_max = '35'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 5\n')
                plot.write('set mytics 5\n')
                plot.write('set y2tics 10\n')
                plot.write('set my2tics 5\n')
            else:
                plot.write('set size 1.0,0.5\n')
                plot.write('set origin 0.0,0.0\n')

            plot.write('unset xzeroaxis\n')
            plot.write('set title \"Hum/Temp Sensor ' + sensor_number + ': ' + sensor_ht_name[int(float(sensor_number))] + ' - Past Week: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('set format x \"%a\\n%m/%d\"\n')
            plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
            plot.write('plot \"' + sensor_ht_log_final[2] + '" u 1:7 index 0 notitle w lp ls 1 axes x1y1, ')
            plot.write('\"\" u 1:8 index 0 notitle w lp ls 2 axes x1y2, ')
            plot.write('\"\" u 1:9 index 0 notitle w lp ls 3 axes x1y1\n')
            plot.write('unset multiplot\n')


        if sensor_type == "co2":
            plot.write('set multiplot\n')
            # Top graph - day
            if (int(pid_co2_relay_high[int(sensor_number)]) != 0 or
                int(pid_co2_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 1.0,0.4\n')
                plot.write('set origin 0.0,0.6\n')
                plot.write('set key at graph 0.035, graph 0.98\n')
                plot.write('set format x ""\n')
            else:
                plot.write('set size 1.0,0.5\n')
                plot.write('set origin 0.0,0.5\n')
                plot.write('set key at graph 0.035, graph 0.98\n')

            plot.write('set termopt enhanced\n')
            plot.write('set title \"CO_2 Sensor ' + sensor_number + ': ' + sensor_co2_name[int(float(sensor_number))] + ' - Past Day: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('plot \"' + sensor_co2_log_final[1] + '" u 1:7 index 0 title \"CO_2\" w lp ls 1 axes x1y1\n')

            if (int(pid_co2_relay_high[int(sensor_number)]) != 0 or
                int(pid_co2_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 0.989,0.2\n')
                plot.write('set origin 0.011,0.4\n')
                plot.write('set key at graph 0.01, graph 0.95\n')
                plot.write('set format x \"%H:%M\\n%m/%d\"\n')
                y1_min = '-100'
                y1_max = '100'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 50\n')
                plot.write('set mytics 2\n')
                plot.write('set xzeroaxis linetype 1 linecolor rgb \'#000000\' linewidth 1\n')
                plot.write('unset title\n')
                plot.write('plot \"<awk \'$15 == ' + sensor_number + '\' ' + relay_log_generate + '"')

                first = True
                if int(pid_co2_relay_high[int(sensor_number)]) != 0:
                    plot.write(' u 1:' + str(pid_co2_relay_high[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_co2_relay_high[int(sensor_number)])-1] + '\" w impulses ls 4 axes x1y1')
                    first = False

                if int(pid_co2_relay_low[int(sensor_number)]) != 0:
                    if not first:
                        plot.write(', \"\"')
                    plot.write(' u 1:' + str(pid_co2_relay_low[int(sensor_number)]+6) + ' index 0 title \"' + relay_name[int(pid_co2_relay_low[int(sensor_number)])-1] + '\" w impulses ls 5 axes x1y1\n')

                plot.write('\n')

            # Bottom graph - week
            d = 7
            time_ago = '1 Week'
            date_ago = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y %m %d %H %M %S")
            date_ago_disp = (datetime.datetime.now() - datetime.timedelta(hours=h, days=d)).strftime("%Y/%m/%d %H:%M:%S")
            if (int(pid_co2_relay_high[int(sensor_number)]) != 0 or
                int(pid_co2_relay_low[int(sensor_number)]) != 0):
                plot.write('set size 1.0,0.4\n')
                plot.write('set origin 0.0,0.0\n')
                y1_min = '0'
                y1_max = '5000'
                plot.write('set yrange [' + y1_min + ':' + y1_max + ']\n')
                plot.write('set ytics 500\n')
                plot.write('set mytics 5\n')
            else:
                plot.write('set size 1.0,0.5\n')
                plot.write('set origin 0.0,0.0\n')

            plot.write('unset xzeroaxis\n')
            plot.write('set title \"CO_2 Sensor ' + sensor_number + ': ' + sensor_co2_name[int(float(sensor_number))] + ' - Past Week: ' + date_ago_disp + ' - ' + date_now_disp + '\"\n')
            plot.write('set format x \"%a\\n%m/%d\"\n')
            plot.write('set xrange [\"' + date_ago + '\":\"' + date_now + '\"]\n')
            plot.write('plot \"' + sensor_co2_log_final[2] + '" u 1:7 index 0 notitle w lp ls 1 axes x1y1\n')
            plot.write('unset multiplot\n')

    plot.close()

    # Generate graph with gnuplot with the above generated command sequence
    if logging.getLogger().isEnabledFor(logging.DEBUG) == False:
        subprocess.call(['gnuplot', gnuplot_graph])

        # Delete all temporary files
        os.remove(gnuplot_graph)
        os.remove(relay_log_generate)
        if graph_span == "default":
            if sensor_type == "t":
                os.remove(sensor_t_log_final[1])
                os.remove(sensor_t_log_final[2])
            if sensor_type == "ht":
                os.remove(sensor_ht_log_final[1])
                os.remove(sensor_ht_log_final[2])
            if sensor_type == "co2":
                os.remove(sensor_co2_log_final[1])
                os.remove(sensor_co2_log_final[2])
        elif graph_type == "combined":
            if sum(sensor_t_graph):
                os.remove(sensor_t_log_generate)
            if sum(sensor_ht_graph):
                os.remove(sensor_ht_log_generate)
            if sum(sensor_co2_graph):
                os.remove(sensor_co2_log_generate)
            for i in range(0, len(sensor_t_name)):
                if sensor_t_graph[i]:
                    os.remove(sensor_t_log_final[i])
            for i in range(0, len(sensor_ht_name)):
                if sensor_ht_graph[i]:
                    os.remove(sensor_ht_log_final[i])
            for i in range(0, len(sensor_co2_name)):
                if sensor_co2_graph[i]:
                    os.remove(sensor_co2_log_final[i])
        elif graph_type == "separate":
            os.remove(sensor_ht_log_final[1])
            os.remove(sensor_co2_log_final[1])
    else:
        gnuplot_log = "%s/plot-%s-%s-%s-%s.log" % (log_path, sensor_type, graph_type, graph_span, sensor_number)
        with open(gnuplot_log, 'ab') as errfile:
            subprocess.call(['gnuplot', gnuplot_graph], stderr=errfile)

    logging.debug("[Generate Graph] Finished")