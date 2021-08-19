# -*- coding: utf-8 -*-
"""
Created on Mon Jan 14 10:45:15 2019
@author: U724965
"""

import os
import imghdr
import datetime
import shutil
import imutils
import sys
import operator
from functools import partial

import cv2
import pytesseract
import xlsxwriter
from PIL import Image
from PyQt5.QtCore import QEvent, Qt, pyqtSignal, pyqtSlot, QPoint, QLineF
from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QColor, QFont, QImage
from PyQt5.QtGui import QPixmap, QPainter, QPen, QPalette
from PyQt5.QtWidgets import QListWidgetItem, QStyledItemDelegate, QLineEdit, QFileDialog, QApplication
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QFrame, \
    QGraphicsView, QMenu, QAction, QGraphicsLineItem, QLCDNumber, QLabel, QDialog, \
    QDialogButtonBox, QHBoxLayout, QGridLayout

import Ui_ImageSort
import common

pytesseract.pytesseract.tesseract_cmd = (os.path.join(os.getcwd(), "Application\\Tesseract-OCR\\tesseract.exe"))

# Functions defined in the common class
show_message = common.show_message
view_file_location = common.view_file_location
view_image = common.view_image
del_folder = common.del_folder

# Two masks to compare "value" microns and "value" pixels in the delegate class
MaskRole1 = Qt.UserRole + 100
MaskRole2 = Qt.UserRole + 100


