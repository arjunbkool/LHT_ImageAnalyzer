# -*- coding: utf-8 -*-
"""
Created on Thu Feb  20 12:41:16 2019

@author: U724965
"""

import cv2
import os
from functools import partial
from shutil import copyfile, rmtree

import numpy as np
import xlrd
import xlsxwriter
from PIL import Image, ImageEnhance, ImageStat
from PIL.ImageQt import ImageQt

from PyQt5.QtCore import QEvent, Qt, QRectF, QRect, pyqtSignal, pyqtSlot, QPointF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QPalette
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QFrame, \
    QGraphicsView, QApplication, QGraphicsEllipseItem, QSlider, QRadioButton, QLabel, QDialog, QVBoxLayout, QMenu, \
    QAction, QCheckBox

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import Ui_ImageExposure
import Ui_ImagePixelSelection
import common

show_message = common.show_message
view_file_location = common.view_file_location
view_image = common.view_image
del_folder = common.del_folder
crop_img = common.crop_img
NumpyToQImage = common.NumpyToQImage


# The class to do the Image Enhancements (Third Window)
class ImageExposure(Ui_ImageExposure.Ui_MainWindow, QMainWindow):
    closed = pyqtSignal()
    kernel = pyqtSignal(int)
    image_update = pyqtSignal(int)

    def __init__(self, parent=None):
        super(ImageExposure, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("LHT Image Analyzer - Version 1.0")

        # No initial knowledge of our directories
        self.destination_directory = None
        self.source_directory = None
        self.curr_dir_source = None
        self.curr_dir_destination = None
        self.newpathdir = None
        self.finishpathdir = None

        self.lcdNumber.display(str(0))  # lcd Number to see the value of enhancement applied
        self.img_files = None  # The locations of all images
        self.length = 0  # To store the number of image files
        self.set = 0  # Which set of images are dispplayed in the current window
        self.refresh = True  # To convey that it is refresh of already loaded images
        self.images = []  # The images are stored as PIL Images for easy enhancement functions
        self.id = 0  # The current ID of the image in focus
        self.checkbox_id = None  # Which of the check box is selected information (selective enhancement)
        self.kernel_value = None  # This is the value of the average brightness inside the kernel, selected enhancement
        self.max_count_hist = []  # The maximum Y value of each histogram (to make the major graph appear centric)

        # Show images
        self.pushButton_1.clicked.connect(partial(self.click1, 0))
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)

        # Previous and next set
        self.pushButton_2.clicked.connect(self.click2)
        self.pushButton_3.clicked.connect(self.click3)

        # Auto brightness + contrast button
        self.auto_applied = False
        self.label_7.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label_7.customContextMenuRequested.connect(self.on_context_menu)
        self.label_7.setEnabled(False)
        self.label_7.installEventFilter(self)

        # Radio Buttons + individual event filter
        self.radioButton_1.installEventFilter(self)
        self.radioButton_2.installEventFilter(self)
        self.radioButton_3.installEventFilter(self)
        self.radioButton_1.setChecked(True)

        # Labels
        self.labels = [self.label_1, self.label_2, self.label_3,
                       self.label_4, self.label_5, self.label_6]

        for label in self.labels:
            label.installEventFilter(self)
            label.setContextMenuPolicy(Qt.CustomContextMenu)
            label.customContextMenuRequested.connect(self.on_context_menu)

        # create context menu for labels
        self.popMenu1 = QMenu(self)
        self.action00 = QAction("Reload Original Image")
        self.popMenu1.addAction(self.action00)
        self.action01 = QAction("Show Histogram")
        self.popMenu1.addAction(self.action01)
        self.action02 = QAction("Show Image")
        self.popMenu1.addAction(self.action02)
        self.action00.triggered.connect(self.show_original_image)
        self.action01.triggered.connect(self.show_hist_window)
        self.action02.triggered.connect(self.show_pix_selection_window)

        # create context menu for "press mouse button to select" button
        self.popMenu2 = QMenu(self)
        self.action1 = QAction("Histogram Equalisation (Brightness + Contrast)")
        self.action2 = QAction("Resize Equalisation (Size Interpolated Brightness)")
        self.action3 = QAction("Absolute Equalisation (Mean Brightness)")
        self.action4 = QAction("Selective Equalisation (Pixel Point/Kernel)")
        self.popMenu2.addAction(self.action1)
        self.popMenu2.addAction(self.action2)
        self.popMenu2.addAction(self.action3)
        self.popMenu2.addAction(self.action4)
        self.button_ID = 0
        self.action1.triggered.connect(partial(self.Auto_Brightness_Text, 1))
        self.action2.triggered.connect(partial(self.Auto_Brightness_Text, 2))
        self.action3.triggered.connect(partial(self.Auto_Brightness_Text, 3))
        self.action4.triggered.connect(partial(self.Auto_Brightness_Text, 4))

        # Histogram Window
        self.hist_window_on = False
        self.hist_window_1 = Histogram(self)
        self.hist_window_2 = Histogram(self)
        self.hist_window_3 = Histogram(self)
        self.hist_window_4 = Histogram(self)
        self.hist_window_5 = Histogram(self)
        self.hist_window_6 = Histogram(self)
        self.hist_windows = [self.hist_window_1, self.hist_window_2, self.hist_window_3,
                             self.hist_window_4, self.hist_window_5, self.hist_window_6]
        for hist_window in self.hist_windows:
            hist_window.closed.connect(self.hist_window_off)

        # Pixel Selection Window
        self.pixel_window_on = False
        self.pixel_window_1 = ImagePixel(self)
        self.pixel_window_2 = ImagePixel(self)
        self.pixel_window_3 = ImagePixel(self)
        self.pixel_window_4 = ImagePixel(self)
        self.pixel_window_5 = ImagePixel(self)
        self.pixel_window_6 = ImagePixel(self)
        self.pixel_windows = [self.pixel_window_1, self.pixel_window_2, self.pixel_window_3,
                              self.pixel_window_4, self.pixel_window_5, self.pixel_window_6]
        for pixel_window in self.pixel_windows:
            pixel_window.kernel.connect(self.set_kernel_value)
            pixel_window.image_update.connect(self.set_selective_image)

        # Vertical Slider
        self.sliders = [self.verticalSlider_1, self.verticalSlider_2, self.verticalSlider_3,
                        self.verticalSlider_4, self.verticalSlider_5, self.verticalSlider_6]
        for slider in self.sliders:
            slider.installEventFilter(self)
            i = self.sliders.index(slider)
            slider.sliderReleased.connect(partial(self.enhancement, i))

        # Checkbox for Reference for Selective Equalisation (only active when the option is selected)
        self.checkBoxes = [self.checkBox_1, self.checkBox_2, self.checkBox_3,
                           self.checkBox_4, self.checkBox_5, self.checkBox_6]

        # The radio buttons (round button)
        self.Radios = [self.radioButton_4, self.radioButton_5, self.radioButton_6,
                       self.radioButton_7, self.radioButton_8, self.radioButton_9]

        for i in range(6):
            self.Radios[i].setVisible(False)
            self.checkBoxes[i].setVisible(False)
            self.checkBoxes[i].installEventFilter(self)

    # Restore images button
    def click1(self, change=0):
        for i in range(6):
            self.Radios[i].setVisible(False)
            self.checkBoxes[i].setVisible(False)

        self.newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory),
                                       "Enhanced")

        self.label_7.setEnabled(True)
        self.lcdNumber.display(str(0))

        if change == 0:
            if os.path.exists(self.newpathdir):
                rmtree(self.newpathdir)
            else:
                os.makedirs(self.newpathdir)
            self.refresh = True
            self.auto_applied = False

            with open("Img_files_cropped.txt") as file:
                self.img_files = file.read().splitlines()
            self.length = len(self.img_files)
            file.close()

        if self.refresh is True:
            self.images = [[] for x in range(self.length)]
            for i in range(self.length):
                self.images[i] = Image.open(self.img_files[i])

        if change is 0:
            self.max_count_hist = []
            for i in range(self.length):
                im = self.images[i].histogram()
                im_max = max(im)
                self.max_count_hist.append(im_max)

        if self.hist_window_on is True and change is 0:
            self.hist_window_1.clear_plot()
            self.hist_window_2.clear_plot()
            self.hist_window_3.clear_plot()
            self.hist_window_4.clear_plot()
            self.hist_window_5.clear_plot()
            self.hist_window_6.clear_plot()

        if self.hist_window_on is True and change is 1:
            for i in range(6):
                m = 6 * (self.set - 1) + i
                if m < self.length:
                    im = self.images[m].histogram()
                    self.hist_windows[i].mid_y = self.max_count_hist[m]
                    self.hist_windows[i].plot(im, i + 1)

        self.set = 1
        self.pushButton_3.setEnabled(False)
        self.pushButton_2.setEnabled(True) if self.length > 6 else self.pushButton_2.setEnabled(False)

        n = 6 if self.length > 6 else self.length

        for i, label, pixel_window, filename in zip(range(n), self.labels, self.pixel_windows, self.img_files):

            if self.refresh is True:
                image = QImage(filename)
            else:
                image_array = np.asarray(self.images[i].convert('L'))
                image = NumpyToQImage(image_array)

            image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)
            pixmap = QPixmap(image)
            w = int(label.width() - 4.0)
            h = int(label.height() - 4.0)
            smaller_pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            label.setPixmap(smaller_pixmap)
            label.setScaledContents(True)



            pixel_window.label = i
            pixel_window.setImage(self.images[i])

    # Next set button
    def click2(self):

        if self.checkbox_id is not None:
            for i in range(6):
                self.checkBoxes[i].setVisible(False)

        self.pushButton_3.setEnabled(True)
        self.set = self.set + 1
        n = 6 if (self.length - self.set * 6) > 6 else (self.length - (self.set - 1) * 6)

        if self.hist_window_on is True:
            self.hist_window_1.clear_plot()
            self.hist_window_2.clear_plot()
            self.hist_window_3.clear_plot()
            self.hist_window_4.clear_plot()
            self.hist_window_5.clear_plot()
            self.hist_window_6.clear_plot()

        for i, label in zip(range(n), self.labels):
            k = (self.set - 1) * 6 + i

            if k is self.checkbox_id:
                self.checkBoxes[i].setVisible(True)

            if self.refresh is True:
                image = QImage(self.img_files[k])
            else:
                image_array = np.asarray(self.images[k].convert('L'))
                image = NumpyToQImage(image_array)

            image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)
            pixmap = QPixmap(image)
            w = int(label.width() - 4.0)
            h = int(label.height() - 4.0)
            smaller_pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            label.setPixmap(smaller_pixmap)
            label.setScaledContents(True)

        if n < 6:
            self.pushButton_2.setEnabled(False)
            displays = [False, False, False, False, False, False]
            displays[:n] = [True] * n

            for i, label, display in zip(range(6), self.labels, displays):
                if not display:
                    label.clear()

    # Previous set button
    def click3(self):

        if self.checkbox_id is not None:
            for i in range(6):
                self.checkBoxes[i].setVisible(False)

        if self.set > 1:
            self.pushButton_2.setEnabled(True)

        self.set = self.set - 1
        if self.set == 1:
            self.pushButton_3.setEnabled(False)

        if self.hist_window_on is True:
            self.hist_window_1.clear_plot()
            self.hist_window_2.clear_plot()
            self.hist_window_3.clear_plot()
            self.hist_window_4.clear_plot()
            self.hist_window_5.clear_plot()
            self.hist_window_6.clear_plot()

        if self.set > 0:

            for i, label in zip(range(6), self.labels):
                k = (self.set - 1) * 6 + i

                if k is self.checkbox_id:
                    self.checkBoxes[i].setVisible(True)

                if self.refresh is True:
                    image = QImage(self.img_files[k])
                else:
                    image_array = np.asarray(self.images[k].convert('L'))
                    image = NumpyToQImage(image_array)

                image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)

                pixmap = QPixmap(image)
                w = int(label.width() - 4.0)
                h = int(label.height() - 4.0)
                smaller_pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
                label.setPixmap(smaller_pixmap)
                label.setScaledContents(True)

        else:
            self.pushButton_2.setEnabled(False)
            self.set = 1

    # Back button
    def click6(self):
        show_message("Do you wish go back? (all image enhancements will be removed)", True, "Yes",
                     common.btn1_fun, True, "No", lambda: None)

        if common.show_message_btn1:
            # The images were opened, so to avoid the process to continue using them, we need to close it
            for i in range(len(self.images)):
                self.images[i].close()

            self.close()
            if os.path.exists("Img_files_enhanced.txt"):
                os.remove("Img_files_enhanced.txt")

    # Next button and book-keeping
    def click7(self):
        self.newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory),
                                       "Enhanced")
        self.finishpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory),
                                          "Finished")

        if os.path.exists("Img_files_enhanced.txt"):
            os.remove("Img_files_enhanced.txt")

        copyfile("Img_files_cropped.txt", "Img_files_enhanced.txt")

        with open("Img_files_enhanced.txt") as file:
            data_files = file.read().splitlines()
        file.close()

        for root, dirs, files in os.walk(self.newpathdir):
            for name in files:
                for i, s in zip(range(len(data_files)), data_files):
                    if os.path.basename(s) == name:
                        data_files[i] = os.path.join(root, name)

        with open("Img_files_enhanced.txt", "w") as file:
            for i in range(len(data_files)):
                file.write(data_files[i])
                file.write("\n")

        show_message("Are you sure to move to the next page?"
                     , True, "Yes", common.btn1_fun, True, "No", lambda: None)

        if common.show_message_btn1:
            self.hide()

            with open("Img_files_enhanced.txt") as file:
                self.img_files = file.read().splitlines()
            self.length = len(self.img_files)

            img_enhanced = {"enhanced location": []}
            if self.length > 1:
                for i in range(self.length):
                    if os.path.basename(os.path.dirname(self.img_files[i])) == "Enhanced":
                        img_enhanced["enhanced location"].append(self.img_files[i])
                    else:
                        img_enhanced["enhanced location"].append("<Not Enhanced>")

            # open the file for reading
            try:
                workbook_read = xlrd.open_workbook('image_data.xlsx')
            except:
                show_message("xlsx file cannot be opened, check if the workbook is used "
                             "by another application")

            sheets = workbook_read.sheets()
            worksheet_read = sheets[0]

            # open the same file for writing (just don't write yet)
            workbook_write = xlsxwriter.Workbook(r'image_data.xlsx')
            bold = workbook_write.add_format({'bold': 1})
            worksheet_write = workbook_write.add_worksheet(worksheet_read.name)

            # run through the sheets and store sheets in workbook
            # this still doesn't write to the file yet
            for row in range(worksheet_read.nrows):
                for col in range(worksheet_read.ncols):
                    if row == 0:  # top row is written in bold
                        worksheet_write.write(row, col, worksheet_read.cell(row, col).value, bold)
                    else:
                        worksheet_write.write(row, col, worksheet_read.cell(row, col).value)

            # write NEW data
            worksheet_write.write('F1', 'Location of Enhanced Image File', bold)
            col = 5  # Since we start writing from F
            for key in img_enhanced.keys():
                row = 0
                row += 1
                for item in img_enhanced[key]:
                    worksheet_write.write(row, col, item)
                    row += 1
                col += 1

            workbook_write.close()

            # Create a final finished folder with the last updated files (sorted based on magnification)

            if os.path.exists(self.finishpathdir):
                rmtree(self.finishpathdir)
                os.makedirs(self.finishpathdir)

            else:
                os.makedirs(self.finishpathdir)

            name_move = None
            dir_move = None

            for root, dirs, files in os.walk(os.path.join(self.curr_dir_destination, self.destination_directory)):
                for name in files:
                    if "X" in os.path.basename(root):
                        name_move = os.path.join(root, name)
                        dir_move = os.path.basename(root)
                        for root_en, dirs_en, files_en in os.walk(
                                os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory),
                                             "Enhanced")):
                            for name_en in files_en:
                                if name == name_en:
                                    name_move = os.path.join(root_en, name_en)
                                else:
                                    for root_cr, dirs_cr, files_cr in os.walk(os.path.join(
                                            os.path.join(self.curr_dir_destination, self.destination_directory),
                                            "Cropped")):
                                        for name_cr in files_cr:
                                            if name == name_cr:
                                                name_move = os.path.join(root_cr, name_cr)

                        dir_move_root = os.path.join(self.finishpathdir, dir_move)
                        if not os.path.exists(dir_move_root):
                            os.makedirs(dir_move_root)

                        copyfile(name_move, os.path.join(dir_move_root, os.path.basename(name_move)))

    # The dynamic enhancement in brightness, contrast and sharpness. Images are saved with each click
    def enhancement(self, local):

        enhanced_im = None
        self.refresh = False

        # Adjustment of local sliders
        if self.labels[local].pixmap() is not None:
            display_value = self.sliders[local].value() - 50.0
            k = 1.0 + display_value / 50.0
            m = 6 * (self.set - 1) + local
            self.id = m
            self.lcdNumber.display(str(display_value))

            if self.radioButton_1.isChecked():
                enhancer = ImageEnhance.Brightness(self.images[m])
                enhanced_im = enhancer.enhance(k)
                self.images[m] = enhanced_im

            elif self.radioButton_2.isChecked():
                enhancer = ImageEnhance.Contrast(self.images[m])
                enhanced_im = enhancer.enhance(k)
                self.images[m] = enhanced_im

            elif self.radioButton_3.isChecked():
                enhancer = ImageEnhance.Sharpness(self.images[m])
                enhanced_im = enhancer.enhance(k)
                self.images[m] = enhanced_im

            if self.hist_window_on is True:
                im = self.images[m].histogram()
                self.hist_windows[local].mid_y = self.max_count_hist[m]
                self.hist_windows[local].plot(im, local + 1)

            if not os.path.isdir(self.newpathdir):
                os.makedirs(self.newpathdir)

            enhanced_im.save(os.path.join(self.newpathdir, os.path.basename(self.img_files[m])))

            self.pixel_windows[local].label = local
            self.pixel_windows[local].setImage(enhanced_im)

            image = np.asarray(enhanced_im).copy()
            qimage = NumpyToQImage(image)
            pixmap = QPixmap(qimage)
            w = int(self.labels[local].width() - 4.0)
            h = int(self.labels[local].height() - 4.0)
            smaller_pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            self.labels[local].setPixmap(smaller_pixmap)
            self.labels[local].setScaledContents(True)

            self.verticalSlider_1.setValue(50.0)
            self.verticalSlider_2.setValue(50.0)
            self.verticalSlider_3.setValue(50.0)
            self.verticalSlider_4.setValue(50.0)
            self.verticalSlider_5.setValue(50.0)
            self.verticalSlider_6.setValue(50.0)

    # To show the window where pixel and kernel is selected
    def show_pix_selection_window(self):
        id_temp = self.id
        m = 6 * (self.set - 1) + id_temp

        self.pixel_windows[id_temp].label = id_temp

        image = QImage(self.img_files[id_temp])
        width = image.width()
        height = image.height()
        ratio = height / width
        self.pixel_windows[id_temp].resize(1024, int(ratio * 1024)+200)

        self.pixel_windows[id_temp].setImage(self.images[m])
        self.pixel_windows[id_temp].on = self.pixel_window_on
        self.pixel_windows[id_temp].checkbox_id = self.checkbox_id
        self.pixel_windows[id_temp].image_id = m
        self.pixel_windows[id_temp].img_files = self.img_files
        self.pixel_windows[id_temp].newpathdir = self.newpathdir

        self.pixel_windows[id_temp].kernel_value = self.kernel_value
        self.pixel_windows[id_temp].show()

    # Set the Auto Button property and Text
    def Auto_Brightness_Text(self, button):

        def reconnect(signal, newhandler=None, oldhandler=None):
            while True:
                try:
                    if oldhandler is not None:
                        signal.disconnect(oldhandler)
                    else:
                        signal.disconnect()
                except TypeError:
                    break
            if newhandler is not None:
                signal.connect(newhandler)

        self.button_ID = button

        if button is 1:
            self.pixel_window_on = False
            for i in range(6):
                self.Radios[i].setVisible(True)
                self.checkBoxes[i].setVisible(False)
            self.pushButton_7.setText("Histogram Equalisation")
            reconnect(self.pushButton_7.clicked, partial(self.Auto_Brightness, self.button_ID))
        if button is 2:
            for i in range(6):
                self.Radios[i].setVisible(True)
                self.checkBoxes[i].setVisible(False)
            self.pixel_window_on = False
            self.pushButton_7.setText("Resize Equalisation")
            reconnect(self.pushButton_7.clicked, partial(self.Auto_Brightness, self.button_ID))
        if button is 3:
            for i in range(6):
                self.Radios[i].setVisible(True)
                self.checkBoxes[i].setVisible(False)
            self.pixel_window_on = False
            self.pushButton_7.setText("Absolute Equalisation")
            reconnect(self.pushButton_7.clicked, partial(self.Auto_Brightness, self.button_ID))
        if button is 4:
            for i in range(6):
                self.Radios[i].setVisible(False)
                self.buttonGroup_2.removeButton(self.checkBoxes[i])
                self.checkBoxes[i].setVisible(True)
                self.checkBoxes[i].setChecked(False)

            self.checkbox_id = None
            self.pushButton_7.setText("Selective Equalisation")
            self.pixel_window_on = True
            reconnect(self.pushButton_7.clicked, partial(self.Auto_Brightness, self.button_ID))

    # All Auto Enhancement Functions
    def Auto_Brightness(self, button):
        self.pixel_window_on = False

        if self.auto_applied is True:
            if self.pushButton_7.text() == "Selective Equalisation" or self.pushButton_7.text() == "Reference Selected":
                pass
            else:
                show_message("An auto Enhancement was already applied. Do you wish to Reload the images?", True,
                             "Yes (recommended)", common.btn1_fun, True, "No", lambda: None)
                if common.show_message_btn1:
                    for i in range(self.length):
                        self.images[i] = Image.open(self.img_files[i])

        self.auto_applied = True
        Radio_id = 0
        self.refresh = False
        if not os.path.isdir(self.newpathdir):
            os.makedirs(self.newpathdir)
        for i in range(6):
            if self.Radios[i].isChecked():
                Radio_id = i
        m = 6 * (self.set - 1) + Radio_id

        # Histogram Equalisation
        if button is 1:
            def hist_norm(source, template):

                olddtype = source.dtype
                oldshape = source.shape
                source = source.ravel()
                template = template.ravel()

                s_values, bin_idx, s_counts = np.unique(source, return_inverse=True,
                                                        return_counts=True)
                t_values, t_counts = np.unique(template, return_counts=True)
                s_quantiles = np.cumsum(s_counts).astype(np.float64)
                s_quantiles /= s_quantiles[-1]
                t_quantiles = np.cumsum(t_counts).astype(np.float64)
                t_quantiles /= t_quantiles[-1]
                interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)
                interp_t_values = interp_t_values.astype(olddtype)

                return interp_t_values[bin_idx].reshape(oldshape)

            im_template = np.asarray(self.images[m].convert('L'))

            for i in range(self.length):
                if i is not m:
                    im_source = np.asarray(self.images[i].convert('L'))
                    im_matched = hist_norm(im_source, im_template)
                    self.images[i] = Image.fromarray(im_matched)
                    self.images[i].save(os.path.join(self.newpathdir, os.path.basename(self.img_files[i])))
            self.click1(1)

        # Resize Equalisation
        if button is 2:
            im_template = np.asarray(self.images[m].convert('L'))
            img = cv2.resize(im_template, (1, 1))
            img_ref_value = int(img[[0]])
            for i in range(self.length):
                if i is not m:
                    im_source = np.asarray(self.images[i].convert('L'))
                    img = cv2.resize(im_source, (1, 1))
                    img_value = int(img[[0]])
                    img_enhanced_value = img_value

                    while img_enhanced_value is not img_ref_value:
                        # brightness must be increased
                        if img_enhanced_value < img_ref_value:
                            enhancer = ImageEnhance.Brightness(self.images[i])
                            enhanced_im = enhancer.enhance(1.1)
                            im_enhanced = np.asarray(enhanced_im.convert('L'))
                            img = cv2.resize(im_enhanced, (1, 1))
                            img_enhanced_value = int(img[[0]])
                            self.images[i] = enhanced_im

                        # brightness must be decreased
                        if img_enhanced_value > img_ref_value:
                            enhancer = ImageEnhance.Brightness(self.images[i])
                            enhanced_im = enhancer.enhance(0.99)
                            im_enhanced = np.asarray(enhanced_im.convert('L'))
                            img = cv2.resize(im_enhanced, (1, 1))
                            img_enhanced_value = int(img[[0]])
                            self.images[i] = enhanced_im

                        if abs(img_enhanced_value - img_ref_value) < 3:
                            break

                    self.images[i].save(os.path.join(self.newpathdir, os.path.basename(self.img_files[i])))

            self.click1(1)

        # Absolute Equalisation
        if button is 3:
            im_template = self.images[m].convert('L')
            # px_template = im_template.load()
            # print("value of pixel for source at 4X4 = ", px_template[4, 4])

            img_ref_stat = ImageStat.Stat(im_template)
            img_ref_stat = int(img_ref_stat.mean[0])

            for i in range(self.length):
                if i is not m:
                    # if i == 2:
                    #     px_target = self.images[i].load()
                    #     print("old value of pixel at 4,4, for: ", i, " = ", px_target[4, 4])
                    #     print("old value of pixel at 5,5, for: ", i, " = ", px_target[5, 5])

                    im_source = self.images[i].convert('L')
                    img_stat = ImageStat.Stat(im_source)
                    img_stat = int(img_stat.mean[0])
                    enhanced_im_stat = img_stat

                    while enhanced_im_stat is not img_ref_stat:
                        # brightness must be increased
                        if enhanced_im_stat < img_ref_stat:
                            enhancer = ImageEnhance.Brightness(self.images[i])
                            enhanced_im = enhancer.enhance(1.1)
                            enhanced_im_stat = ImageStat.Stat(enhanced_im)
                            enhanced_im_stat = int(enhanced_im_stat.mean[0])
                            self.images[i] = enhanced_im

                        # brightness must be decreased
                        if enhanced_im_stat > img_ref_stat:
                            enhancer = ImageEnhance.Brightness(self.images[i])
                            enhanced_im = enhancer.enhance(0.99)
                            enhanced_im_stat = ImageStat.Stat(enhanced_im)
                            enhanced_im_stat = int(enhanced_im_stat.mean[0])
                            self.images[i] = enhanced_im

                        if abs(enhanced_im_stat - img_ref_stat) < 3:
                            break

                    # if i == 2:
                    #     px_target = self.images[i].load()
                    #     print("new value of pixel at 4,4, for: ", i," = ", px_target[4, 4])
                    #     print("new value of pixel at 5,5, for: ", i, " = ", px_target[5, 5])
                    #     print("\n")
                    self.images[i].save(os.path.join(self.newpathdir, os.path.basename(self.img_files[i])))

            self.click1(1)

        # Selective Equalisation
        if button is 4:
            self.pixel_window_on = True

        # Update the plot ranges after enhancement
        self.max_count_hist = []
        for i in range(self.length):
            im = self.images[i].histogram()
            im_max = max(im)
            self.max_count_hist.append(im_max)

    # To show original image upon right click
    def show_original_image(self):
        m = 6 * (self.set - 1) + self.id
        self.images[m] = Image.open(self.img_files[m])

        self.pixel_windows[self.id].label = self.id
        self.pixel_windows[self.id].setImage(self.images[m])

        check = os.path.join(self.newpathdir, os.path.basename(self.img_files[m]))

        for root, dirs, files in os.walk(self.newpathdir):
            for name in files:
                if os.path.isfile(check):
                    if name == os.path.basename(check):
                        os.remove(os.path.join(root, name))

        image = QImage(self.img_files[m])
        image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)
        pixmap = QPixmap(image)
        w = int(self.labels[self.id].width() - 4.0)
        h = int(self.labels[self.id].height() - 4.0)
        smaller_pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.labels[self.id].setPixmap(smaller_pixmap)
        self.labels[self.id].setScaledContents(True)

        if self.hist_windows[self.id].show_stat is True:
            self.hist_windows[self.id].show()
            im = self.images[m].histogram()
            self.hist_windows[self.id].mid_y = self.max_count_hist[m]
            self.hist_windows[self.id].plot(im, self.id + 1)

    # show context menu upon right click
    def on_context_menu(self, point):
        if type(self.sender()) is type(self.pushButton_1):
            self.popMenu2.exec_(self.label_7.mapToGlobal(point))

        if type(self.sender()) is type(self.label_1):
            if self.labels[self.id].pixmap() is not None:
                self.popMenu1.exec_(self.labels[self.id].mapToGlobal(point))

    # Turns of the window so that no further plotting
    def hist_window_off(self):
        self.hist_window_on = False

    # Histogram window is updated here during right click and double click
    def show_hist_window(self):
        self.hist_window_on = True
        id_temp = self.id
        self.hist_windows[id_temp].show()
        m = 6 * (self.set - 1) + id_temp
        im = self.images[m].histogram()
        self.id = m
        self.hist_windows[id_temp].mid_y = self.max_count_hist[m]
        self.hist_windows[id_temp].plot(im, id_temp + 1)

    # Actions for mouse click on sliders and double click on labels
    def eventFilter(self, source, event):

        if event.type() == QEvent.MouseButtonPress:
            if source is self.label_7:
                self.popMenu2.exec_(self.label_7.mapToGlobal(event.pos()))

            if isinstance(source, QCheckBox):
                # This is important because for compiler the action happens after mouse click. So it has to be manually
                # override to make it true then false before the original UI action occur.
                source.setChecked(True)
                i = self.checkBoxes.index(source)
                self.checkbox_id = (self.set - 1) * 6 + i

                for i in range(6):
                    self.buttonGroup_2.addButton(self.checkBoxes[i])

                for i in range(6):
                    if not self.checkBoxes[i].isChecked():
                        self.checkBoxes[i].setVisible(False)
                source.setChecked(False)
                self.pushButton_7.setText("Reference Selected")

            if isinstance(source, QRadioButton):
                self.verticalSlider_1.setValue(50.0)
                self.verticalSlider_2.setValue(50.0)
                self.verticalSlider_3.setValue(50.0)
                self.verticalSlider_4.setValue(50.0)
                self.verticalSlider_5.setValue(50.0)
                self.verticalSlider_6.setValue(50.0)

            if isinstance(source, QSlider) and source.orientation() == 2:
                max_pos = source.geometry().height()
                pos = event.pos().y()
                k = max_pos / 100
                slider_pos = pos / k
                slider_pos = 100 - slider_pos
                source.setValue(slider_pos)

            if event.button() == Qt.RightButton:
                if isinstance(source, QLabel):
                    if source is not self.label_7:
                        self.id = self.labels.index(source)

        if event.type() == QEvent.MouseButtonDblClick:
            if isinstance(source, QLabel) and source.pixmap() is not None:
                self.id = self.labels.index(source)
                if self.pixel_window_on is False:
                    self.show_hist_window()
                else:
                    self.show_pix_selection_window()

        return super(ImageExposure, self).eventFilter(source, event)

    # default action to show all images during window open
    def showEvent(self, event):
        self.click1()
        self.pushButton_1.setText("Restore (All) Images")

    # The kernel rectangle is communicated here from the pixel class
    @pyqtSlot(int)
    def set_kernel_value(self, value):
        self.kernel_value = value

    # The change in the selected imaged based on kernel brightness
    @pyqtSlot(int)
    def set_selective_image(self, m):
        self.images[m] = Image.open(os.path.join(self.newpathdir, os.path.basename(self.img_files[m])))
        id_temp = m - 6 * (self.set - 1)

        im = self.images[m].histogram()
        self.hist_windows[id_temp].mid_y = self.max_count_hist[m]
        self.hist_windows[id_temp].plot(im, id_temp + 1)

        image_array = np.asarray(self.images[m].convert('L'))
        image = NumpyToQImage(image_array)

        image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)
        pixmap = QPixmap(image)
        w = int(self.labels[id_temp].width() - 4.0)
        h = int(self.labels[id_temp].height() - 4.0)
        smaller_pixmap = pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.labels[id_temp].setPixmap(smaller_pixmap)
        self.labels[id_temp].setScaledContents(True)

        self.pixel_windows[id_temp].label = id_temp
        self.pixel_windows[id_temp].setImage(self.images[m])


