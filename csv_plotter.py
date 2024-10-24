import sys
import os
import random
import pandas as pd
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QFileDialog, QWidget, QLabel, QListWidget, QSpinBox, QHBoxLayout,
    QInputDialog, QLineEdit, QListWidgetItem, QComboBox
)

class DataVisualizer(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('CSV Data Visualizer')
        self.setGeometry(100, 100, 1200, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.status_label = QLabel("Load a file to begin - if loading multiple files, ensure column headers are consistent")
        self.layout.addWidget(self.status_label)

        self.load_button = QPushButton('Load CSV files')
        self.load_button.clicked.connect(self.load_csv)
        self.layout.addWidget(self.load_button)

        self.independent_variable_button = QPushButton('Assign x-axis variable')
        self.independent_variable_button.clicked.connect(self.assign_independent_variable)
        self.layout.addWidget(self.independent_variable_button)

        self.clear_independent_variable_button = QPushButton('Clear x-axis variable')
        self.clear_independent_variable_button.clicked.connect(self.clear_independent_variable)
        self.layout.addWidget(self.clear_independent_variable_button)

        self.reset_axes_button = QPushButton('Reset graph axes')
        self.reset_axes_button.clicked.connect(self.reset_plot_axes)
        self.layout.addWidget(self.reset_axes_button)

        self.clear_button = QPushButton('Clear all selected variables')
        self.clear_button.clicked.connect(self.clear_plot)
        self.layout.addWidget(self.clear_button)

        self.calculate_average_button = QPushButton('Calculate average')
        self.calculate_average_button.clicked.connect(self.calculate_average_over_range)
        self.layout.addWidget(self.calculate_average_button)
        
        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QListWidget.MultiSelection)
        self.column_list.itemSelectionChanged.connect(self.plot_selected_columns)
        self.layout.addWidget(self.column_list)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search columns:")
        search_layout.addWidget(search_label)
        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self.filter_columns)
        search_layout.addWidget(self.search_bar)

        shift_layout = QHBoxLayout()
        self.shift_column_dropdown = QComboBox()
        shift_layout.addWidget(QLabel("Select column data to shift:"))
        shift_layout.addWidget(self.shift_column_dropdown)

        arrow_layout = QHBoxLayout()
        self.left_button = QPushButton('<<')
        self.left_button.clicked.connect(self.shift_left)
        arrow_layout.addWidget(self.left_button)
        self.right_button = QPushButton('>>')
        self.right_button.clicked.connect(self.shift_right)
        arrow_layout.addWidget(self.right_button)

        percent_arrow_layout = QHBoxLayout()
        self.percent_left_button = QPushButton('- 0.5%')
        self.percent_left_button.clicked.connect(self.percent_shift_left)
        percent_arrow_layout.addWidget(self.percent_left_button)
        self.percent_right_button = QPushButton('+ 0.5%')
        self.percent_right_button.clicked.connect(self.percent_shift_right)
        percent_arrow_layout.addWidget(self.percent_right_button)

        self.layout.addLayout(arrow_layout)
        self.layout.addLayout(percent_arrow_layout)
        self.layout.addLayout(search_layout)
        self.layout.addLayout(shift_layout)
 
        self.data = None
        self.legend = None
        self.selected_file_index = None
        self.shifts = {}
        self.percent_shifts = {}
        self.data_frames = []

    def load_csv(self):
        self.independent_variable = None
        self.file_paths, _ = QFileDialog.getOpenFileNames(self, "Open CSV files", "", "CSV files (*.csv)")
        if self.file_paths:
            skip_rows, _ = QInputDialog.getDouble(self, "Input window", "Enter number of header rows to skip:")
            self.data_frames = []
            for file_path in self.file_paths:
                try:
                    data = pd.read_csv(file_path, skiprows=int(skip_rows), encoding='latin1')
                    self.data_frames.append(data)
                except pd.errors.EmptyDataError:
                    self.status_label.setText("One of the selected files is empty")
                except pd.errors.ParserError:
                    self.status_label.setText("Error parsing one of the CSV files (check number of headers rows to skip)")
                except Exception as e:
                    self.status_label.setText(f"Error loading one of the CSV files (check number of header rows to skip): {str(e)}")
            if self.data_frames:
                self.populate_column_list()
                self.populate_shift_column_dropdown()
                self.status_label.setText(f"CSV files loaded successfully: {', '.join(self.file_paths)}")
                self.select_shift_file()
        else:
            self.status_label.setText("No files loaded")
  
    def populate_column_list(self):
        self.column_list.clear()
        self.column_list.addItem("Entire dataset")
        self.column_list.addItems(self.data_frames[0].columns)

    def populate_shift_column_dropdown(self):
        self.shift_column_dropdown.clear()
        self.shift_column_dropdown.addItem("All columns")
        self.shift_column_dropdown.addItems(self.data_frames[0].columns)

    def filter_columns(self):
        if hasattr(self.data_frames[0], 'columns'):
            filtered_columns = [col for col in sorted(self.data_frames[0].columns) if self.search_bar.text().lower() in col.lower()]
            if filtered_columns:
                current_selection = [item.text() for item in self.column_list.selectedItems()]
                current_selection_set = set(current_selection).intersection(filtered_columns)
                self.column_list.clear()
                for column in filtered_columns:
                    item = QListWidgetItem(column)
                    if column in current_selection_set:
                        item.setSelected(True)
                    self.column_list.addItem(item)

    def select_shift_file(self):
        self.file_names = [os.path.basename(file_path) for file_path in self.file_paths]
        if len(self.file_names) == 1:
            self.selected_file_index = 0
        else:
            selected_file, ok = QInputDialog.getItem(self, "Input window", "Choose a file to apply horizontal (x-axis) shifts to:", self.file_names, 0, False)
            if ok and selected_file:
                self.selected_file_index = self.file_names.index(selected_file)
                self.status_label.setText(f"Selected file for shifts: {selected_file}")
            else:
                self.status_label.setText("No file selected for shifts")

    def assign_independent_variable(self):
        self.clear_plot()
        if isinstance(self.data_frames[0], pd.DataFrame):
            columns = self.data_frames[0].columns.tolist()
            selected_column, ok = QInputDialog.getItem(self, "Input window", "Choose a column:", columns, 0, False)
            if ok and selected_column:
                self.independent_variable = selected_column
                self.status_label.setText(f"Assigned as x-axis variable: {selected_column}")
            else:
                self.status_label.setText("No column selected")
        else:
            self.status_label.setText("No data loaded")

    def clear_independent_variable(self):
        self.independent_variable = None
        self.status_label.setText("Assigned x-axis variable cleared")

    def plot_selected_columns(self):
        selected_items = self.column_list.selectedItems() 
        if not selected_items:
            return    
        elif any(item.text() == "Entire dataset" for item in selected_items):
            self.plot_data(self.data_frames)
            self.status_label.setText("Plotting entire dataset")
        else:
            selected_columns = [item.text() for item in selected_items]
            self.plot_data(self.data_frames, selected_columns)
            self.status_label.setText(f"Plotting columns: {', '.join(selected_columns)}")

    def filter_column_data(self, dataframe, column):
        filtered_data = dataframe[pd.to_numeric(dataframe[column], errors='coerce').notnull()].copy()
        filtered_data[column] = filtered_data[column].astype(float)
        if self.independent_variable:  
            filtered_data[self.independent_variable] = filtered_data[self.independent_variable].astype(float)

        return filtered_data

    def calculate_average_over_range(self):
        selected_items = self.column_list.selectedItems()
        if len(self.data_frames) == 1:
            dataframe = self.data_frames[0]
            if self.independent_variable:
                if not selected_items:
                    self.status_label.setText("No columns selected for average calculation")
                    return
                selected_columns = [item.text() for item in selected_items]
                lower_limit, ok1 = QInputDialog.getDouble(self, "Input window", "Enter lower x-axis limit:")
                if not ok1:
                    return
                upper_limit, ok2 = QInputDialog.getDouble(self, "Input window", "Enter upper x-axis limit:")
                if not ok2:
                    return
                if lower_limit >= upper_limit:
                    self.status_label.setText("Lower limit must be less than upper limit")
                    return
                average_values = []
                for col in selected_columns:
                    filtered_data = self.filter_column_data(dataframe, col)
                    range_data = filtered_data[(self.percent_shifts.get(col, 1) * (filtered_data[self.independent_variable] + self.shifts.get(col, 0)) >= lower_limit)
                                 & (self.percent_shifts.get(col, 1) * (filtered_data[self.independent_variable] + self.shifts.get(col, 0)) <= upper_limit)]
                    if range_data.empty:
                        self.status_label.setText(f"No data in the specified range for variable: {col}")
                        return 
                    average_value = range_data[col].mean()
                    average_values.append(f'{col} average: {average_value:.5f}')
                self.status_label.setText(', '.join(average_values))
            else:
                self.status_label.setText("Assign an x-axis variable before attempting to calculate average")
        else:
             self.status_label.setText("Function only available when one file is loaded")

    def plot_data(self, dataframes, columns=None):
        self.plot_widget.clear()
        if self.legend:
            self.legend.clear()
        self.legend = pg.LegendItem((100, 60), offset=(70, 30))
        self.legend.setParentItem(self.plot_widget.graphicsItem())
        self.linestyles = [QtCore.Qt.SolidLine, QtCore.Qt.DotLine, QtCore.Qt.DashLine]
        for idx, data in enumerate(dataframes):
            if self.independent_variable:
                if columns:
                    for i, col in enumerate(columns):
                        filtered_data = self.filter_column_data(data, col)
                        shift = self.shifts.get(col, 0)
                        percent_shift = self.percent_shifts.get(col, 1)
                        if idx == self.selected_file_index:
                            plot_item = pg.PlotDataItem(percent_shift * (filtered_data[self.independent_variable].to_numpy() + shift), filtered_data[col].to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(columns)), style=self.linestyles[idx]))
                        else:
                            plot_item = pg.PlotDataItem(filtered_data[self.independent_variable].to_numpy(), filtered_data[col].to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(columns)), style=self.linestyles[idx]))
                        self.plot_widget.addItem(plot_item)
                        self.legend.addItem(plot_item, f'{col} ({self.file_names[idx]})')  
                else:
                    for i, col in enumerate(data.columns):
                        filtered_data = self.filter_column_data(data, col)
                        shift = self.shifts.get(col, 0)
                        percent_shift = self.percent_shifts.get(col, 1) 
                        if idx == self.selected_file_index:
                            plot_item = pg.PlotDataItem(percent_shift * (filtered_data[self.independent_variable].to_numpy() + shift), filtered_data.to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(data.columns)), style=self.linestyles[idx]))
                        else:
                            plot_item = pg.PlotDataItem(filtered_data[self.independent_variable].to_numpy(), filtered_data.to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(data.columns)), style=self.linestyles[idx]))
                        self.plot_widget.addItem(plot_item)
                        self.legend.addItem(plot_item, f'{col} ({self.file_names[idx]})')
                self.plot_widget.setLabel('bottom', self.independent_variable)
                self.plot_widget.setLabel('left', 'y-axis')
                self.plot_widget.showGrid(True, True)
            else:
                if columns:
                    for i, col in enumerate(columns):
                        filtered_data = self.filter_column_data(data, col)
                        shift = self.shifts.get(col, 0)
                        percent_shift = self.percent_shifts.get(col, 1)
                        if idx == self.selected_file_index:
                            plot_item = pg.PlotDataItem(percent_shift * (filtered_data.index.to_numpy() + shift), filtered_data[col].to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(columns)), style=self.linestyles[idx]))
                        else:
                            plot_item = pg.PlotDataItem(filtered_data.index.to_numpy(), filtered_data[col].to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(columns)), style=self.linestyles[idx]))
                        self.plot_widget.addItem(plot_item)
                        self.legend.addItem(plot_item, f'{col} ({self.file_names[idx]})')  
                else:
                    for i, col in enumerate(data.columns):
                        filtered_data = self.filter_column_data(data, col)
                        shift = self.shifts.get(col, 0)
                        percent_shift = self.percent_shifts.get(col, 1)
                        if idx == self.selected_file_index:
                            plot_item = pg.PlotDataItem(percent_shift * (filtered_data.index.to_numpy() + shift), filtered_data[col].to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(data.columns)), style=self.linestyles[idx]))
                        else:
                            plot_item = pg.PlotDataItem(filtered_data.index.to_numpy(), filtered_data[col].to_numpy(),
                                                        pen=pg.mkPen(color=(i, len(data.columns)), style=self.linestyles[idx]))
                        self.plot_widget.addItem(plot_item)
                        self.legend.addItem(plot_item, f'{col} ({self.file_names[idx]})')
                self.plot_widget.setLabel('bottom', 'x-axis (arb. units)')
                self.plot_widget.setLabel('left', 'y-axis')
                self.plot_widget.showGrid(True, True)

    def clear_plot(self):
        self.shifts = {}
        self.percent_shifts = {}
        self.plot_widget.clear()
        self.column_list.clearSelection()
        self.plot_widget.scene().removeItem(self.legend)
        self.status_label.setText("All selected variables cleared")

    def reset_plot_axes(self):
        self.plot_widget.getPlotItem().enableAutoRange()
        self.status_label.setText("Graph axes reset")

    def shift_left(self):
        selected_column = self.shift_column_dropdown.currentText()
        if selected_column == "All columns" and self.selected_file_index is not None:
            for column in self.data_frames[self.selected_file_index]:
                self.shifts[column] = self.shifts.get(column, 0) - 50
            self.plot_selected_columns()
        elif selected_column and self.selected_file_index is not None:
            self.shifts[selected_column] = self.shifts.get(selected_column, 0) - 50
            self.plot_selected_columns()
        else:
            self.status_label.setText("Select a column to shift")
      
    def shift_right(self):
        selected_column = self.shift_column_dropdown.currentText()
        if selected_column == "All columns" and self.selected_file_index is not None:
            for column in self.data_frames[self.selected_file_index]:
                self.shifts[column] = self.shifts.get(column, 0) + 50
            self.plot_selected_columns()
        elif selected_column and self.selected_file_index is not None:
            self.shifts[selected_column] = self.shifts.get(selected_column, 0) + 50
            self.plot_selected_columns()
        else:
            self.status_label.setText("Select a column to shift")

    def percent_shift_left(self):
        selected_column = self.shift_column_dropdown.currentText()
        if selected_column == "All columns" and self.selected_file_index is not None:
            for column in self.data_frames[self.selected_file_index]:
                self.percent_shifts[column] = self.percent_shifts.get(column, 1) - 0.005
            self.plot_selected_columns()
            self.status_label.setText(f"Current shift: {np.around((self.percent_shifts[column] - 1) * 100, 1)}%")
        elif selected_column and self.selected_file_index is not None:
            self.percent_shifts[selected_column] = self.percent_shifts.get(selected_column, 1) - 0.005
            self.plot_selected_columns()
            self.status_label.setText(f"Current shift: {np.around((self.percent_shifts[column] - 1) * 100, 1)}%")
        else:
            self.status_label.setText("Select a column to shift")

    def percent_shift_right(self):
        selected_column = self.shift_column_dropdown.currentText()
        if selected_column == "All columns" and self.selected_file_index is not None:
            for column in self.data_frames[self.selected_file_index]:
                self.percent_shifts[column] = self.percent_shifts.get(column, 1) + 0.005
            self.plot_selected_columns()
            self.status_label.setText(f"Current shift: {np.around((self.percent_shifts[column] - 1) * 100, 1)}%")
        elif selected_column and self.selected_file_index is not None:
            self.percent_shifts[selected_column] = self.percent_shifts.get(selected_column, 1) + 0.005
            self.plot_selected_columns()
            self.status_label.setText(f"Current shift: {np.around((self.percent_shifts[column] - 1) * 100, 1)}%")
        else:
            self.status_label.setText("Select a column to shift")
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataVisualizer()
    window.show()
    sys.exit(app.exec_())