# Main class to do Image sorting (First Window)
class ImageSort(Ui_ImageSort.Ui_MainWindow, QMainWindow):
    # The mask role changes for lengths as entered by the user
    statusChanged = pyqtSignal(int, int, str)

    # Initialising the class variables and functions
    def __init__(self):
        super(ImageSort, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("LHT Image Analyzer - Version 1.0")

        # Directories
        self.destination_directory = "Destination"
        self.source_directory = "Source"
        self.format = [".png", ".tif", ".gif"]
        self.curr_dir_source = os.getcwd()
        self.curr_dir_destination = os.getcwd()

        # Magnifications, Crop and Temp folders
        self.path = [os.path.join(self.curr_dir_destination,
                                  self.destination_directory)]
        if not os.path.isdir(self.path[0]):
            os.mkdir(self.path[0])

        self.img_files = []  # Source image location
        self.img_files_cropped = []  # Cropped files location
        self.img_files_enhanced = []  # Enhanced images location
        self.scale_txt = []  # Scale text
        self.scale_mag = []  # Image magnifications
        self.scale_len = []  # Image scale lengths
        self.scale_mag_string = []  # Image magnification as string with a preceding x
        self.img_destination = []  # Destination image locations as keys and corresponding to OCR values
        self.completed = 0  # To update progressbar percentage
        self.clicked_once = False  # To check if user clicked destination update and excel sheet button
        self.progressBar.hide()  # Progress bar is only required during OCR
        self.label_3.hide()  # Progress percentage
        self.index_diff = None  # To find the image index within img_files upon right click

        # Context Menu and double clicks for Main Menu, List widget and Tabs
        self.actionChange_Source_Directory.triggered.connect(partial(self.change_directory, 0))
        self.actionChange_Destination_Directory.triggered.connect(partial(self.change_directory, 1))
        self.actionMAnual.triggered.connect(partial(self.change_button_text, 0))
        self.actionSemi_Auto_OCR.triggered.connect(partial(self.change_button_text, 1))
        self.actionExit.triggered.connect(sys.exit)
        self.listWidget.itemClicked.connect(self.set_height_width)
        self.listWidget.itemDoubleClicked.connect(self.item_click)
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.on_context_menu)
        self.popMenu = QMenu(self)
        self.action1 = QAction("View Image File (Grayscale)")
        self.action1.triggered.connect(self.open_file)

        # Buttons
        self.pushButton_2.setText("OCR Mode (Default)")
        self.pushButton_2.installEventFilter(self)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_4.setEnabled(False)
        self.pushButton_6.setEnabled(False)
        self.pushButton_1.clicked.connect(self.click1)  # Update source location
        self.pushButton_3.clicked.connect(self.click3)  # View Results
        self.pushButton_4.clicked.connect(self.click4)  # Move Files
        self.pushButton_5.clicked.connect(self.click5)  # Update Excel Sheet
        self.pushButton_7.clicked.connect(self.click7)  # Clear Temp Folder

    # Update source location "optionally delete all destination directories here"
    def click1(self):
        self.img_destination = None
        self.label_3.hide()
        self.progressBar.hide()
        self.pushButton_3.setEnabled(False)
        cancel = False
        if os.path.exists('image_data.xlsx'):
            try:
                os.remove('image_data.xlsx')
            except:
                show_message("xlsx file cannot be removed, check if the workbook is used", True, "Retry",
                             common.btn1_fun, True, "Cancel", common.btn2_fun)
                if common.show_message_btn1:
                    cancel = False
                    self.click1()
                if common.show_message_btn2:
                    cancel = True

        if cancel is False:
            self.listWidget.clear()
            self.pushButton_4.setEnabled(False)
            self.pushButton_6.setEnabled(True)
            self.completed = 0
            self.progressBar.setValue(self.completed)
            self.img_files[:] = []
            self.scale_txt[:] = []
            self.scale_len[:] = []
            self.scale_mag[:] = []
            self.scale_mag_string[:] = []
            self.update_source_location()
            self.clicked_once = False

    # OCR button
    def click2(self):
        self.iterate()
        self.pushButton_2.setEnabled(False)
        self.pushButton_2.setToolTip('Refresh source location to do OCR again')
        self.pushButton_3.setToolTip(None)
        self.pushButton_3.setEnabled(True)
        self.pushButton_4.setEnabled(True)
        self.click3()

    # View the OCR results on screen
    def click3(self):
        self.list_view()
        self.pushButton_3.setToolTip('Update OCR to view results')
        self.pushButton_3.setEnabled(False)
        self.pushButton_4.setEnabled(True)

    # Move the files to destination folder
    def click4(self):
        self.pushButton_3.setEnabled(False)
        self.update_destination_location()
        self.scale_mag_string[:] = []
        self.pushButton_4.setToolTip('Update OCR to move files')

    # Update excel file
    def click5(self):
        # To correct the data addition into dictionary without index failure
        if self.scale_txt and self.scale_len and self.scale_mag and self.clicked_once is False:

            if self.img_destination is not None:  # Always update excel sheet upon first click = make new dictionary
                self.img_destination.clear()

            self.img_destination = {"location": [], "scale": [], "pixel": [], "magnification": []}
            if len(self.img_files) > 1:
                for i in range(len(self.img_files)):
                    self.img_destination["location"].append(self.img_files[i])
                    self.img_destination["scale"].append(self.scale_txt[i])
                    self.img_destination["pixel"].append(self.scale_len[i])
                    self.img_destination["magnification"].append("X" + str(self.scale_mag[i]))
            else:
                print("No files in the image location text file..")

        if self.img_destination:
            try:
                workbook = xlsxwriter.Workbook(r'image_data.xlsx')
            except:
                show_message("xlsx file cannot be handled (updating previous Excel sheet - open), "
                             "check if the workbook is used by another application")

            item = QListWidgetItem("Updating Excel sheet")
            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)
            worksheet = workbook.add_worksheet()
            bold = workbook.add_format({'bold': 1})
            worksheet.write('A1', 'Location of Image File', bold)
            worksheet.write('B1', 'Scale Dimension', bold)
            worksheet.write('C1', 'Unit Length (in Pixels)', bold)
            worksheet.write('D1', 'Magnification', bold)
            col = 0
            for key in self.img_destination.keys():
                row = 0
                row += 1
                for item in self.img_destination[key]:
                    worksheet.write(row, col, item)
                    row += 1
                col += 1

            try:
                workbook.close()
            except:
                show_message("xlsx file cannot be handled (updating previous Excel sheet - close), "
                             "check if the workbook is used by another application")

        else:

            if os.path.isfile("image_data.xlsx"):
                os.remove("image_data.xlsx")

            try:
                workbook = xlsxwriter.Workbook(r'image_data.xlsx')
            except:
                show_message("xlsx file cannot be handled (new Excel sheet - open), "
                             "check if the workbook is used by another application")

            worksheet = workbook.add_worksheet()
            bold = workbook.add_format({'bold': 1})
            worksheet.write('A1', 'Location of Image File', bold)
            worksheet.write('B1', 'Scale Dimension', bold)
            worksheet.write('C1', 'Unit Length (in Pixels)', bold)
            worksheet.write('D1', 'Magnification', bold)
            col = 0
            for i, item in zip(range(len(self.img_files)), self.img_files):
                row = i + 1
                worksheet.write(row, col, item)

            try:
                workbook.close()
            except:
                show_message("xlsx file cannot be handled (new Excel sheet - close), "
                             "check if the workbook is used by another application")

        self.clicked_once = True
        self.listWidget.addItem("\n")

    # Next Button
    def click6(self):

        show_message("Are you sure to move to the next page?"
                     , True, "Yes", common.btn1_fun, True, "No", lambda: None)

        if common.show_message_btn1:
            self.hide()
            self.click5()
            self.pushButton_6.setEnabled(False)
            file1 = open("Img_files.txt", "w")
            file2 = open("Img_files_cropped.txt", "w")

            for name in range(len(self.img_files)):
                file1.write(self.img_files[name])
                file2.write(self.img_files[name])
                file1.write("\n")
                file2.write("\n")
            file1.close()
            file2.close()

            new_path = os.path.join(self.curr_dir_destination,
                                    os.path.join(self.destination_directory, "Cropped"))
            if os.path.exists(new_path):
                for root, dirs, files in os.walk(new_path):
                    for name in files:
                        if os.path.isfile(os.path.join(root, name)):
                            os.remove(os.path.join(root, name))
                os.rmdir(new_path)

    # Delete Temp and Cropped files
    def click7(self):
        self.listWidget.addItem("\n")

        status = del_folder(os.path.join(self.source_directory, "Temp"), self.img_files, "Img_files.txt")

        if status == 1:
            self.listWidget.addItem("Temp Directory has been deleted")
        elif status == 0:
            self.listWidget.addItem("Temp Directory does not exist")

        status = del_folder(os.path.join(self.destination_directory, "Cropped"), self.img_files_cropped,
                            "Img_files_cropped.txt")
        if status == 1:
            self.listWidget.addItem("Cropped Directory has been deleted")
        elif status == 0:
            self.listWidget.addItem("Cropped Directory does not exist")

        status = del_folder(os.path.join(self.destination_directory, "Enhanced"), self.img_files_enhanced,
                            "Img_files_enhanced.txt")
        if status == 1:
            item = QListWidgetItem("Enhanced Directory has been deleted")
            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)
        elif status == 0:
            item = QListWidgetItem("Enhanced Directory does not exist")
            self.listWidget.addItem("Enhanced Directory does not exist")
            self.listWidget.scrollToItem(item)

    # This is to change Source or Destination folder
    def change_directory(self, selection):
        if selection == 0:
            file = self.openFileNameDialog()
            try:
                self.curr_dir_source = os.path.dirname(file)
                self.source_directory = os.path.basename(file)
            except:
                pass

        if selection == 1:
            file = self.openFileNameDialog()
            try:
                self.curr_dir_destination = os.path.dirname(file)
                self.destination_directory = os.path.basename(file)
                self.path.insert(0, file)
            except:
                pass

    # Change label (manual or OCR) and Button text (update source location function will be called first)
    def change_button_text(self, selection):

        if selection == 0:  # Default/Manual
            self.click1()
            self.label_4.setText("Mode of Data Entry: Manual")
            self.pushButton_2.setText("Manual Mode")
        if selection == 1:  # Semi Auto
            self.click1()
            self.label_4.setText("Mode of Data Entry: Semi-Auto")
            self.pushButton_2.setText("OCR Mode (Default)")

    # To show the Folder browser dialog
    def openFileNameDialog(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file:
            return file

    # To determine what happens when clicked on the text editor
    def item_click(self):
        path = self.listWidget.currentItem().text()  # A local Variable called "path"

        if path[0].isdigit():  # To get path as data in the format: "value" microns
            # if the data written is a path then this deletes preceding "value) "from it
            for i in range(len(path)):
                if path[0] == " ":
                    path = path[1:]
                    break
                path = path[1:]

        if os.path.isfile(path):
            dialog = ImageDialog(path)

            image = QImage(path)
            width = image.width()
            height = image.height()
            ratio = height / width

            dialog.resize(1024, int(ratio * 1024))
            dialog.exec_()

        elif os.path.isdir(path):
            show_message("The file does not exist in the Source location")

    # update image locations from source directory except target directory into list
    def update_source_location(self):

        if not os.path.isdir(os.path.join(self.curr_dir_source, self.source_directory)):
            os.makedirs(os.path.join(self.curr_dir_source, self.source_directory))

        for root, dirs, files in os.walk(os.path.join(self.curr_dir_source, self.source_directory)):
            for name in files:
                incl = 1
                if os.path.dirname(root) in self.path:
                    continue  # if the path is already inside the destination folder, it is not added as a source file

                elif ".jpg" in name:
                    for check in self.img_files:
                        if not check:  # check if the file exists, if not then delete from list
                            self.img_files.remove(check)
                        elif check == os.path.join(root,
                                                   name):  # check if the file is duplicate, if is then do not append
                            incl = 0
                    if incl == 1:
                        self.img_files.append(os.path.join(root, name))

                elif os.path.splitext(name)[1] in self.format:
                    for check in self.img_files:
                        if not check:
                            self.img_files.remove(check)
                        if check == os.path.join(root, name):
                            incl = 0
                    if incl == 1:
                        self.img_files.append(self.format_to_jpg(os.path.join(root, name)))
                        if self.img_files[-1] == 'remove':
                            del self.img_files[-1]

        if not self.img_files:
            self.pushButton_2.setEnabled(False)
            show_message("No images in Source location\n(other file types maybe found in Source\\Temp folder)")

        else:
            self.pushButton_2.setEnabled(True)
            item = QListWidgetItem("Current source folder has the following images "
                                   "[Double Click to View / Measure Image]")

            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)

            for i in range(len(self.img_files)):
                item = QListWidgetItem(self.img_files[i])
                self.listWidget.addItem(item)  # In their order of discovery
                self.listWidget.scrollToItem(item)

        self.listWidget.addItem("\n")

    # This is where each image file undergo OCR and subsequent updating of list
    def iterate(self):
        import numpy as np
        self.label_3.show()
        self.progressBar.setValue(self.completed)
        self.progressBar.show()
        a = datetime.datetime.now()

        for i in range(len(self.img_files)):
            img = cv2.imread(self.img_files[i],
                             cv2.IMREAD_GRAYSCALE)  # Other modes of read are cv2.IMREAD_COLOR, cv2.IMREAD_UNCHANGED
            height = img.shape[0]
            width = img.shape[1]

            # We approximate that the scale text resides on the bottom 10% of image
            ocr = img[int(0.90 * height):height, int(0.50 * width):width]  # cropping the bottom 10% part of the image
            # and the right 50% of the image (make suitable changes)

            # First estimate the scale label width by scanning lines (longest white line, could be also border of box)
            length, start_col, end_col = self.ocr_len(ocr)
            ocr_new = ocr[0:height, start_col:end_col]

            # Next we wil try to delete all noises other than digits
            rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
            tophat = cv2.morphologyEx(ocr_new, cv2.MORPH_TOPHAT, rectKernel)
            gradX = cv2.Sobel(tophat, ddepth=cv2.CV_32F, dx=1, dy=0,
                              ksize=-1)
            gradX = np.absolute(gradX)
            (minVal, maxVal) = (np.min(gradX), np.max(gradX))
            gradX = (255 * ((gradX - minVal) / (maxVal - minVal)))
            gradX = gradX.astype("uint8")
            gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKernel)
            thresh = cv2.threshold(gradX, 0, 255,
                                   cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            conts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)
            conts = imutils.grab_contours(conts)

            # Now we mke a dictionary containing serial numbers and their corresponding areas for each contours detected
            area_dict = dict()
            for (j, c) in enumerate(conts):
                area_dict[str(j)] = cv2.contourArea(c)

            # We will now see the two greatest areas from this dictionary and get their 4 coordinates
            # Sort in descending order
            sorted_area_dict = sorted(area_dict.items(), key=operator.itemgetter(1), reverse=True)

            # If any area was detected at all (length of dict will be at least 1)
            if len(sorted_area_dict) > 0:
                j_1 = int(sorted_area_dict[0][0])  # index of highest area

                # if there is a second area detected at all (length of dict will be at least 2)
                if len(sorted_area_dict) > 1:
                    j_2 = int(sorted_area_dict[1][0])  # index of second highest area
                else:
                    j_2 = j_1

                # Get all the 4 coordinates of both the areas
                x1_TL = 0
                x2_TL = 0
                y1_TL = 0
                y2_TL = 0
                x1_BR = 0
                x2_BR = 0
                y1_BR = 0
                y2_BR = 0
                for (j, c) in enumerate(conts):
                    if j == j_1:  # Rectangle coordinates of largest area
                        x1_TL = cv2.boundingRect(c)[0]
                        y1_TL = cv2.boundingRect(c)[1]
                        x1_BR = cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2]
                        y1_BR = cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3]

                    if j == j_2:  # Rectangle coordinates of second largest area
                        x2_TL = cv2.boundingRect(c)[0]
                        y2_TL = cv2.boundingRect(c)[1]
                        x2_BR = cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2]
                        y2_BR = cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3]

                # Then find coordinates of the biggest rectangle that encloses these two large contours
                x_TL = min(x1_TL, x2_TL)
                y_TL = min(y1_TL, y2_TL)
                x_BR = max(x1_BR, x2_BR)
                y_BR = max(y1_BR, y2_BR)

                # Give a little clarence if required
                ocr_final = ocr_new[y_TL:y_BR, x_TL:x_BR]

                # Last step is to see if we need threshold inversion, since black text on white background works best
                threshold_final = cv2.threshold(ocr_final, 200, 250, cv2.THRESH_BINARY)[1]

                # If average color distribution over this threshold is black, then invert
                avg_color_per_row = np.average(threshold_final, axis=0)
                avg_color = np.average(avg_color_per_row, axis=0)

                # If the average color is pitch black, then threshold range was slightly off (image could be too dim)
                thresh_inc = 5  # Threshold increment
                flag = 0  # flag makes sure that dark image does not shift into too bright image and gets checked again
                while avg_color <= 20.0:
                    flag = 1
                    threshold_final = cv2.threshold(ocr_final, 200 - thresh_inc, 250 - thresh_inc, cv2.THRESH_BINARY)[1]
                    avg_color_per_row = np.average(threshold_final, axis=0)
                    avg_color = np.average(avg_color_per_row, axis=0)
                    thresh_inc = thresh_inc + 5
                    # We must assign a limit value so that the while loop does not run infinitely
                    if 200 - thresh_inc == 25:
                        break

                thresh_inc = 5  # Threshold increment back to 5
                # If the average color is pure white, then threshold range was slightly off (image could be too bright)
                while avg_color >= 235.0 and flag == 0:
                    threshold_final = cv2.threshold(ocr_final, 200 + thresh_inc, 250, cv2.THRESH_BINARY)[1]
                    avg_color_per_row = np.average(threshold_final, axis=0)
                    avg_color = np.average(avg_color_per_row, axis=0)
                    thresh_inc = thresh_inc + 5
                    # We must assign a limit value so that the while loop does not run infinitely
                    if 200 + thresh_inc == 245:
                        break

                if avg_color < 100:  # Means that the letters are white on black background
                    ocr_final = cv2.bitwise_not(threshold_final)
                else:
                    ocr_final = threshold_final

                text = self.ocr_txt(ocr_final)

            # If there are no areas, then we assume the image has only noise and therefore no text to detect
            else:
                text = 0

            # Scales updated
            self.scale_len.append(length)
            self.scale_txt.append(text)
            self.completed = float((i + 1) / len(self.img_files) * 100)
            QApplication.processEvents()
            self.progressBar.setValue(int(self.completed))

        b = datetime.datetime.now()
        if not self.img_files:
            show_message("No images to check OCR")
        else:
            item = QListWidgetItem("*Completed OCR Check..\n")
            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)
            c = str(b - a)
            c = c[:-3]
            item = QListWidgetItem("Total time taken for OCR check = %s (Hours:Min:Sec.Millisec)\n" % c)
            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)

    # All the updated values printed after OCR check on the text editor
    def list_view(self, manual=False):

        if manual is True:
            self.listWidget.clear()
            delegate = ListDelegate(self.listWidget)
            delegate.statusChanged.connect(self.scale_update)
            self.listWidget.setItemDelegate(delegate)
            if not self.img_files:
                show_message("No locations or scales to update")
            else:
                self.listWidget.addItem("\nThe locations of files in the list are: "
                                        "[Double Click to View/Measure Image]")
            for i in range(len(self.img_files)):
                self.listWidget.addItem(str(i + 1) + ") " + str(self.img_files[i]))

            self.listWidget.addItem("\nEnter corresponding scale texts: [Right Click to View / Measure Image] ")
            for i in range(len(self.img_files)):
                item0 = QListWidgetItem()
                item0.setForeground(Qt.black)
                item0.setData(MaskRole1, "{}) 000 micro\\ns".format(i + 1))
                item0.setFlags(item0.flags() | Qt.ItemIsEditable)

                # Since there is no scale text, we create a blank list here
                if not self.scale_txt:
                    for j in range(len(self.img_files)):
                        self.scale_txt.append(0)

                if self.scale_txt[i] == 0:
                    item0.setForeground(Qt.red)

                item0.setText("{}) {} microns".format(i + 1, self.scale_txt[i]))
                self.listWidget.addItem(item0)
                self.listWidget.scrollToItem(item0)

            self.listWidget.addItem("\nEnter corresponding scale length: [Right Click to View / Measure Image] ")

            for i in range(len(self.img_files)):
                item1 = QListWidgetItem()
                item1.setForeground(Qt.black)
                item1.setData(MaskRole2, "{}) 000 pixels".format(i + 1))
                item1.setFlags(item1.flags() | Qt.ItemIsEditable)

                # Since there is no scale length, we create a blank list here
                if not self.scale_len:
                    for j in range(len(self.img_files)):
                        self.scale_len.append(0)

                if self.scale_len[i] == 0:
                    item1.setForeground(Qt.red)

                item1.setText("{}) {} pixels".format(i + 1, self.scale_len[i]))
                self.listWidget.addItem(item1)
                self.listWidget.scrollToItem(item1)

            self.listWidget.addItem("\n")

        elif manual is False:
            self.listWidget.clear()
            delegate = ListDelegate(self.listWidget)
            delegate.statusChanged.connect(self.scale_update)
            self.listWidget.setItemDelegate(delegate)

            if not self.img_files:
                show_message("No locations or scales to update")

            else:
                self.listWidget.addItem("\nThe locations of files in the list are: "
                                        "[Double Click to View/Measure Image]")

                for i in range(len(self.img_files)):
                    self.listWidget.addItem(str(i + 1) + ") " + str(self.img_files[i]))

                self.listWidget.addItem("\nCorresponding scale texts are: ")
                for i in range(len(self.scale_txt)):
                    item2 = QListWidgetItem()
                    item2.setForeground(Qt.black)
                    item2.setData(MaskRole1, "{}) 000 micro\\ns".format(i + 1))
                    # n is not detected correct if \\ not used
                    item2.setFlags(item2.flags() | Qt.ItemIsEditable)

                    if self.scale_txt[i] == 0:
                        item2.setForeground(Qt.red)

                    item2.setText("{}) {} microns".format(i + 1, self.scale_txt[i]))
                    self.listWidget.addItem(item2)
                    self.listWidget.scrollToItem(item2)

                self.listWidget.addItem("\nCorresponding scale length in pixels are: ")
                for i in range(len(self.scale_len)):
                    item3 = QListWidgetItem()
                    item3.setForeground(Qt.black)
                    item3.setData(MaskRole2, "{}) 000 pixels".format(i + 1))
                    item3.setFlags(item3.flags() | Qt.ItemIsEditable)

                    if self.scale_len[i] == 0:
                        item3.setForeground(Qt.red)

                    item3.setText("{}) {} pixels".format(i + 1, self.scale_len[i]))
                    self.listWidget.addItem(item3)
                    self.listWidget.scrollToItem(item3)

                self.listWidget.addItem("\n")

    # Check the file and move them to appropriate locations
    def update_destination_location(self):

        if not self.img_files:
            show_message("No images in Source location to move")

        if self.scale_txt and self.clicked_once is False:
            self.listWidget.addItem("Corresponding scale magnifications are: ")
            for i in range(len(self.img_files)):
                text = self.scale_txt[i]
                length = self.scale_len[i]
                self.ocr_mag(text, length)
                # length = self.check_len_txt(i, length, text)
                self.scale_len[i] = length
                item = QListWidgetItem(str(i + 1) + ") X" + str(self.scale_mag[i]))
                self.listWidget.addItem(item)
                self.listWidget.scrollToItem(item)
            self.listWidget.addItem("\n")

        for i in range(len(self.path)):
            if not os.path.isdir(self.path[i]):
                os.mkdir(self.path[i])

        for i in range(len(self.img_files)):
            working_dir = os.path.split(os.path.abspath(self.img_files[i]))[0]
            if os.path.normpath(working_dir) in self.path and self.clicked_once is False:
                item = QListWidgetItem("The file already exists in destination folder, checking next file..")
                self.listWidget.addItem(item)
                self.listWidget.scrollToItem(item)
                continue

        # To correct the data addition into dictionary without index failure
        if self.scale_txt and self.clicked_once is False:
            # Actual moving of files
            for i in range(len(self.img_files)):
                working_dir = os.path.split(os.path.abspath(self.img_files[i]))[0]
                # check if the folder of file is in one of the destination folders

                if os.path.normpath(working_dir) in self.path:
                    item = QListWidgetItem("The file already exists in destination folder, checking next file..")
                    self.listWidget.addItem(item)
                    self.listWidget.scrollToItem(item)
                    continue
                else:
                    item = QListWidgetItem("The file is moved to destination folder, checking next file..")
                    self.listWidget.addItem(item)
                    self.listWidget.scrollToItem(item)
                    newpath = os.path.join(self.curr_dir_destination, self.scale_mag_string[i])
                    newpathfile = os.path.join(newpath, os.path.basename(self.img_files[i]))

                    shutil.move(self.img_files[i], newpathfile)
                    self.img_files[i] = os.path.join(newpath, os.path.basename(self.img_files[i]))

    # To check if the image resolution has changed with the previously checked image file during iteration (This
    # function is currently ignored!)
    def img_res_check(self, img_location):
        img = cv2.imread(img_location, cv2.IMREAD_GRAYSCALE)
        if (abs(img.shape[0] - self.lcdNumber_1.intValue()) >= 2 or abs(
                img.shape[1] - self.lcdNumber_2.intValue()) >= 2):
            show_message("Warning: The resolution of the picture has changed (OCR detection Error Possibility!) ", True,
                         "View File", partial(view_file_location, img_location), True, "Force Resolution to Default",
                         partial(self.resize_fun, img_location), True, "Accept Risk", lambda: None)

    # Displays the last checked image's resolution
    def set_height_width(self):
        path = self.listWidget.currentItem().text()
        if os.path.isfile(path):
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            self.lcdNumber_1.display(img.shape[0])
            self.lcdNumber_2.display(img.shape[1])

    # Instruction to change the resolution
    def resize_fun(self, img_location):
        img = cv2.imread(img_location, cv2.IMREAD_GRAYSCALE)
        img.resize(self.lcdNumber_1.intValue(), self.lcdNumber_2.intValue())
        os.remove(img_location)
        cv2.imwrite(img_location, img)
        show_message("Auto-Rescale to default resolution completed..")

    # Instruction to automatically convert image files in other formats to jpg type, original file copied to Temp
    # Change jpg to png or tiff here to make change in the uniform file types
    def format_to_jpg(self, img_path):
        new_path = os.path.join(self.curr_dir_source, os.path.join(self.source_directory, "Temp"))
        if not os.path.isdir(new_path):
            os.mkdir(new_path)

        im = Image.open(img_path)
        rgb_im = im.convert('RGB')

        new_path_file = os.path.join(new_path, (os.path.splitext(os.path.basename(img_path))[0] + '.jpg'))

        if not os.path.isfile(new_path_file):  # copy the file into temp folder only if it does not exist
            item = QListWidgetItem("\nImage " + str(os.path.basename(img_path)) +
                                   "was in a non-jpg format, \nSo we convert and copy it to the default temp "
                                   "directory (_Source_/Temp) \n")
            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)
            rgb_im.save(new_path_file)
        else:
            new_path_file = "remove"

        return new_path_file

    # Function for OCR using pytesseract (The real pre-operations occur in "iterate" step - requiring time management)
    def ocr_txt(self, ocr):  # calculating scale bar text of an image
        flag = 0
        ocr_text = pytesseract.image_to_string(ocr, config='--psm 6')

        for s in ocr_text.split():
            if s.isdigit():
                flag = 1
                break
            else:
                continue
        if flag == 1:
            ocr_text = [int(s) for s in ocr_text.split() if s.isdigit()][0]

        else:
            item = QListWidgetItem("Warning! failed to distinguish numerical value during OCR. Edit the values "
                                   "Manually.. ")
            self.listWidget.addItem(item)
            self.listWidget.scrollToItem(item)
            ocr_text = 0

        return ocr_text

    # Calculating scale bar length of an image (static function placed here for easy reading of code)
    # Efficiency could be increased by optimising the linear jumps in pixel during scan by the last known length
    def ocr_len(self, ocr):
        start_col = 0

        def check_line(img, m, n, columns):  # to return the number of pixels in a horizontal line
            length = 0
            for i in range(columns):
                if (n + i + 1) < columns:
                    if img[m][n + i + 1] > 50:
                        length = length + 1
                    else:
                        break
            return length

        edged = cv2.Canny(ocr, 90, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)
        rows, columns = edged.shape[:2]
        ocr_length = 0

        for j in range(rows):
            for k in range(columns):
                if edged[j][k] > 200 and edged[j][k - 1] > 50:
                    length = check_line(edged, j, k, columns)
                    if length > ocr_length:
                        start_col = k
                        ocr_length = length

        end_col = start_col + ocr_length
        start_col = start_col

        return ocr_length, start_col, end_col

    # Function to detect appropriate magnification
    def ocr_mag(self, ocr_text, ocr_length):
        global mag
        s = "None"
        if ocr_length == 0 or ocr_text == 0:
            res = 0
        else:
            res = ocr_text / ocr_length

        if 0.2 > res > 0.19:
            mag = 200  # reference magnification of 200 gives 0.194 micron resolution per pixel
            s = os.path.join(self.destination_directory, "X") + str(mag)

        elif res == 0:
            mag = 0
            s = os.path.join(self.destination_directory, "X_Unknown")

        elif res > 0.2 or res < 0.19:
            ratio = res / 0.194
            ratio = round(ratio, 2)

            if ratio == 0:
                mag = 0
                s = os.path.join(self.destination_directory, "X_Unknown")
            else:
                mag = int(200 / ratio)
                mag = int(50 * round(float(mag / 50), 0))  # Magnification is approx. always a multiplier of 50X
                s = os.path.join(self.destination_directory, "X") + str(mag)

        self.scale_mag.append(mag)
        self.scale_mag_string.append(s)
        new_path = os.path.join(self.curr_dir_destination, s)

        if new_path not in self.path:
            self.path.append(new_path)

    # Check if there is deviation in scales corresponding to similar microns (This function is currently ignored!)
    def check_len_txt(self, i, length, txt):
        if self.scale_txt:  # if the list is non empty
            for j in range(len(self.scale_txt)):
                if (self.scale_txt[j] == txt) and (abs(self.scale_len[j] - length) > 10):
                    item = QListWidgetItem(
                        "\nWarning: Difference between pixel lengths of two similar images!")
                    self.listWidget.addItem(item)
                    self.listWidget.scrollToItem(item)

                    item = QListWidgetItem("Scale length of image %i with scale text %i = %i pixels" % (
                        j + 1, self.scale_txt[j], self.scale_len[j]))
                    self.listWidget.addItem(item)
                    self.listWidget.scrollToItem(item)

                    item = QListWidgetItem(
                        "Scale length of image %i with scale text %i = %i pixels" % (i + 1, txt, length))
                    self.listWidget.addItem(item)
                    self.listWidget.scrollToItem(item)
        return length

    # The action to open folder/file
    def open_file(self):
        length = len(self.img_files)
        if 0 <= self.index_diff < length:
            try:
                # print("Image No:", self.index_diff, " is open..")
                ext = imghdr.what(self.img_files[self.index_diff])
            except:
                ext = None
            if os.path.exists(self.img_files[self.index_diff]) and ext is not None:
                dialog = ImageDialog(self.img_files[self.index_diff])

                image = QImage(self.img_files[self.index_diff])
                width = image.width()
                height = image.height()
                ratio = height / width

                dialog.resize(1024, int(ratio * 1024))
                dialog.exec_()

    # To open reassign the functions to the data entry mode selected based on button text
    # def eventFilter(self, source, event):
    #
    #     # Connect and disconnect Data Entry button
    #     def reconnect(signal, newhandler=None, oldhandler=None):
    #         while True:
    #             try:
    #                 if oldhandler is not None:
    #                     signal.disconnect(oldhandler)
    #                 else:
    #                     signal.disconnect()
    #             except TypeError:
    #                 break
    #         if newhandler is not None:
    #             signal.connect(newhandler)
    #
    #     if event.type() == QEvent.MouseButtonPress:
    #         if source is self.pushButton_2:
    #             if self.pushButton_2.isEnabled():
    #
    #                 if self.pushButton_2.text() == "Manual Mode":
    #                     #  Blank readings and View Results
    #                     reconnect(self.pushButton_2.clicked, partial(self.list_view, True))
    #                     self.pushButton_3.setVisible(False)
    #
    #                 if self.pushButton_2.text() == "OCR Mode (Default)":
    #                     self.pushButton_3.setVisible(True)
    #                     reconnect(self.pushButton_2.clicked, self.click2)
    #
    #     return super(ImageSort, self).eventFilter(source, event)

    # To show the right click actions on list widget
    def on_context_menu(self, point):
        self.action1.setText("Select an Image File to View Options")
        self.popMenu.addAction(self.action1)

        success = False
        self.index_diff = -1
        index = self.listWidget.currentRow()
        check = self.listWidget.item(index).text()
        word1 = "texts"
        word2 = "length"

        if word1 in check or word2 in check:
            success = True

        while success is not True:
            index = index - 1
            if index >= 0:
                check = self.listWidget.item(index).text()
                if word1 in check or word2 in check:
                    success = True
                self.index_diff = self.index_diff + 1

            if index < 0:
                break

        if self.index_diff >= 0:
            # To avoid errors when any non image file is chosen
            try:
                ext = imghdr.what(self.img_files[self.index_diff])
            except:
                ext = None

            # To avoid error while selecting blank lines
            try:
                if os.path.exists(self.img_files[self.index_diff]) and ext is not None:
                    self.popMenu.removeAction(self.action1)
                    self.action1.setText("View: " + os.path.basename(self.img_files[self.index_diff]) + " (Grayscale)")
                    self.popMenu.addAction(self.action1)
            except:
                pass

        self.popMenu.exec_(self.listWidget.mapToGlobal(point))

    # To get the 3 values into this class from Delegate class: serial number, value, selection type (microns/pixels)
    @pyqtSlot(int, int, str)
    def scale_update(self, num, val, selection):
        if selection == "microns":
            if len(self.scale_txt) > 0:
                self.scale_txt[num - 1] = val
            else:
                show_message("The files have already been sorted to the Destination")
        elif selection == "pixels":
            if len(self.scale_len) > 0:
                self.scale_len[num - 1] = val
            else:
                show_message("The files have already been sorted to the Destination")


