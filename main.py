from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import *
from PyQt5.uic import *

import folium
from folium.plugins import Draw

import os
import sys
import webbrowser

import colorcet as cc
import contextily as cx
import geopandas
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from blackmarble.extract import bm_extract
from blackmarble.raster import bm_raster

file = open('/Users/jannik/Library/CloudStorage/OneDrive-Persönlich/Geoinformatik/Geoprogrammierung II/BLACKMARBLE_TOKEN.txt')
bearer = file.read()
file.close()

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=10, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

def deposit_token():
    global bearer
    bearer, ok = QInputDialog.getText(window, 'Enter NASA Earthdata bearer token',
                                   '''Go to [the NASA LAADS Archive](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5000/VNP46A3/)\n
Click "Login" (bottom on top right); create an account if needed.\n
In Your Account Information Click "Generate Token"''',
                                   QLineEdit.Normal, '')

def draw_region():
    m = folium.Map([47, 7], zoom_start=4)
    Draw(
        export=True,
        filename="region.geojson",
        position="topleft",
        draw_options={"marker": False, 'polyline': False, 'circlemarker': False, 'circle': False, "polygon": {"allowIntersection": False}},
        edit_options={"polygon": {"allowIntersection": False}},
    ).add_to(m)
    
    # Save the map to an HTML file
    map_path = os.path.abspath("region_map.html")
    m.save(map_path)
    
    # Open the map in the default web browser
    webbrowser.open(f'file://{map_path}')

def open_gadm():
    webbrowser.open('https://gadm.org/download_country.html')

def load_geojson():
    load_pfad, filter = QFileDialog.getOpenFileName(window, "Datei öffnen", "", "GeoJSON (*.json) *.geojson *.json.zip)")
    global gdf
    gdf = geopandas.read_file(load_pfad)

def plot_map():
    try:
        bearer
    except NameError:
        QMessageBox.critical(window, "Error", "NASA Earthdata bearer token must be deposited!")
        pass

    selected_date = window.calendarWidget.selectedDate()

    if window.box_mode.currentIndex() == 0:
        mode = 'VNP46A2'
        product_description = 'Gap_Filled_DNB_BRDF-Corrected_NTL'
        title_date = selected_date.toString('dd. MMMM yyyy')
    elif window.box_mode.currentIndex() == 1:
        mode = 'VNP46A3'
        product_description = 'NearNadir_Composite_Snow_Free'
        selected_date = QDate(selected_date.year(), selected_date.month(), 1)
        title_date = selected_date.toString('MMMM yyyy')
    elif window.box_mode.currentIndex() == 2:
        mode = 'VNP46A4'
        product_description = 'NearNadir_Composite_Snow_Free'
        selected_date = QDate(selected_date.year(), 1, 1)
        title_date = selected_date.toString('yyyy')

    date_string = selected_date.toString('yyyy-MM-dd')
    #date_string = selected_date.toString('2023-01-01')
    
    r_plot = bm_raster(gdf, product_id=mode, date_range=date_string, bearer=bearer, file_directory=("ntl.tif"))
    
    # Clear the previous plot
    sc.ax.clear()
    
    r_plot[product_description].sel(time=date_string).plot.pcolormesh(
        ax=sc.ax,
        cmap=cc.cm.bmy,
        robust=True,
    )
    cx.add_basemap(sc.ax, crs=gdf.crs.to_string())

    sc.ax.text(
        0,
        -0.1,
        f"Source: NASA Black Marble {mode}",
        ha="left",
        va="center",
        transform=sc.ax.transAxes,
        fontsize=10,
        color="black",
        weight="normal",
    )
    sc.ax.set_title(f"NTL Radiance in {title_date}", fontsize=20)

    # Refresh the canvas
    sc.draw()

def plot_on_map():
    pass

app = QApplication(sys.argv)

window = loadUi('BlackMarbleViewer.ui')
window.setWindowTitle("Black Marble Viewer")

# Create a canvas and add it to the plot_widget
sc = MplCanvas(window.plot_widget, width=5, height=10, dpi=100)
layout = QHBoxLayout()
layout.addWidget(sc)
window.plot_widget.setLayout(layout)

window.show()

window.button_token.clicked.connect(deposit_token)
window.button_draw.clicked.connect(draw_region)
window.button_gadm.clicked.connect(open_gadm)
window.button_load.clicked.connect(load_geojson)

window.box_mode.addItems(["Day", "Month", "Year"])

window.button_plot.clicked.connect(plot_map)
window.button_map.clicked.connect(plot_on_map)

app.exec()