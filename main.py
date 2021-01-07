# -*- coding: utf-8 -*-
"""
Created on Mon Jan 14 10:45:15 2019
@author: U724965
"""

import atexit
import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMessageBox

import common
import image_analyzer
import image_crop
import image_exposure
import image_sort

try:
    os.startfile(path)
except:
    pass


# The manager of windows and what happens when Next and Back button are pressed
class Manager:

    def __init__(self):
        self.first = image_sort.ImageSort()
        self.second = image_crop.ImageCrop()
        self.third = image_exposure.ImageExposure()
        self.fourth = image_analyzer.ImageAnalyze()
        self.first.show()

        self.first.pushButton_6.clicked.connect(partial(self.function, "gotoCrop"))
        self.second.pushButton_5.clicked.connect(partial(self.function, "gotoExposure"))
        self.third.pushButton_5.clicked.connect(partial(self.function, "gotoAnalysis"))
        self.fourth.pushButton_2.clicked.connect(partial(self.function, "finishProgram"))

        self.second.pushButton_4.clicked.connect(partial(self.function, "backtoSort"))
        self.third.pushButton_4.clicked.connect(partial(self.function, "backtoCrop"))
        self.fourth.pushButton_1.clicked.connect(partial(self.function, "backtoExposure"))

    def function(self, task):
        if task == "gotoCrop":
            self.second.label_1.clear()
            self.second.label_2.clear()
            self.second.label_3.clear()
            self.second.label_4.clear()
            self.second.label_5.clear()
            self.second.label_6.clear()

            self.second.pushButton_1.setText("Show Images")
            self.second.refresh = False
            self.second.formCall = False

            self.second.pushButton_2.setEnabled(False)
            self.second.pushButton_3.setEnabled(False)

            self.first.click6()
            if common.show_message_btn1:
                self.second.source_directory = self.first.source_directory
                self.second.destination_directory = self.first.destination_directory
                self.second.curr_dir_source = self.first.curr_dir_source
                self.second.curr_dir_destination = self.first.curr_dir_destination
                self.second.show()

        if task == "gotoExposure":
            self.third.label_1.clear()
            self.third.label_2.clear()
            self.third.label_3.clear()
            self.third.label_4.clear()
            self.third.label_5.clear()
            self.third.label_6.clear()

            self.second.click5()
            if common.show_message_btn1:
                self.third.source_directory = self.second.source_directory
                self.third.destination_directory = self.second.destination_directory
                self.third.curr_dir_source = self.second.curr_dir_source
                self.third.curr_dir_destination = self.second.curr_dir_destination
                self.third.show()

        if task == "gotoAnalysis":

            self.third.click7()
            if common.show_message_btn1:
                self.fourth.source_directory = self.third.source_directory
                self.fourth.destination_directory = self.third.destination_directory
                self.fourth.curr_dir_source = self.third.curr_dir_source
                self.fourth.curr_dir_destination = self.third.curr_dir_destination
                self.fourth.show()
                self.fourth.tree_update()

        if task == "finishProgram":
            self.first.close()
            self.second.close()
            self.third.close()
            self.fourth.close()

        if task == "backtoSort":
            self.first.listWidget.clear()
            self.second.click4()
            if common.show_message_btn1:
                self.first.show()

        if task == "backtoCrop":
            self.second.label_1.clear()
            self.second.label_2.clear()
            self.second.label_3.clear()
            self.second.label_4.clear()
            self.second.label_5.clear()
            self.second.label_6.clear()

            self.second.pushButton_1.setText("Show Images")
            self.second.refresh = False
            self.second.formCall = False

            self.second.pushButton_2.setEnabled(False)
            self.second.pushButton_3.setEnabled(False)

            self.third.click6()
            if common.show_message_btn1:
                self.second.show()

        if task == "backtoExposure":
            self.third.label_1.clear()
            self.third.label_2.clear()
            self.third.label_3.clear()
            self.third.label_4.clear()
            self.third.label_5.clear()
            self.third.label_6.clear()

            self.fourth.click1()
            if common.show_message_btn1:
                self.third.show()


def catch_exceptions(t, val, tb):
    QMessageBox.critical(None,
                         "An exception was raised",
                         "Exception type: {}".format(t))
    old_hook(t, val, tb)


old_hook = sys.excepthook
sys.excepthook = catch_exceptions

try:
    with open("counterfile") as infile:
        _count = int(infile.read())
except FileNotFoundError:
    _count = 0


def incrcounter(n):
    global _count
    _count = _count + n


def savecounter():
    with open("counterfile", "w") as outfile:
        outfile.write("%d" % _count)


atexit.register(savecounter)


def main():
    app = QApplication(sys.argv)
    manager = Manager()
    app.exec_()


if __name__ == '__main__': main()