# The histogram window
class Histogram(QDialog):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super(Histogram, self).__init__()
        self.sub = None
        self.mid_y = None
        # a figure instance to plot on
        self.figure = Figure()

        # this is the Canvas Widget that displays the `figure` it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.show_stat = None

    def showEvent(self, event):
        self.show_stat = True
        super(Histogram, self).showEvent(event)

    def hideEvent(self, event):
        self.show_stat = False
        super(Histogram, self).hideEvent(event)

    def closeEvent(self, event):
        self.closed.emit()

    def plot(self, data, label_id=0):
        if self.sub is not None:
            self.sub.remove()
        self.sub = self.figure.add_subplot(111)
        self.setWindowTitle("Histogram No: " + str(label_id))
        self.sub.clear()
        self.sub.autoscale(enable=True, axis='both', tight=None)
        self.sub.set_xlim(left=0, right=255)
        self.sub.set_ylim(top=1.2 * self.mid_y, bottom=0)
        self.sub.plot(data)
        self.canvas.draw()

    def clear_plot(self):
        if self.sub:
            self.hide()


# The image pixel selection window for selective enhancement
class ImagePixel(Ui_ImagePixelSelection.Ui_MainWindow, QMainWindow):
    pointChanged = pyqtSignal(QPointF, QPointF)
    kernel = pyqtSignal(int)
    image_update = pyqtSignal(int)

    def __init__(self, parent=None):
        super(ImagePixel, self).__init__()
        self.setupUi(self)

        self.img_files = None  # To store the locations
        self.pixmap = None  # To display in labels
        self.im = None  # this will get the image as an 'Image' format
        self.on = False  # To know if the selective brightness button has been pressed or not
        self.checkbox_id = None  # this is the reference image
        self.img_files = None  # to store all image locations (connection from exposure class)
        self.newpathdir = None  # To store the save location (connection from exposure class)
        self.image_id = None  # this is the passed image
        self.label = 0  # To know which label ID out of 6 is called, useful for window title
        self.origin = None  # This is origin of pixel point and used to compare when a new point is clicked
        self.circleItem = None  # This is the circle which will be the point of selection
        self.rectItem = None  # This is the square around the point
        self.pixel_plot_is_locked = False  # To make sure that after apply enhancement, not further change of pixel
        self.kernel_value = None  # As long as reference pixel is not selected, it is NONE. Once selected, this
        # value will be assigned as its average value for all other target images

        self.enhanced_im = None  # This is the target full image after apply enhancement
        self.crop_ratio_w = 1  # resolution difference in image when window resize
        self.crop_ratio_h = 1  # resolution difference in image when window resize

        # Buttons
        self.pushButton_1.clicked.connect(self.click1)  # Select Pixel-Point
        self.pushButton_2.clicked.connect(self.click2)  # OK
        self.pushButton_3.clicked.connect(self.click3)  # Cancel

        # My Scene
        self.scene = QGraphicsScene()
        self.scene.clear()

        # My Image
        self.image_item = QGraphicsPixmapItem()

        # My View
        self.view = Click_QGraphicsView(self.graphicsView)

        # My View Initial Geometry
        self.view.setGeometry(self.geometry().x() + 10, self.geometry().y() + 39,
                              self.geometry().width() - 58, self.geometry().height() - 195)

        # My View Setting Scene with rect and point
        self.view.pointChanged.connect(self.pixel_plot)

        # My View Attributes
        self.view.setBackgroundRole(QPalette.Dark)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setRenderHint(QPainter.Antialiasing, False)

    # The button to select Pixel Point (both Reference and Target Images)
    def click1(self):

        if self.checkbox_id is None:
            QApplication.restoreOverrideCursor()
            self.view.ref = None

        # The reference image
        if self.checkbox_id is self.image_id:
            self.view.ref = True
            QApplication.setOverrideCursor(Qt.PointingHandCursor)
            self.pushButton_1.setEnabled(False)
        else:
            self.pushButton_2.setEnabled(False)
            self.view.ref = False
            QApplication.setOverrideCursor(Qt.CrossCursor)
            self.pixel_plot_is_locked = False
            self.pushButton_1.setText("Apply Enhancement")
            QApplication.restoreOverrideCursor()
            self.pushButton_1.clicked.disconnect(self.click1)
            self.pushButton_1.clicked.connect(self.apply_enhancement)

    # This is the Second click on button in the target image to apply the brightness enhancement
    def apply_enhancement(self):
        self.pixel_plot_is_locked = True  # graphics item interaction will be locked
        self.pushButton_1.setText("Click target Pixel-Point")
        self.pushButton_1.clicked.disconnect(self.apply_enhancement)
        self.pushButton_1.clicked.connect(self.click1)
        self.pushButton_2.setEnabled(True)

        # For all target images, once kernel was set and calculated, we apply enhancement upon click
        if self.checkbox_id is not self.image_id and self.kernel_value is not None:
            if self.rectItem is not None:

                r_rect = self.rectItem.rect().toRect()

                r_rect = QRect(r_rect.x() * self.crop_ratio_w, r_rect.y() * self.crop_ratio_h,
                               r_rect.width() * self.crop_ratio_w, r_rect.height() * self.crop_ratio_h)

                r_x1 = int(r_rect.x())
                r_y1 = int(r_rect.y())
                r_x2 = r_x1 + int(r_rect.width())
                r_y2 = r_y1 + int(r_rect.height())

                target_matrix = self.im.crop((r_x1, r_y1, r_x2, r_y2))
                target = target_matrix.convert('L')
                target_stat = ImageStat.Stat(target)
                target_stat = int(target_stat.mean[0])
                enhanced_target_stat = target_stat

                while enhanced_target_stat is not self.kernel_value:
                    if abs(enhanced_target_stat - self.kernel_value) < 3:
                        break

                    # brightness must be increased
                    if enhanced_target_stat < self.kernel_value:
                        enhancer1 = ImageEnhance.Brightness(target)
                        enhanced_target = enhancer1.enhance(1.1)
                        target = enhanced_target

                        enhancer2 = ImageEnhance.Brightness(self.im)
                        self.enhanced_im = enhancer2.enhance(1.1)
                        self.im = self.enhanced_im

                        enhanced_target_stat = ImageStat.Stat(enhanced_target)
                        enhanced_target_stat = int(enhanced_target_stat.mean[0])
                        continue

                    # brightness must be decreased
                    if enhanced_target_stat > self.kernel_value:
                        enhancer1 = ImageEnhance.Brightness(target)
                        enhanced_target = enhancer1.enhance(0.99)
                        target = enhanced_target

                        enhancer2 = ImageEnhance.Brightness(self.im)
                        self.enhanced_im = enhancer2.enhance(0.99)
                        self.im = self.enhanced_im

                        enhanced_target_stat = ImageStat.Stat(enhanced_target)
                        enhanced_target_stat = int(enhanced_target_stat.mean[0])
                        continue

                if not os.path.isdir(self.newpathdir):
                    os.makedirs(self.newpathdir)

                self.im.save(os.path.join(self.newpathdir, os.path.basename(self.img_files[self.image_id])))
                self.image_update.emit(self.image_id)

            else:
                show_message("Select a Target pixel-point")

        elif self.kernel_value is None:
            show_message("Select a Source pixel-point")

    # OK button
    def click2(self):
        self.view.ref = None
        QApplication.restoreOverrideCursor()
        self.pushButton_1.setVisible(False)
        self.close()

    # Cancel button - removes history of any selection
    def click3(self):
        self.view.ref = None
        self.view.click = False
        self.view.selection = False
        self.pushButton_1.setVisible(False)
        QApplication.restoreOverrideCursor()
        self.close()

    # Regardless of button CLoseEvent is always triggered upon window close, so book-keeping
    def closeEvent(self, event):
        self.view.ref = None
        self.view.click = False
        self.view.selection = False
        self.pushButton_1.setVisible(False)
        QApplication.restoreOverrideCursor()

        # Here we will calculate the needed inputs for enhancement in other images
        if self.checkbox_id is self.image_id:
            if self.rectItem is not None:
                r_rect = self.rectItem.rect().toRect()

                r_rect = QRect(r_rect.x() * self.crop_ratio_w, r_rect.y() * self.crop_ratio_h,
                               r_rect.width() * self.crop_ratio_w, r_rect.height() * self.crop_ratio_h)

                r_x1 = int(r_rect.x())
                r_y1 = int(r_rect.y())
                r_x2 = r_x1 + int(r_rect.width())
                r_y2 = r_y1 + int(r_rect.height())

                kernel_matrix = self.im.crop((r_x1, r_y1, r_x2, r_y2))
                kernel = kernel_matrix.convert('L')

                kernel_ref_stat = ImageStat.Stat(kernel)
                kernel_ref_stat = int(kernel_ref_stat.mean[0])
                self.kernel.emit(kernel_ref_stat)

        self.close()

    # Show event upon double click/right click and action
    def showEvent(self, event):

        x_correction = self.frame_1.x() + self.frame_2.x() + self.graphicsView.x()
        y_correction = self.frame_1.y() + self.frame_2.y() + self.graphicsView.y()

        # To force the initial view geometry after window has formed completely (frame_1 is 9)
        self.view.setGeometry(self.geometry().x() + x_correction, self.geometry().y() + y_correction,
                              self.graphicsView.width(), self.graphicsView.height())
        self.setImage(self.im)

        # If the image is to be selective enhanced, then we need all the new attributes of graphicsview window
        if self.on is True:
            self.pushButton_1.setVisible(True)
            self.label_1.setVisible(True)
            self.label_2.setVisible(True)
            self.label_3.setVisible(True)
            self.lcdNumber_1.setVisible(True)
            self.lcdNumber_2.setVisible(True)
            self.lcdNumber_3.setVisible(True)
            self.lcdNumber_4.setVisible(True)
            self.view.on = True

        # If the image is only to be viewed, then no need of pick pixel options, selections and other details
        if self.on is False:
            self.pushButton_1.setVisible(False)
            self.label_1.setVisible(False)
            self.label_2.setVisible(False)
            self.label_3.setVisible(False)
            self.lcdNumber_1.setVisible(False)
            self.lcdNumber_2.setVisible(False)
            self.lcdNumber_3.setVisible(False)
            self.lcdNumber_4.setVisible(False)
            self.view.on = False

        # If the reference image is not checked, then we dont allow user to view the extra attributes
        if self.checkbox_id is None:
            self.pushButton_1.setVisible(False)
            self.label_1.setVisible(False)
            self.label_2.setVisible(False)
            self.label_3.setVisible(False)
            self.lcdNumber_1.setVisible(False)
            self.lcdNumber_2.setVisible(False)
            self.lcdNumber_3.setVisible(False)
            self.lcdNumber_4.setVisible(False)
            self.view.on = False

        # this is the condition to find reference image
        if self.checkbox_id is self.image_id:
            self.pixel_plot_is_locked = False
            self.pushButton_1.setEnabled(True)
            self.pushButton_1.setText("Pick source Pixel-Point")
        else:
            self.pixel_plot_is_locked = False
            self.pushButton_1.setEnabled(True)
            self.pushButton_1.setText("Click target Pixel-Point")

        super(ImagePixel, self).showEvent(event)

    # This function is invoked when we double click the label
    def setImage(self, im):
        self.setWindowTitle("LHT Image Analyzer - Version 1.0")
        self.setWindowTitle("Image No: " + str(self.label + 1))
        self.im = im
        qim = ImageQt(im)
        self.pixmap = QPixmap.fromImage(qim)

        self.crop_ratio_w = self.pixmap.width() / self.view.width()
        self.crop_ratio_h = self.pixmap.height() / self.view.height()

        smaller_pixmap = self.pixmap.scaled(self.view.width(), self.view.height(),
                                            Qt.IgnoreAspectRatio, Qt.FastTransformation)

        self.image_item.setPixmap(smaller_pixmap)
        self.scene.addItem(self.image_item)

        self.scene.setSceneRect(0, 0, self.view.width(), self.view.height())
        self.view.setGeometry(0, 0, self.view.width(), self.view.height())

        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setScene(self.scene)

        self.view.setSceneSize()

    # When window gets resize, view size is changed and image is set again (refresh)
    def resizeEvent(self, event):

        x_correction = self.frame_1.x() + self.frame_2.x() + self.graphicsView.x()
        y_correction = self.frame_1.y() + self.frame_2.y() + self.graphicsView.y()

        # To force the image set operation only after window has formed completely (frame_1 expands from 0 to 9)
        if self.frame_1.x() > 0:
            self.view.setGeometry(self.geometry().x() + x_correction, self.geometry().y() + y_correction,
                                  self.graphicsView.width(), self.graphicsView.height())
            self.setImage(self.im)

    # Here the new enclosing rectangle and centre point is created
    @pyqtSlot(QPointF, QPointF)
    def pixel_plot(self, origin, pos):
        if self.checkbox_id is not None and self.pixel_plot_is_locked is False:
            # Each time when new rectangle is created, old is deleted
            if self.origin is not None:
                self.scene.removeItem(self.circleItem)
                self.scene.removeItem(self.rectItem)

            self.rectItem = QGraphicsRectItem()
            rect1 = QRectF(origin, pos)
            self.rectItem.setRect(rect1)
            self.rectItem.setPen(QPen(Qt.red, 0, Qt.DashDotLine))
            self.circleItem = QGraphicsEllipseItem()
            centre = origin + (pos - origin) / 2.0
            centre_TL = QPointF(centre.x() - 2.0, centre.y() - 2.0)
            centre_BR = QPointF(centre.x() + 2.0, centre.y() + 2.0)
            rect2 = QRectF(centre_TL, centre_BR)
            self.circleItem.setRect(rect2)
            self.circleItem.setPen(QPen(Qt.red, 2.0))
            self.scene.addItem(self.circleItem)
            self.scene.addItem(self.rectItem)
            self.origin = origin


