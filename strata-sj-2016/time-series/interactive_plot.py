
import matplotlib.pyplot as _plt
from matplotlib.widgets import Button
_plt.style.use('ggplot')


## Plot an interactive version.
class LineDrawer(object):
    def __init__(self, scores, guide_lines, threshold_lines):
        self.guide_lines = guide_lines
        self.threshold_lines = threshold_lines
        self.figure = self.guide_lines[0].figure
        self.scores = scores

        self.anoms = self.scores[:0]
        self.anom_plot = self.figure.axes[0].plot(self.anoms['time'],
                                                  self.anoms['count'],
                                                  color='red', lw=0, marker='o',
                                                  markersize=10,
                                                  alpha=0.7)

    def connect(self):
        """Connect to the event."""
        self.cid_press = self.figure.canvas.mpl_connect('button_press_event',
                                                        self.on_press)

    def disconnect(self):
        """Disconnect the event bindings."""
        self.figure.canvas.mpl_disconnect(self.cid_press)

    def on_press(self, event):
        """Store the location data when the mouse button is pressed."""

        if event.inaxes == self.figure.axes[0]:
            self.threshold_lines[0].set_ydata((event.ydata, event.ydata))
            self.threshold_lines[1].set_ydata((0., 0.))
            self.threshold_lines[2].set_ydata((0., 0.))

            col = self.scores.value_col_names[0]

        elif event.inaxes == self.figure.axes[1]:
            self.threshold_lines[1].set_ydata((event.ydata, event.ydata))
            self.threshold_lines[0].set_ydata((0., 0.))
            self.threshold_lines[2].set_ydata((0., 0.))

            col = self.scores.value_col_names[1]

        elif event.inaxes == self.figure.axes[2]:
            self.threshold_lines[2].set_ydata((event.ydata, event.ydata))
            self.threshold_lines[0].set_ydata((0., 0.))
            self.threshold_lines[1].set_ydata((0., 0.))

            col = self.scores.value_col_names[2]

        else:
            return

        ## Print the anomalies from the selected horizontal threshold.
        mask = self.scores[col] >= event.ydata
        self.anoms = self.scores[mask]

        ## Replot the anomalies on the first axes.
        self.anom_plot[0].set_data((list(self.anoms['time']),
                                    list(self.anoms['count'])))

        ## Re-position the vertical guide lines.
        for line in self.guide_lines:
            line.set_xdata((event.xdata, event.xdata))

        ## Re-draw the whole figure.
        self.figure.canvas.draw()

