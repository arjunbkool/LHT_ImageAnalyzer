# -*- coding: utf-8 -*-
"""
Created on Thu Feb  10 12:41:16 2019

@author: U724965
"""


import os
from shutil import copyfile

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QRectF, QRect, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QFrame, QGraphicsView

import Ui_ImageROI


# The class that is invoked upon double clicking labels for crop function
class ImageROI(Ui_ImageROI.Ui_MainWindow, QMainWindow):
    formLife = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ImageROI, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("LHT Image Analyzer - Version 1.0")

        # Initial knowledge of our directories
        self.destination_directory = None
        self.source_directory = None
        self.curr_dir_source = None
        self.curr_dir_destination = None
        self.newpathdir = None

        self.path = None       # The incoming path location
        self.img_files = None  # All the images, so as to reproduce original image
        self.pixmap = None     # The pixmap has to be known for two functions. set image and crop image

        # Buttons
        self.pushButton_1.clicked.connect(self.click1)   # View Original Image
        self.pushButton_2.clicked.connect(self.click2)   # Crop the image
        self.pushButton_3.clicked.connect(self.click3)   # Close the window

        # My Scene
        self.scene = QGraphicsScene()
        self.scene.clear()

        # My Image
        self.image_item = QGraphicsPixmapItem()

        # My ROI
        self.ROI_item = QGraphicsRectItem()
        self.ROI_item.setBrush(QBrush(Qt.NoBrush))
        self.ROI_item.setPen(QPen(Qt.white, 0, Qt.DashDotLine))

        # My View
        self.view = Click_QGraphicsView(self.graphicsView)

        # My View Initial Geometry
        # self.view.setGeometry(self.geometry().x() + 10, self.geometry().y() + 39,
        #                       self.geometry().width() - 58, self.geometry().height() - 185)

        #   This part is a forced correction to my coordinates since my view and window
        #   are placed apart. 10 = X coordinate of graphicsView widget from geometry in
        #   the designer, 39 = Y, 58 = difference between window and widget width, 195 =
        #   difference between window and widget height

        self.crop_ratio_w = 1    # The changes in x ratio of window diamension
        self.crop_ratio_h = 1    # The changes in y ratio of window diamension

        # My View Setting Scene
        self.view.ROI_item = self.ROI_item
        self.view.statusChanged.connect(self.LCD_update)

        # My View Attributes
        self.view.setBackgroundRole(QtGui.QPalette.Dark)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setRenderHint(QPainter.Antialiasing, False)
        self.view.setMouseTracking(True)  # Default value is True

    # View Original Image
    def click1(self):
        newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory), "Cropped")
        newpath = os.path.join(newpathdir, os.path.basename(self.path))

        if newpath == self.path:
            statusChanged = pyqtSignal(float, float, float, float)
            with open("Img_files.txt", "r") as file:
                self.img_files = file.read().splitlines()
            file.close()
            for i in range(len(self.img_files)):
                if os.path.basename(self.img_files[i]) == os.path.basename(newpath):
                    newpath = self.img_files[i]
        else:
            newpath = self.path

        self.setImage(newpath)

    # Crop the image when pressing OK button according to selection
    def click2(self):
        crop_rect = self.view.ROI_item.rect().toRect()

        crop_rect = QRect(crop_rect.x() * self.crop_ratio_w, crop_rect.y() * self.crop_ratio_h,
                          crop_rect.width() * self.crop_ratio_w, crop_rect.height() * self.crop_ratio_h)
        #   This is the change in crop region when window size changes

        cropped = self.pixmap.copy(crop_rect)
        newpathdir = os.path.join(os.path.join(self.curr_dir_destination, self.destination_directory), "Cropped")
        if not os.path.isdir(newpathdir):
            os.makedirs(newpathdir)

        newpath = os.path.join(newpathdir, os.path.basename(self.path))

        if os.path.exists(newpath):
            # os.remove(newpath)
            cropped.save(newpath)
        else:
            cropped.save(newpath)

        if not os.path.isfile('Img_files_cropped.txt'):
            copyfile("Img_files.txt",
                     "Img_files_cropped.txt")  # cropped files could have been deleted manually in between

        with open("Img_files_cropped.txt", "r") as file:
            self.img_files = file.read().splitlines()
        file.close()

        for i in range(len(self.img_files)):
            if os.path.basename(self.img_files[i]) == os.path.basename(newpath):
                self.img_files[i] = newpath

        with open("Img_files_cropped.txt", "w") as file:
            for i in range(len(self.img_files)):
                file.write(self.img_files[i])
                file.write("\n")
        file.close()
        self.formLife.emit(True)
        self.close()

    # Close the window
    def click3(self):
        self.view.click = False
        self.view.selection = False
        self.close()

    # This function is invoked when we double click on the label
    def setImage(self, path):
        self.path = path
        self.pixmap = QPixmap(path)
        self.crop_ratio_w = self.pixmap.width() / self.view.width()
        self.crop_ratio_h = self.pixmap.height() / self.view.height()

        smaller_pixmap = self.pixmap.scaled(self.view.width(), self.view.height(),
                                            Qt.IgnoreAspectRatio, Qt.FastTransformation)

        self.image_item.setPixmap(smaller_pixmap)
        self.scene.addItem(self.image_item)
        self.scene.addItem(self.ROI_item)

        self.scene.setSceneRect(0, 0, self.view.width(), self.view.height())
        self.view.setGeometry(0, 0, self.view.width(), self.view.height())

        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setScene(self.scene)

        self.view.setSceneSize()

    # When Escape key is pressed then selection rectangle disappears
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            rect = QRectF(0, 0, 0, 0)
            self.ROI_item.setRect(rect)
        event.accept()

    # When Mouse click is pressed then selection rectangle disappears
    def mousePressEvent(self, event):
        rect = QRectF(0, 0, 0, 0)
        self.ROI_item.setRect(rect)

    # When window is resize, view size is changed and image is set again (refresh)
    def resizeEvent(self, event):
        x_correction = self.frame_1.x() + self.frame_2.x() + self.graphicsView.x()
        y_correction = self.frame_1.y() + self.frame_2.y() + self.graphicsView.y()

        # To force the image set operation only after window has formed completely (frame_1 expands from 0 to 9)
        if self.frame_1.x() > 0:
            self.view.setGeometry(self.geometry().x() + x_correction, self.geometry().y() + y_correction,
                                  self.graphicsView.width(), self.graphicsView.height())
            self.setImage(self.path)

    # Every time window is showed, ROI_Item is reduced to a zero rectangle
    def showEvent(self, event):
        x_correction = self.frame_1.x() + self.frame_2.x() + self.graphicsView.x()
        y_correction = self.frame_1.y() + self.frame_2.y() + self.graphicsView.y()

        # To force the initial view geometry after window has formed completely (frame_1 is 9)
        self.view.setGeometry(self.geometry().x() + x_correction, self.geometry().y() + y_correction,
                              self.graphicsView.width(), self.graphicsView.height())
        self.setImage(self.path)

        rect = QRectF(0, 0, 0, 0)
        self.ROI_item.setRect(rect)

    # Double click on anywhere over the window to get its coordinates
    # def mouseDoubleClickEvent(self, event):
    #     print("point coordinates are: ", event.pos())

    # The x and y cordinates are printed in the LCD widget
    @pyqtSlot(float, float, float, float)
    def LCD_update(self, x1, y1, x2, y2):
        self.lcdNumber_1.display(x1)
        self.lcdNumber_2.display(y1)
        self.lcdNumber_3.display(x2)
        self.lcdNumber_4.display(y2)


