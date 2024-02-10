import sys
import os
import re
import time
import pyaudio

import PyQt6.QtWidgets as QW
import PyQt6.QtGui as QG
import PyQt6.QtCore as QC
import numpy as np
from scipy.ndimage import gaussian_filter1d


import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class DataTable(QW.QTableWidget):
    # Define the custom signal to include row, column, and the float value
    data_updated = QC.pyqtSignal(int, int, float)

    def __init__(self):
        super().__init__()
        self.setRowCount(20)
        self.setColumnCount(4)
        for col in range(self.columnCount()):
            self.setColumnWidth(col, 100)  # Set the column width to 50 pixels

        self.cellChanged.connect(self.on_cell_changed)
        self.setFixedWidth(400)
        

        headers = ["Blåsfrekvens\n(Hz)", "Massa\n(g)", "höjd\n(mm)", "Plingfrekvens\n(Hz)"]
        self.setHorizontalHeaderLabels(headers)
        # Connect the cellChanged signal to the slot
        self.cellChanged.connect(self.on_cell_changed)
        self.setFixedWidth(500)

    def on_cell_changed(self, row, column):
        # Get the cell item
        cell_item = self.item(row, column)
        if cell_item is not None:
            cell_text = cell_item.text()
            try:
                # Try converting the cell data to float
                cell_value = float(cell_text)
                # Emit the signal if conversion is successful
                self.data_updated.emit(row, column, cell_value)
            except ValueError:
                # If conversion fails, empty the cell
                self.blockSignals(True)  # Block signals to prevent recursive calls
                cell_item.setText('')
                self.blockSignals(False)  # Unblock signals after updating the cell


class DarkFigure(FigureCanvas):
    bgcolor = "black"
    fgcolor = "white"
    def __init__(self,**kwargs):
        plt.rcParams['text.usetex'] = False
        plt.rcParams['text.color'] = self.fgcolor
        # plt.rcParams['text.latex.preamble'] = r"\usepackage{amsmath,wasysym}"
        plt.rcParams['axes.facecolor'] = self.bgcolor
        plt.rcParams['axes.edgecolor'] = self.fgcolor
        plt.rcParams['xtick.color'] = self.fgcolor
        plt.rcParams['ytick.color'] = self.fgcolor
        plt.rcParams['figure.facecolor'] = self.bgcolor
        plt.rcParams['figure.edgecolor'] = self.bgcolor

        self.fig = plt.Figure(facecolor=self.bgcolor)
        self.ax = self.fig.add_axes([0.15,0.15,0.8,0.8])
        self.line, = self.ax.plot([],[],**kwargs)
        super().__init__(self.fig)


class FrequencyReader(DarkFigure):
    def __init__(self):
        super().__init__(color="orange",lw=2,ls="-")
        self.init_microphone()
        self.max_mag = 0
        self.ax.set_yticks([])
        self.peak_freq_text = self.ax.text(0.5, 0.95, "",
                                       transform=self.ax.transAxes, 
                                       ha="center", va="top", 
                                       color=self.fgcolor)
        
        self.peak_values = []
        self.last_time = time.perf_counter()

    def init_microphone(self):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.buffer_size = 11025  # One-fourth of the sampling rate for 0.25-second updates
        self.sampling_rate = 44100  # Sampling rate

        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sampling_rate,
            input=True,
            frames_per_buffer=self.buffer_size,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()

    def audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        fft_result = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(fft_result), d=1/self.sampling_rate)

        mask = (freqs >= 0) & (freqs <= 4000)
        frequencies = freqs[mask]
        magnitudes = np.abs(fft_result[mask])

        self.update_plot(frequencies, magnitudes)
        return (in_data, pyaudio.paContinue)

    def update_plot(self, frequencies, magnitudes):
        smooth_mag = gaussian_filter1d(magnitudes,2)
        self.line.set_data(frequencies, smooth_mag)
        self.ax.set_xlim(0, 4000)  # Set x-axis limit to 0-2kHz
        
        # Calculate the average magnitude
        avg_magnitude = np.mean(smooth_mag)

        # Find the peak magnitude and its corresponding frequency
        peak_magnitude = np.max(smooth_mag)
        if peak_magnitude > 5 * avg_magnitude:
            peak_freq = frequencies[np.argmax(smooth_mag)]
            # Update the peak frequency text
            self.peak_freq_text.set_text(f"Frekvens: {peak_freq:.0f} Hz")
            self.last_time = time.perf_counter()
        else:
            if time.perf_counter()>self.last_time+2:
                self.peak_freq_text.set_text("")

        self.ax.set_ylim(0, peak_magnitude)  # Adjust y-axis limit dynamically
        self.draw()

