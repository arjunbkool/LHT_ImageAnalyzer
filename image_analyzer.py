# -*- coding: utf-8 -*-
"""
Created on Thu Mar  8 14:41:16 2019

@author: U724965
"""

import collections
import os
import imghdr
import subprocess

import xlrd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu, QAction, QMainWindow, QTreeWidgetItem

import Ui_ImageAnalyze
import common

# import imglyb


# Functions defined in common class
show_message = common.show_message
view_file_location = common.view_file_location
view_image = common.view_image
del_folder = common.del_folder


# The class to do the Image Tree view and potentially passing arguements to imageJ (Fourth Window)
class ImageAnalyze(Ui_ImageAnalyze.Ui_MainWindow, QMainWindow):

    def __init__(self, parent=None):

        # No initial knowledge of our directories
        self.destination_directory = None
        self.source_directory = None
        self.curr_dir_source = None
        self.curr_dir_destination = None
        self.newpathdir = None

        global workbook_read
        super(ImageAnalyze, self).__init__()
        self.setupUi(self)
        self.treeWidget.clear()

        # Double Click and Right Click Actions in Tree
        self.treeWidget.itemDoubleClicked.connect(self.view_image_tree)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.on_context_menu)
        self.popMenu = QMenu(self)
        self.action1 = QAction("Open Folder/File")
        self.action2 = QAction("Open With ImageJ")
        self.action1.triggered.connect(self.open_folder)
        self.action2.triggered.connect(self.send_to_imageJ)

    # Back button
    def click1(self):
        show_message("Do you wish go back?", True, "Yes",
                     common.btn1_fun, True, "No", lambda: None)

        if common.show_message_btn1:
            self.treeWidget.clear()
            self.close()

    # The tree is updated from excel sheet
    def tree_update(self):

        # Read Excel sheet to update tree
        try:
            workbook_read = xlrd.open_workbook('image_data.xlsx')
        except:
            show_message("xlsx file cannot be opened, check if the workbook is used "
                         "by another application")

        sheets = workbook_read.sheets()
        worksheet = sheets[0]
        items = []
        self.treeWidget.headerItem().setText(0, "Image Files")
        self.treeWidget.setColumnCount(1)

        source = QTreeWidgetItem(["Source"])
        destination = QTreeWidgetItem(["Destination"])

        # Adding image children to Source
        for col in range(worksheet.ncols):
            for row in range(worksheet.nrows):
                if col is 0 and row > 0:
                    source_child = QTreeWidgetItem([str(worksheet.cell_value(row, col))])
                    source.addChild(source_child)

        master_dict = collections.defaultdict(list)
        reference_dict = collections.defaultdict(list)

        # Updating the best location to a dictionary (priority 1: after enhanced, 2: After Crop, 3: Original)
        for row in range(1, worksheet.nrows):
            best = None
            for col in range(0, 6):
                if not str(worksheet.cell(row, col).value).startswith("<No"):
                    if col is not 3 and col is not 2 and col is not 1:
                        best = worksheet.cell(row, col).value

            # Condition when there is OCR test conducted and destination is split between folders
            if worksheet.cell(1, 3).value is not "":
                key = '{}'.format(str(worksheet.cell_value(row, 3)))
                if key == "X0":
                    key = str("Unknown")
            # Condition when there are no magnification folders
            else:
                key = "Folder"

            reference_dict[str(key)].append(os.path.split(os.path.dirname(best))[1])
            master_dict[str(key)].append(best)

        # Adding image children to folder child and then to Destination
        for i in reference_dict:
            destination_child = QTreeWidgetItem([i])

            destination_child_child_enh = QTreeWidgetItem(["Enhanced"])
            destination_child_child_cro = QTreeWidgetItem(["Cropped"])
            destination_child_child_ori = QTreeWidgetItem(["Original"])

            for j in range(len(reference_dict[i])):
                destination_child_child_child = QTreeWidgetItem([master_dict[i][j]])

                if reference_dict[i][j] == "Enhanced":
                    destination_child_child_enh.addChild(destination_child_child_child)
                elif reference_dict[i][j] == "Cropped":
                    destination_child_child_cro.addChild(destination_child_child_child)
                else:
                    destination_child_child_ori.addChild(destination_child_child_child)

            destination_child.addChild(destination_child_child_enh)
            destination_child.addChild(destination_child_child_cro)
            destination_child.addChild(destination_child_child_ori)
            destination.addChild(destination_child)

        self.treeWidget.addTopLevelItem(source)
        self.treeWidget.addTopLevelItem(destination)

        # Update tree with Finished (ImageJ Ready) Folder
        finished_child_child = None
        finished_child = None
        finished = QTreeWidgetItem(["Finished (ImageJ ready)"])

        # Adding child directories
        for root, dirs, files in os.walk(os.path.join(os.path.join(self.curr_dir_destination,
                                                                   self.destination_directory), "Finished")):
            for dir in dirs:
                if "X" in dir:
                    finished_child = QTreeWidgetItem([dir])
                    finished.addChild(finished_child)

                    # Adding child_child files to child directories
                    for root_dir, dirs_dir, files_dir in os.walk(os.path.join(root, dir)):
                        for name_dir in files_dir:
                            finished_child_child = QTreeWidgetItem([os.path.join(root_dir, name_dir)])
                            finished_child.addChild(finished_child_child)

        # Adding child directories to main directory
        if finished_child_child is not None and finished_child is not None:
            self.treeWidget.addTopLevelItem(finished)

    # What actions are displayed on right click of an item
    def on_context_menu(self, point):
        text = None
        self.popMenu.removeAction(self.action1)
        self.popMenu.removeAction(self.action2)

        for i in self.treeWidget.selectedIndexes():
            text = i.data(Qt.DisplayRole)

        try:
            check = imghdr.what(text)
        except:
            check = None

        parent = self.treeWidget.currentItem().parent()
        parent_text = "None"
        if parent is not None:
            parent_text = parent.text(self.treeWidget.currentColumn())

        if text == "Source":
            self.popMenu.addAction(self.action1)
            pass
        elif text == "Destination":
            self.popMenu.addAction(self.action1)
        elif text == "Finished (ImageJ ready)":
            self.popMenu.addAction(self.action1)
        elif parent_text == "Destination":
            self.popMenu.addAction(self.action1)
        elif text == "Cropped":
            self.popMenu.addAction(self.action1)
        elif text == "Enhanced":
            self.popMenu.addAction(self.action1)
        elif text == "Original":
            self.popMenu.addAction(self.action1)
        elif parent_text == "Finished (ImageJ ready)":
            self.popMenu.addAction(self.action1)
            self.popMenu.addAction(self.action2)
        elif os.path.exists(text) and check is not None:
            self.popMenu.addAction(self.action1)
            self.popMenu.addAction(self.action2)

        self.popMenu.exec_(self.treeWidget.mapToGlobal(point))

    # The action to open folder/file
    def open_folder(self):
        text = None
        path = None
        for i in self.treeWidget.selectedIndexes():
            text = i.data(Qt.DisplayRole)

        parent = self.treeWidget.currentItem().parent()
        parent_text = "None"
        if parent is not None:
            parent_text = parent.text(self.treeWidget.currentColumn())

        try:
            check = imghdr.what(text)
        except:
            check = None

        if os.path.exists(text) and check is not None:
            path = text
        elif text == "Source":
            path = os.path.join(self.curr_dir_source, self.source_directory)
        elif text == "Destination":
            path = os.path.join(self.curr_dir_destination, self.destination_directory, )
        elif text == "Folder":
            path = self.curr_dir_destination
        elif text == "Finished (ImageJ ready)":
            path = os.path.join(self.curr_dir_destination, self.destination_directory, "Finished")

        elif "X" in text:
            if parent_text == "Destination":
                path = os.path.join(self.curr_dir_destination, self.destination_directory, text)
            elif parent_text == "Finished (ImageJ ready)":
                path = os.path.join(self.curr_dir_destination, self.destination_directory, "Finished", text)

        elif "Unknown" in text:
            if parent_text == "Destination":
                path = os.path.join(self.curr_dir_destination, self.destination_directory, "X_Unknown")
            elif parent_text == "Finished (ImageJ ready)":
                path = os.path.join(self.curr_dir_destination, self.destination_directory, "Finished", "X_Unknown")

        elif "Cropped" in text:
            path = os.path.join(self.curr_dir_destination, self.destination_directory, "Cropped")
        elif "Enhanced" in text:
            path = os.path.join(self.curr_dir_destination, self.destination_directory, "Enhanced")
        elif "Original" in text:
            path = os.path.join(self.curr_dir_destination, self.destination_directory)

        try:
            os.startfile(path)
        except:
            pass

    # ImageJ operations
    def send_to_imageJ(self):
        path_to_imageJ = os.path.join(os.getcwd(), "Application\\Fiji.app\\ImageJ-win64.exe")  # Location of ImageJ
        path_to_macro = os.path.join(os.getcwd(), "Application\\macro.ijm")
        path_to_arg = os.path.join(os.getcwd(),
                                   "Application\\arguments.txt")  # Location of the first image file of my sequence

        text = "None"
        path = "None"
        folder_name = "None"
        folder = "Yes"
        No_of_files = 1
        scale_text = 0
        scale_length = 0

        for i in self.treeWidget.selectedIndexes():
            text = i.data(Qt.DisplayRole)

        try:
            check = imghdr.what(text)
        except:
            check = None
        if os.path.exists(text) and check is not None:
            folder = "No"
            path = text

        elif "X" in text:  # This means any selection magnification heading with X
            path = os.path.join(self.curr_dir_destination, self.destination_directory, "Finished", text)
            folder_name = os.path.basename(path)
        elif "Unknown" in text:
            path = os.path.join(self.curr_dir_destination, self.destination_directory, "Finished", "X_Unknown")
            folder_name = "X0"

        try:
            workbook_read = xlrd.open_workbook('image_data.xlsx')
        except:
            show_message("xlsx file cannot be handled, check if the workbook is used "
                         "by another application")

        sheets = workbook_read.sheets()
        worksheet = sheets[0]

        if folder is "No":  # It is an image file
            for row in range(worksheet.nrows):
                for col in range(worksheet.ncols):
                    if col is 0 or col is 4 or col is 5:
                        if os.path.basename(path) == os.path.basename(str(worksheet.cell_value(row, col))):
                            scale_text = worksheet.cell_value(row, 1)
                            scale_length = worksheet.cell_value(row, 2)

        if folder is "Yes":  # It is an image folder
            path_check = path
            No_of_files = 0
            for root, dirs, files in os.walk(path_check):
                for name in files:
                    if name is not "thumbs.db":
                        path = os.path.join(root, name)         # This gets us the last file name within the folder
                        No_of_files = No_of_files + 1

            for row in range(worksheet.nrows):
                for col in range(worksheet.ncols):
                    if col is 3:
                        if folder_name == str(worksheet.cell_value(row, col)):
                            scale_text = worksheet.cell_value(row, 1)
                            scale_length = worksheet.cell_value(row, 2)
                            break

        file = open(path_to_arg, "w")

        file.write(folder)
        file.write("\n")
        file.write(str(No_of_files))
        file.write("\n")
        file.write(path)
        file.write("\n")
        if scale_text:
            file.write(str(scale_text))
        else:
            file.write("0")
        file.write("\n")
        if scale_length:
            file.write(str(scale_length))
        else:
            file.write("0")
        file.write("\n")

        file.write("\n\n*** The parameters for imageJ macro are: "
                   "\n1) File/Folder (Yes = Folder, No = File) "
                   "\n2) No: of Files ( = 1 if its a single file)"
                   "\n2) Name of file (Or starting file of the sequence) "
                   "\n3) Corresponding magnification scale - text"
                   "\n4) Corresponding magnification scale - length ***")
        file.close()

        if file.closed is True:
            cmd = [path_to_imageJ, "-macro", path_to_macro, path_to_arg]
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            if p.wait() > 0:
                print("Error")
            else:
                print("Success")

    # To view the tree widget file image upon double click
    def view_image_tree(self):

        for i in self.treeWidget.selectedIndexes():
            text = i.data(Qt.DisplayRole)

        try:
            check = imghdr.what(text)
        except:
            check = None
        if os.path.exists(text) and check is not None:
            view_image(text)