# Delegate class to apply mask and change only the values in the text editor
class ListDelegate(QStyledItemDelegate):
    statusChanged = pyqtSignal(int, int, str)
    selection = None

    # During the click on editor
    def createEditor(self, parent, option, index):
        check = index.data()
        if check[-7:] == "microns":
            mask = index.data(MaskRole1)
        else:
            mask = index.data(MaskRole2)

        if mask is not None:
            editor = QLineEdit(parent)
            editor.setInputMask(mask)
            return editor

    # After edit has been completed
    def setModelData(self, editor, model, index):

        save = index.data()  # save is the data before editing
        num = ""  # num is used to find the index by noting down the value before ')'
        for i in range(len(save)):
            if save[i] == ")":
                break
            if save[i].isdigit():
                num = num + save[i]
        num = int(num)

        if editor.hasAcceptableInput():
            text = editor.text()
            model.setData(index, text, Qt.DisplayRole)

        check = index.data()  # check is used to find if the incoming field is microns/pixels

        if check[-7:] == "microns":
            selection = "microns"  # selection determines what is the field edited
            re = QRegularExpression(r"(\d+)\) (\d+) microns")
        else:
            selection = "pixels"
            re = QRegularExpression(r"(\d+)\) (\d+) pixels")

        match = re.match(index.data())
        color = QColor("red")

        if match.hasMatch():
            val = match.captured(match.lastCapturedIndex())
            if int(val) != 0 or index.data() != save:
                color = QColor("blue")
                self.statusChanged.emit(num, int(val), selection)

            if int(val) == 0:
                color = QColor("red")

            if index.data() == save and int(val) != 0:
                color = QColor("black")

        model.setData(index, color, Qt.ForegroundRole)