class DataViewer(FigureCanvas):
    def __init__(self, xlabel, function, x_index, y_index, fit_line):
        super().__init__()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel(xlabel, color="white", fontsize=20)
        self.ax.set_ylabel("Frequency (Hz)", color="white", fontsize=20)
        self.data_points, = self.ax.plot([], [], 'w.', markersize=10)
        self.fit_line = fit_line
        self.function = function
        self.x_index = x_index
        self.y_index = y_index
        self.line_eq_text = None

    def update_plot(self, plot_data):
        # Apply function and extract data
        x_data = eval(self.function, {"x": plot_data[:, self.x_index], "np": np})
        y_data = plot_data[:, self.y_index]
        x_data = x_data[~np.isnan(x_data)]
        y_data = y_data[~np.isnan(y_data)]
        if len(x_data)!=len(y_data):
            return

        # Update plot
        self.data_points.set_data(x_data, y_data)

        # Fit line and display equation if fit_line is True
        if self.fit_line and len(x_data) > 1 and len(y_data) > 1:
            a, b = np.polyfit(x_data, y_data, 1)
            fitted_line = a * x_data + b

            # Add or update fitted line
            if hasattr(self, 'fitted_line_plot'):
                self.fitted_line_plot.set_data(x_data, fitted_line)
            else:
                self.fitted_line_plot, = self.ax.plot(x_data, fitted_line, 'r-', label='Fitted Line')

            # Add or update equation text
            line_eq = f"$f(x) = ax+b$ där $a={a:.2f}$ och $b={b:.2f}$"
            if self.line_eq_text:
                self.line_eq_text.set_text(line_eq)
            else:
                self.line_eq_text = self.ax.text(0.02, 0.98, line_eq, ha="left",va="top",transform=self.ax.transAxes, fontsize=14, color='red')

        # Adjust plot limits and redraw
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)
        self.draw()



class BottleExperiment(QW.QWidget):
    def __init__(self):
        super().__init__()

        # Set the layout for the BottleExperiment widget
        h_layout = QW.QHBoxLayout(self)

        # Create the DataTable and add it to the left side of the layout
        self.data_table = DataTable()
        self.data_table.data_updated.connect(self.updateData)
        h_layout.addWidget(self.data_table)

        # Create the QTabWidget for the right side
        self.tab_widget = QW.QTabWidget()
        self.tab_widget.currentChanged.connect(self.onTabChanged)
        h_layout.addWidget(self.tab_widget)

        # Add the FrequencyReader as the first tab
        self.f_reader = FrequencyReader()
        self.tab_widget.addTab(self.f_reader, "Frequency Reader")

        # Create and add DataViewer instances for the rest of the tabs
        self.data_viewers = [
            DataViewer(xlabel, func, x_index, y_index, fit_line) for xlabel, func, x_index, y_index, fit_line in zip(
                [r"Höjd (mm)", r"1/Höjd (1/mm)", r"Massa (g)", r"1/Massa (1/g)", r"$1/\sqrt{m}$ (1/$\sqrt{\mathrm{g}}$)"],
                ["x", "1/x", "x", "1/x", "1/np.sqrt(x)"],
                [2, 2, 1, 1, 1],
                [0, 0, 3, 3, 3],
                [False,True,False,False,True]
            )
        ]
        for i, viewer in enumerate(self.data_viewers):
            tab_label = f"f_B {i+1}" if i < 2 else f"f_P {i-1}"
            self.tab_widget.addTab(viewer, tab_label)

        # Initialize plot data array
        self.plot_data = np.full((20, 4), np.nan)

    def updateData(self, row, col, value):
        # Update plot data
        self.plot_data[row, col] = value

    def closeEvent(self, event):
        # Close the FrequencyReader stream
        self.f_reader.closeEvent(event)
        super().closeEvent(event)

    def onTabChanged(self, index):
        # Check if the index corresponds to a DataViewer tab
        if index >= 1:  # Assuming index 0 is the FrequencyReader tab
            # Adjust the index to account for the first tab being the FrequencyReader
            data_viewer_index = index - 1

            # Retrieve the corresponding DataViewer widget
            data_viewer = self.data_viewers[data_viewer_index]

            # Update the plot with the new data
            data_viewer.update_plot(self.plot_data)


if __name__=="__main__":
    app = QW.QApplication([])
    with open("style.css",'r') as file:
        app.setStyleSheet(file.read())
    bottle_experiment = BottleExperiment()
    bottle_experiment.show()
    sys.exit(app.exec())