# The mouse click actions associated with image pixel selection window
class Click_QGraphicsView(QGraphicsView):
    pointChanged = pyqtSignal(QPointF, QPointF)

    scene_size = (0, 0)
    event_origin = None
    click_pos = None
    event_pos = None
    event_corner = None
    on = False  # connection of on from Ui_ImagePixel class
    ref = None  # connection of ref from Ui_ImagePixel class
    center_pos = None
    changing_pos = None
    div = 2

    def action(self):

        if self.div is 0:
            self.div = 1

        if self.ref is not None:
            # either when ref is True or False, but not when it is None

            self.center_pos = [int(self.click_pos.x()), int(self.click_pos.y())]  # assigned the centre point
            self.event_origin = QPointF(0, 0)

            if self.center_pos[0] - 0 < self.scene_size[0] - self.center_pos[0] and self.center_pos[1] - 0 < \
                    self.scene_size[1] - self.center_pos[1]:
                x1 = self.click_pos.x() / self.div
                y1 = self.click_pos.y() / self.div
                sq = min(x1, y1)
                self.event_origin.setX(int(self.click_pos.x() - sq))
                self.event_origin.setY(int(self.click_pos.y() - sq))

            if self.center_pos[0] - 0 > self.scene_size[0] - self.center_pos[0] and self.center_pos[1] - 0 < \
                    self.scene_size[1] - self.center_pos[1]:
                x1 = (self.scene_size[0] - self.click_pos.x()) / self.div
                y1 = self.click_pos.y() / self.div
                sq = min(x1, y1)
                self.event_origin.setX(int(self.click_pos.x() - sq))
                self.event_origin.setY(int(self.click_pos.y() - sq))

            if self.center_pos[0] - 0 < self.scene_size[0] - self.center_pos[0] and self.center_pos[1] - 0 > \
                    self.scene_size[1] - self.center_pos[1]:
                x1 = self.click_pos.x() / self.div
                y1 = (self.scene_size[1] - self.click_pos.y()) / self.div
                sq = min(x1, y1)
                self.event_origin.setX(int(self.click_pos.x() - sq))
                self.event_origin.setY(int(self.click_pos.y() - sq))

            if self.center_pos[0] - 0 > self.scene_size[0] - self.center_pos[0] and self.center_pos[1] - 0 > \
                    self.scene_size[1] - self.center_pos[1]:
                x1 = (self.scene_size[0] - self.click_pos.x()) / self.div
                y1 = (self.scene_size[1] - self.click_pos.y()) / self.div
                sq = min(x1, y1)
                self.event_origin.setX(int(self.click_pos.x() - sq))
                self.event_origin.setY(int(self.click_pos.y() - sq))

            trans = [2 * (self.center_pos[0] - self.event_origin.x()),
                     2 * (self.center_pos[1] - self.event_origin.y())]
            trans_point = QPointF(trans[0], trans[1])
            self.event_corner = self.event_origin + trans_point

            self.pointChanged.emit(self.event_origin, self.event_corner)

    def mousePressEvent(self, event):

        if self.on is True:
            event_pos = self.mapToScene(event.pos())
            self.click_pos = event_pos
            self.action()

    def wheelEvent(self, event):

        wheel_counter = event.angleDelta()
        if wheel_counter.y() / 120 == -1:
            self.div += 0.3

        elif wheel_counter.y() / 120 == 1:
            self.div -= 0.3

        self.action()

    def setSceneSize(self):
        rect = self.scene().sceneRect()
        self.scene_size = (rect.width(), rect.height())