class ClickableGraphicsView(QGraphicsView):
    distanceChanged = pyqtSignal(float)  # The signal that connects the distance value to the main window

    def __init__(self, parent=None):
        super(ClickableGraphicsView, self).__init__(parent)
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self.setBackgroundRole(QPalette.Dark)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHint(QPainter.Antialiasing, False)
        self.pixmap_item = None
        self.div = 0
        self.line_item = QGraphicsLineItem()
        self.line_item.setPen(QPen(Qt.blue, 4.0 + self.div))

    def setImage(self, path):
        pixmap = QPixmap(path)
        # My Scene and my Image
        self.pixmap_item = self.scene().addPixmap(pixmap)
        self.pixmap_item.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)

    # The wheel scroll can increase or decrease thickness
    def wheelEvent(self, event):
        wheel_counter = event.angleDelta()
        if wheel_counter.y() / 120 == -1:
            self.div -= 0.3
        elif wheel_counter.y() / 120 == 1:
            self.div += 0.3
        self.line_item.setPen(QPen(Qt.blue, 4.0 + self.div))

    # When mouse button is pressed
    def mousePressEvent(self, event):
        start_pos = self.calculate_pos(event.pos())  # Starting position upon click
        if not start_pos.isNull():
            self.line_item.setLine(QLineF(start_pos, start_pos))
            self.scene().addItem(self.line_item)
        super(ClickableGraphicsView, self).mousePressEvent(event)

    # When mouse is moved
    def mouseMoveEvent(self, event):
        if self.line_item.scene() is not None:
            end_pos = self.calculate_pos(event.pos())  # The final position during click release
            if not end_pos.isNull():
                line = self.line_item.line()
                # When shift key is pressed condition, horizontal line
                if event.modifiers() & Qt.ShiftModifier:
                    end_pos.setY(line.p1().y())
                line.setP2(end_pos)
                self.line_item.setLine(line)

    # When mouse is released
    def mouseReleaseEvent(self, event):
        if self.line_item.scene() is not None:
            # self.scene().removeItem(self.line_item)
            distance = self.line_item.line().length()
            self.distanceChanged.emit(distance)  # This value is displayed in the LCD widget

    def calculate_pos(self, pos):
        if self.pixmap_item is not None:
            if self.pixmap_item == self.itemAt(pos):
                sp = self.mapToScene(pos)
                lp = self.pixmap_item.mapToItem(self.pixmap_item, sp)
                p = lp.toPoint()
                if self.pixmap_item.pixmap().rect().contains(p):
                    return p
        return QPoint()

    def resizeEvent(self, event):
        self.fitInView(self.sceneRect(), Qt.IgnoreAspectRatio)
        super(ClickableGraphicsView, self).resizeEvent(event)


