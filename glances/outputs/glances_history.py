# -*- coding: utf-8 -*-
#
# This file is part of Glances.
#
# Copyright (C) 2014 Nicolargo <nicolas@nicolargo.com>
#
# Glances is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Glances is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""History class."""

# Import system lib
import os

# Import Glances lib
from glances.core.glances_globals import logger

# Import specific lib
try:
    from matplotlib import __version__ as matplotlib_version
    import matplotlib.pyplot as plt
except:
    matplotlib_check = False
    logger.warning(
        'Can not load Matplotlib library. Please install it using "pip install matplotlib"')
else:
    matplotlib_check = True
    logger.info('Load Matplotlib version %s' % matplotlib_version)


class GlancesHistory(object):

    """This class define the object to manage stats history"""

    def __init__(self, output_folder):
        self.output_folder = output_folder

    def get_output_folder(self):
        """Return the output folder where the graph are generated"""
        return self.output_folder

    def graph_enabled(self):
        """Return True if Glances can generaate history graphs"""
        return matplotlib_check

    def reset(self, stats):
        """
        Reset all the history
        """
        if not self.graph_enabled():
            return False
        for p in stats.getAllPlugins():
            h = stats.get_plugin(p).get_stats_history()
            if h is not None:
                stats.get_plugin(p).reset_stats_history()
        return True

    def get_graph_color(self, item):
        """
        Get the item's color
        """
        try:
            ret = item['color']
        except KeyError:
            return '#FFFFFF'
        else:
            return ret

    def get_graph_legend(self, item):
        """
        Get the item's legend
        """
        return item['name']

    def get_graph_yunit(self, item, pre_label=''):
        """
        Get the item's Y unit
        """
        try:
            unit = " (%s)" % item['y_unit']
        except KeyError:
            unit = ''
        if pre_label == '':
            label = ''
        else:
            label = pre_label.split('_')[0]
        return "%s%s" % (label, unit)

    def generate_graph(self, stats):
        """
        Generate graphs from plugins history
        Return the number of output files generated by the function
        """
        if not self.graph_enabled():
            return 0

        index_all = 0
        for p in stats.getAllPlugins():
            h = stats.get_plugin(p).get_stats_history()
            # Data
            if h is None:
                # History (h) not available for plugin (p)
                continue
            # Init graph
            plt.clf()
            index_graph = 0
            handles = []
            labels = []
            for i in stats.get_plugin(p).get_items_history_list():
                if i['name'] in h.keys():
                    # The key exist
                    # Add the curves in the current chart
                    logger.debug("Generate graph: %s %s" % (p, i['name']))
                    index_graph += 1
                    # Labels
                    handles.append(plt.Rectangle((0, 0), 1, 1, fc=self.get_graph_color(i), ec=self.get_graph_color(i), linewidth=2))
                    labels.append(self.get_graph_legend(i))
                    # Legend
                    plt.ylabel(self.get_graph_yunit(i, pre_label=''))
                    # Curves
                    plt.grid(True)
                    plt.plot_date(h['date'], h[i['name']],
                                  fmt='', drawstyle='default', linestyle='-',
                                  color=self.get_graph_color(i),
                                  xdate=True, ydate=False)
                    if index_graph == 1:
                        # Title only on top of the first graph
                        plt.title(p.capitalize())
                else:
                    # The key did not exist
                    # Find if anothers key ends with the key
                    # Ex: key='tx' => 'ethernet_tx'
                    # Add one curve per chart
                    stats_history_filtered = sorted(
                        [key for key in h.keys() if key.endswith('_' + i['name'])])
                    logger.debug("Generate graphs: %s %s" %
                                 (p, stats_history_filtered))
                    if len(stats_history_filtered) > 0:
                        # Create 'n' graph
                        # Each graph iter through the stats
                        plt.clf()
                        index_item = 0
                        for k in stats_history_filtered:
                            index_item += 1
                            plt.subplot(
                                len(stats_history_filtered), 1, index_item)
                            plt.ylabel(self.get_graph_yunit(i, pre_label=k))
                            plt.grid(True)
                            plt.plot_date(h['date'], h[k],
                                          fmt='', drawstyle='default', linestyle='-',
                                          color=self.get_graph_color(i),
                                          xdate=True, ydate=False)
                            if index_item == 1:
                                # Title only on top of the first graph
                                plt.title(p.capitalize() + ' ' + i['name'])
                        # Save the graph to output file
                        fig = plt.gcf()
                        fig.set_size_inches(20, 5 * index_item)
                        plt.xlabel('Date')
                        plt.savefig(
                            os.path.join(self.output_folder, 'glances_%s_%s.png' % (p, i['name'])), dpi=72)
                        index_all += 1

            if index_graph > 0:
                # Save the graph to output file
                fig = plt.gcf()
                fig.set_size_inches(20, 10)
                plt.legend(handles, labels, loc=1, prop={'size': 9})
                plt.xlabel('Date')
                plt.savefig(
                    os.path.join(self.output_folder, 'glances_%s.png' % (p)), dpi=72)
                index_all += 1

            plt.close()

        return index_all