# The class where click on View from graphics widget is designed
class Click_QGraphicsView(QGraphicsView):
    statusChanged = pyqtSignal(float, float, float, float)  # To LCD update
    scene_size = (0, 0)  # The initial Scene Size
    ROI_item = None      # The ROI recangle
    event_origin = None  # Origin point which is send to the ROI class
    event_pos = None     # To read click position
    selection = False    # To see if the rectangle selection is on or off
    click = False        # The click is on to determine mouse drag

    def mousePressEvent(self, event):
        self.click = True
        self.selection = True

        if self.selection:
            event_pos = self.mapToScene(event.pos())
            pos = (int(event_pos.x()), int(event_pos.y()))
            if 0 <= pos[0] < self.scene_size[0] and 0 <= pos[1] < self.scene_size[1]:
                self.event_origin = event_pos
            else:
                self.event_origin = None
            self.click = True
        else:
            QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):

        if self.event and self.click:
            self.selection = True

        event_pos = self.mapToScene(event.pos())
        if self.selection and self.click:
            if self.event_origin:
                self.statusChanged.emit(self.event_origin.x(), self.event_origin.y(), event_pos.x(), event_pos.y())

                if event_pos.x() < 0:
                    event_pos.setX(0)
                elif event_pos.x() > self.scene_size[0] - 1:
                    event_pos.setX(self.scene_size[0] - 1)
                if event_pos.y() < 0:
                    event_pos.setY(0)
                elif event_pos.y() > self.scene_size[1] - 1:
                    event_pos.setY(self.scene_size[1] - 1)
                self.ROI_item.setRect(QRectF(self.event_origin, event_pos).normalized())
            else:
                pass
        else:
            QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.selection:
            self.click = False
            if self.event_origin:
                self.event_origin = None
        else:
            QGraphicsView.mouseReleaseEvent(self, event)

    def setSceneSize(self):
        rect = self.scene().sceneRect()
        self.scene_size = (rect.width(), rect.height())