# The Image show Dialog window upon double click list widget, where we can also measure the distances
class ImageDialog(QDialog):
    def __init__(self, image, parent=None):
        super(ImageDialog, self).__init__(parent)
        self.setWindowTitle("LHT Image Analyzer - Version 1.0")

        # My View
        self.view = ClickableGraphicsView()
        self.view.setImage(image)

        # Image Dialog Design
        label = QLabel("Distance")
        lcdNumber = QLCDNumber()

        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        lcdNumber.setFont(font)
        lcdNumber.setAutoFillBackground(False)
        lcdNumber.setFrameShape(QFrame.Box)
        lcdNumber.setFrameShadow(QFrame.Plain)
        lcdNumber.setSmallDecimalPoint(False)
        lcdNumber.setDigitCount(5)
        lcdNumber.setMode(QLCDNumber.Dec)
        lcdNumber.setSegmentStyle(QLCDNumber.Flat)

        self.view.distanceChanged.connect(lcdNumber.display)
        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)
        lay = QGridLayout(self)
        lay.addWidget(self.view, 0, 0, 1, 2)
        hlay = QHBoxLayout()
        hlay.addWidget(label)
        hlay.addWidget(lcdNumber)
        hlay.addStretch()
        lay.addLayout(hlay, 1, 0)
        lay.addWidget(buttonbox, 1, 1)
