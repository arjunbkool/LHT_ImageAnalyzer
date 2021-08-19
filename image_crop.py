# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 12:41:16 2019

@author: U724965
"""

import math
import os
import re
from shutil import copyfile, rmtree

import cv2
import numpy as np
import xlrd
import xlsxwriter
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor, QImage, QBrush
from PyQt5.QtWidgets import QMainWindow, QFrame, QLabel, QMenu, QAction

import Ui_ImageCrop
import common
import image_roi

show_message = common.show_message
view_file_location = common.view_file_location
view_image = common.view_image
del_folder = common.del_folder
crop_img = common.crop_img
NumpyToQImage = common.NumpyToQImage


# The main window class to do the Crop functions (Second Window)
class ImageCrop(Ui_ImageCrop.Ui_MainWindow, QMainWindow):
    # A value has to be passed so that we know the ROI window is alive
    formLife = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ImageCrop, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("LHT Image Analyzer - Version 1.0")

        # Initial knowledge of our directories
        self.destination_directory = None
        self.source_directory = None
        self.curr_dir_source = None
        self.curr_dir_destination = None
        self.newpathdir = None

        self.transparency = 220  # A transparency is set for all the initial label images before global crop
        self.btn_img = [None, None, None,
                        None, None, None]  # To store image for edit ROE button (to be disposed later)
        self.img_files = None  # To store the image locations
        self.img_crop = []  # To store the cropped image locations for dictionary
        self.length = 0  # To store the number of files
        self.img_files_border = []  # To store the label border, so as to descide if crop completed or not
        self.set = 0  # It stores the value of current set of images displayed
        self.refresh = False  # If refresh is true, we are regenerating images on window (eg: after crop)
        self.formCall = False  # To know if the ROI window is on or not
        self.id = 0  # To know the label id, image that has to be reloaded

        # Make ImageRoi Windows
        self.form3 = image_roi.ImageROI(self)
        self.form4 = image_roi.ImageROI(self)
        self.form5 = image_roi.ImageROI(self)
        self.form6 = image_roi.ImageROI(self)
        self.form7 = image_roi.ImageROI(self)
        self.form8 = image_roi.ImageROI(self)
        self.forms = [self.form3, self.form4, self.form5,
                      self.form6, self.form7, self.form8]

        # create context menu for labels
        self.popMenu1 = QMenu(self)
        self.action00 = QAction("Reload Original Image")
        self.popMenu1.addAction(self.action00)
        self.action00.triggered.connect(self.show_original_image)

        # Buttons
        self.pushButton_1.clicked.connect(self.click1)  # Show images button
        self.pushButton_2.clicked.connect(self.click2_previous)  # Previous set button
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_3.clicked.connect(self.click2_next)  # Next set button
        self.pushButton_8.clicked.connect(self.click3)  # Refresh button for all images
        self.pushButton_6.clicked.connect(self.click6)  # Auto crop button for the 6 images in current window
        self.pushButton_7.clicked.connect(self.click7)  # Auto crop button for all images

        # The label characteristics
        self.labels = [self.label_1, self.label_2, self.label_3,
                       self.label_4, self.label_5, self.label_6]
        for label in self.labels:
            label.installEventFilter(self)
            label.setContextMenuPolicy(Qt.CustomContextMenu)
            label.customContextMenuRequested.connect(self.on_context_menu)

    # Show images button
    def click1(self):

        self.pushButton_6.setEnabled(True)
        self.pushButton_7.setEnabled(True)

        self.refresh = True

        # If there is a cropped file, then we view cropped images which has both original and cropped images
        if os.path.isfile('Img_files_cropped.txt'):
            pass
        elif os.path.isfile('Img_files.txt'):
            copyfile("Img_files.txt", "Img_files_cropped.txt")

        with open("Img_files_cropped.txt") as file:
            self.img_files = file.read().splitlines()
        self.length = len(self.img_files)
        file.close()

        # img_files_border has "True" values for cropped images and False for original images
        self.img_files_border[:self.length] = [False] * self.length
        for i in range(self.length):
            if os.path.basename(os.path.dirname(self.img_files[i])) == "Cropped":
                self.img_files_border[i] = True

        if self.formCall:
            n = 6 if (self.length - self.set * 6) > 6 else (self.length - (self.set - 1) * 6)
            for i, label in zip(range(n), self.labels):
                k = (self.set - 1) * 6 + i
                image = QImage(self.img_files[k])
                image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)

                p = QPainter(image)
                p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                p.fillRect(image.rect(), QColor(0, 0, 0, self.transparency))
                p.end()

                pixmap = QPixmap(image)
                w = int(label.width() - 4.0)
                h = int(label.height() - 4.0)

                if self.img_files_border[k]:
                    smaller_pixmap = pixmap.scaledToWidth(w, Qt.FastTransformation)
                    label.setScaledContents(False)
                    label.setFrameShadow(QFrame.Sunken)
                else:
                    smaller_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)
                    label.setScaledContents(True)
                    label.setFrameShadow(QFrame.Plain)

                label.setPixmap(smaller_pixmap)
                self.btn_img[i] = self.img_files[k]

            if n < 6:
                self.pushButton_3.setEnabled(False)
                displays = [False, False, False, False, False, False]
                displays[:n] = [True] * n

                for i, label, display in zip(range(6), self.labels, displays):
                    if not display:
                        label.clear()
                        label.setFrameShadow(QFrame.Plain)
                        self.btn_img[i] = None

        else:
            self.set = 1  # first set of image displayed with each click 1
            self.pushButton_2.setEnabled(False)  # previous set button is False
            self.pushButton_3.setEnabled(True) if self.length > 6 else self.pushButton_3.setEnabled(False)  # next set

            self.btn_img = [None, None, None, None, None, None]
            n = 6 if self.length > 6 else self.length  # first six images are displayed

            self.formCall = False

            for i, label, filename, border, in zip(range(n), self.labels, self.img_files, self.img_files_border):
                image = QImage(filename)
                image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)

                p = QPainter(image)
                p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                p.fillRect(image.rect(), QColor(0, 0, 0, self.transparency))
                p.end()

                pixmap = QPixmap(image)
                w = int(label.width() - 4.0)
                h = int(label.height() - 4.0)

                if border:
                    smaller_pixmap = pixmap.scaledToWidth(w, Qt.FastTransformation)
                    label.setScaledContents(False)
                    label.setFrameShadow(QFrame.Sunken)
                else:
                    smaller_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)
                    label.setScaledContents(True)
                    label.setFrameShadow(QFrame.Plain)

                label.setPixmap(smaller_pixmap)
                self.btn_img[i] = filename

    # Next set button
    def click2_next(self):

        self.btn_img = [None, None, None, None, None, None]
        self.pushButton_2.setEnabled(True)
        self.set = self.set + 1

        n = 6 if (self.length - self.set * 6) > 6 else (self.length - (self.set - 1) * 6)

        for i, label in zip(range(n), self.labels):
            k = (self.set - 1) * 6 + i
            image = QImage(self.img_files[k])
            image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)

            p = QPainter(image)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.fillRect(image.rect(), QColor(0, 0, 0, self.transparency))
            p.end()

            pixmap = QPixmap(image)
            w = int(label.width() - 4.0)
            h = int(label.height() - 4.0)

            if self.img_files_border[k]:
                smaller_pixmap = pixmap.scaledToWidth(w, Qt.FastTransformation)
                label.setScaledContents(False)
                label.setFrameShadow(QFrame.Sunken)
            else:
                smaller_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)
                label.setScaledContents(True)
                label.setFrameShadow(QFrame.Plain)

            label.setPixmap(smaller_pixmap)
            self.btn_img[i] = self.img_files[k]

        if n < 6:
            self.pushButton_3.setEnabled(False)
            displays = [False, False, False, False, False, False]
            displays[:n] = [True] * n

            for i, label, display in zip(range(6), self.labels, displays):
                if not display:
                    label.clear()
                    label.setFrameShadow(QFrame.Plain)
                    self.btn_img[i] = None

    # Previous set button
    def click2_previous(self):
        self.btn_img = [None, None, None, None, None, None]
        if self.set > 1:
            self.pushButton_3.setEnabled(True)

        self.set = self.set - 1  # display previous set of image
        if self.set == 1:
            self.pushButton_2.setEnabled(False)  # no more previous image set

        if self.set > 0:

            for i, label in zip(range(6), self.labels):
                k = (self.set - 1) * 6 + i
                image = QImage(self.img_files[k])
                image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)

                p = QPainter(image)
                p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                p.fillRect(image.rect(), QColor(0, 0, 0, self.transparency))
                p.end()

                pixmap = QPixmap(image)
                w = int(label.width() - 4.0)
                h = int(label.height() - 4.0)

                if self.img_files_border[k]:
                    smaller_pixmap = pixmap.scaledToWidth(w, Qt.FastTransformation)
                    label.setScaledContents(False)
                    label.setFrameShadow(QFrame.Sunken)
                else:
                    smaller_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)
                    label.setScaledContents(True)
                    label.setFrameShadow(QFrame.Plain)

                label.setPixmap(smaller_pixmap)
                self.btn_img[i] = self.img_files[k]

        else:
            self.pushButton_2.setEnabled(False)
            self.set = 1

    # Refresh Button
    def click3(self):
        if self.refresh and self.label_1.pixmap() is not None:
            show_message("Do you to refresh images? (all cropped files will be removed)", True,
                         "Yes", common.btn1_fun, True, "No", lambda: None)

            self.pushButton_6.setEnabled(True)
            self.pushButton_7.setEnabled(True)

            if common.show_message_btn1:
                new_path = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory), "Cropped")

                if os.path.exists(new_path):
                    rmtree(new_path)

                if os.path.exists("Img_files_cropped.txt"):
                    os.remove("Img_files_cropped.txt")

        self.click1()

    # Back button
    def click4(self):
        show_message("WARNING if you go back - All changes made will be Lost (Including OCR "
                     "and all other Manual Data Entered)", True, "Yes", common.btn1_fun, True, "No", lambda: None)

        if common.show_message_btn1:
            self.form3.close()
            self.form4.close()
            self.form5.close()
            self.form6.close()
            self.form7.close()
            self.form8.close()
            self.hide()

            if os.path.exists("Img_files_cropped.txt"):
                os.remove("Img_files_cropped.txt")
            if os.path.exists("Img_files.txt"):
                os.remove("Img_files.txt")

    # Next button
    def click5(self):
        show_message("Are you sure to move to the next page?"
                     , True, "Yes", common.btn1_fun, True, "No", lambda: None)

        if common.show_message_btn1:
            self.hide()
            if os.path.isfile('Img_files_cropped.txt'):
                with open("Img_files_cropped.txt") as file:
                    self.img_files = file.read().splitlines()
                self.length = len(self.img_files)

            self.img_crop = {"crop location": []}
            if len(self.img_files) > 1:
                for i in range(len(self.img_files)):
                    if os.path.basename(os.path.dirname(self.img_files[i])) == "Cropped":
                        self.img_crop["crop location"].append(self.img_files[i])
                    else:
                        self.img_crop["crop location"].append("<Not Cropped>")

            # open the file for reading
            try:
                workbook_read = xlrd.open_workbook('image_data.xlsx')
            except:
                show_message("xls file cannot be opened, check if the workbook is used "
                             "by another application")

            workbook_read = xlrd.open_workbook('image_data.xlsx')
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
            worksheet_write.write('E1', 'Location of Cropped Image File', bold)
            col = 4  # Since we start writing from E
            for key in self.img_crop.keys():
                row = 0
                row += 1
                for item in self.img_crop[key]:
                    worksheet_write.write(row, col, item)
                    row += 1
                col += 1

            workbook_write.close()

    # Crop button for Auto Crop
    def click6(self):

        self.newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory), "Cropped")

        try:
            if not os.path.isdir(self.newpathdir):
                os.makedirs(self.newpathdir)
        except:
            show_message("Please close the /Cropped Folder or try again")

        if not os.path.isfile('Img_files_cropped.txt'):
            copyfile("Img_files.txt",
                     "Img_files_cropped.txt")  # cropped files could have been deleted manually in between

        with open("Img_files_cropped.txt", "r") as file:
            self.img_files = file.read().splitlines()
        file.close()

        # To read percentage
        if self.lineEdit_1.text() == "":
            percent = 0
        else:
            string_percent = self.lineEdit_1.text()
            string_percent = re.sub("\D", "", string_percent)
            percent = float(string_percent)

        if percent > 100:
            percent = 100

        frameshadows = [self.label_1.frameShadow(), self.label_2.frameShadow(), self.label_3.frameShadow(),
                        self.label_4.frameShadow(), self.label_5.frameShadow(), self.label_6.frameShadow()]

        pixmaps = [self.label_1.pixmap(), self.label_2.pixmap(), self.label_3.pixmap(),
                   self.label_4.pixmap(), self.label_5.pixmap(), self.label_6.pixmap()]

        for i, label, frameshadow, pixmap in zip(range(6), self.labels, frameshadows, pixmaps):
            if frameshadow == 16 and pixmap is not None:
                img = cv2.imread(self.btn_img[i], cv2.IMREAD_GRAYSCALE)
                image = crop_img(img, percent)
                image = np.asarray(image).copy()
                k = (self.set - 1) * 6 + i
                self.img_files_border[k] = True

                qimage = NumpyToQImage(image)
                pixmap = QPixmap(qimage)
                w = int(label.width() - 4.0)
                h = int(label.height() - 4.0)

                if self.img_files_border[k]:
                    smaller_pixmap = pixmap.scaledToWidth(w, Qt.FastTransformation)
                    label.setScaledContents(False)
                    label.setFrameShadow(QFrame.Sunken)
                else:
                    smaller_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)
                    label.setScaledContents(True)
                    label.setFrameShadow(QFrame.Plain)

                label.setPixmap(smaller_pixmap)

                newpath = os.path.join(self.newpathdir, os.path.basename(self.btn_img[i]))

                if os.path.exists(newpath):
                    os.remove(newpath)
                    pixmap.save(newpath)
                else:
                    pixmap.save(newpath)

                for j in range(len(self.img_files)):
                    if os.path.basename(self.img_files[j]) == os.path.basename(newpath):
                        self.img_files[j] = newpath

        with open("Img_files_cropped.txt", "w") as file:
            for j in range(len(self.img_files)):
                file.write(self.img_files[j])
                file.write("\n")
        file.close()

    # Crop button for Auto Crop all images
    def click7(self):

        self.newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory), "Cropped")

        try:
            if not os.path.isdir(self.newpathdir):
                os.mkdir(self.newpathdir)
        except:
            show_message("Please close the /Cropped Folder or try again")

        # To read percentage
        if self.lineEdit_1.text() == "":
            percent = 0
        else:
            string_percent = self.lineEdit_1.text()
            string_percent = re.sub("\D", "", string_percent)
            percent = float(string_percent)

        if percent > 100:
            percent = 100

        if not os.path.isfile('Img_files_cropped.txt'):
            copyfile("Img_files.txt",
                     "Img_files_cropped.txt")  # cropped files could have been deleted manually in between

        with open("Img_files_cropped.txt", "r") as file:
            self.img_files = file.read().splitlines()
        file.close()

        for i in range(self.length):
            if os.path.basename(os.path.dirname(self.img_files[i])) != "Cropped":
                img = cv2.imread(self.img_files[i], cv2.IMREAD_GRAYSCALE)

                image = crop_img(img, percent)
                image = np.asarray(image).copy()
                self.img_files_border[i] = True
                qimage = NumpyToQImage(image)
                pixmap = QPixmap(qimage)
                newpath = os.path.join(self.newpathdir, os.path.basename(self.img_files[i]))

                if os.path.exists(newpath):
                    os.remove(newpath)
                    pixmap.save(newpath)
                else:
                    pixmap.save(newpath)

                for j in range(len(self.img_files)):
                    if os.path.basename(self.img_files[j]) == os.path.basename(newpath):
                        self.img_files[j] = newpath

        with open("Img_files_cropped.txt", "w") as file:
            for j in range(len(self.img_files)):
                file.write(self.img_files[j])
                file.write("\n")
        file.close()
        self.refresh = False
        self.click1()
        self.pushButton_6.setEnabled(False)
        self.pushButton_7.setEnabled(False)

    # To show original image upon right click
    def show_original_image(self):
        m = 6 * (self.set - 1) + self.id
        self.newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory), "Cropped")
        newpath = os.path.join(self.newpathdir, os.path.basename(self.img_files[m]))

        flag = 0
        # the image has been cropped, so delete the file and replace the name in cropped.txt, global array, also display
        for i in range(len(self.img_files)):
            if self.img_files[i] == newpath:
                flag = 1
                if os.path.exists(newpath):
                    os.remove(newpath)

                # old path before crop (in source dir or destination dir) is written in img_files.txt
                with open("Img_files.txt", "r") as file:
                    img_files_old = file.read().splitlines()
                file.close()
                oldpath = img_files_old[m]
                self.img_files[i] = oldpath

                with open("Img_files_cropped.txt", "w") as file:
                    for j in range(len(self.img_files)):
                        file.write(self.img_files[j])
                        file.write("\n")
                file.close()

                # Replacing border with False, since crop image is removed
                self.img_files_border[m] = False

                # To show in the corresponding label, determine label id first
                k = m - (self.set - 1) * 6
                image = QImage(self.img_files[m])
                image = image.convertToFormat(QImage.Format_ARGB8565_Premultiplied)

                p = QPainter(image)
                p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                p.fillRect(image.rect(), QColor(0, 0, 0, self.transparency))
                p.end()

                pixmap = QPixmap(image)
                w = int(self.labels[k].width() - 4.0)
                h = int(self.labels[k].height() - 4.0)

                smaller_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)
                self.labels[k].setScaledContents(True)
                self.labels[k].setFrameShadow(QFrame.Plain)

                self.labels[k].setPixmap(smaller_pixmap)
                self.btn_img[k] = self.img_files[m]

        # The image has not been cropped, so no action is needed
        if flag == 0:
            pass

    # show context menu upon right click
    def on_context_menu(self, point):
        if type(self.sender()) is type(self.label_1):
            if self.sender().pixmap() is not None:
                self.popMenu1.exec_(self.sender().mapToGlobal(point))

    # Double click on image label to view the edit window
    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if isinstance(source, QLabel) and source.pixmap() is not None:
                i = self.labels.index(source)
                self.forms[i].setImage(self.btn_img[i])
                self.forms[i].destination_directory = self.destination_directory
                self.forms[i].source_directory = self.source_directory
                self.forms[i].curr_dir_source = self.curr_dir_source
                self.forms[i].curr_dir_destination = self.curr_dir_destination
                self.forms[i].show()
                self.forms[i].formLife.connect(self.formRefresh)

        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                if isinstance(source, QLabel):
                    self.id = self.labels.index(source)

        return super(ImageCrop, self).eventFilter(source, event)

    # Draw crop rectangles by percentage only over the non edited labels
    def paintEvent(self, event):

        if self.lineEdit_1.text() == "":
            percent = 0
        else:
            string_percent = self.lineEdit_1.text()
            string_percent = re.sub("\D", "", string_percent)
            percent = float(string_percent)

        if percent > 100:
            percent = 100

        frames = [self.frame_1.geometry().topLeft(), self.frame_2.geometry().topLeft(),
                  self.frame_3.geometry().topLeft(),
                  self.frame_4.geometry().topLeft(), self.frame_5.geometry().topLeft()]

        labels_tl = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        labels_br = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        for i in range(6):
            if i < 3:
                labels_tl[i] = frames[0] + frames[1] + frames[2] + self.labels[i].geometry().topLeft()
                labels_br[i] = frames[0] + frames[1] + frames[2] + self.labels[i].geometry().bottomRight()

            if i > 2:
                labels_tl[i] = frames[0] + frames[3] + frames[4] + self.labels[i].geometry().topLeft()
                labels_br[i] = frames[0] + frames[3] + frames[4] + self.labels[i].geometry().bottomRight()

            x1 = labels_tl[i].x()
            y1 = labels_tl[i].y()
            x2 = labels_br[i].x()
            y2 = labels_br[i].y()

            w = x2 - x1
            h = y2 - y1
            w_curr = int(w * math.sqrt(percent * 0.01))
            h_curr = int(h * math.sqrt(percent * 0.01))
            kx = (w - w_curr) / 2
            ky = (h - h_curr) / 2
            x3 = int(x1 + kx)
            y3 = int(y1 + ky)

            if self.labels[i].frameShadow() == 16 and self.labels[i].pixmap() is not None:
                painter = QPainter()
                painter.begin(self)
                painter.setPen(QPen(QBrush(Qt.black), 3))
                painter.drawRect(x3, y3, w_curr, h_curr)
                self.update()
                painter.end()

    def showEvent(self, event):
        self.click1()

    # The form refresh signal from forms
    @pyqtSlot(bool)
    def formRefresh(self, status):
        if status:
            self.refresh = False
            self.formCall = True
            self.click1()
