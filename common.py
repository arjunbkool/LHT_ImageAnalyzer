import math
import os

import cv2
import numpy as np
from PyQt5.QtGui import QImage, qRgb
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt

curr_dir = os.getcwd()
gray_color_table = [qRgb(i, i, i) for i in range(256)]

global show_message_btn1
global show_message_btn2
global show_message_btn3


def NumpyToQImage(im):
    qim = QImage()
    if im is None:
        return qim
    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888)
            elif im.shape[2] == 4:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32)
    return qim


def crop_img(img, percent):
    x1, y1 = 0, 0
    x2, y2 = img.shape[1], img.shape[0]
    w, h = x2 - x1, y2 - y1

    w_curr, h_curr = int(w * math.sqrt(percent * 0.01)), int(h * math.sqrt(percent * 0.01))
    kx, ky = (w - w_curr) * 0.5, (h - h_curr) * 0.5
    x3, y3 = int(x1 + kx), int(y1 + ky)

    img_cropped = img[int(y3):int(y3 + h_curr), int(x3):int(x3 + w_curr)]
    return img_cropped


def view_image(path, time=0,
               name="LHT Image Analysis Tool"):  # to view an image, default value of time is till key press(0)

    cv2.namedWindow(name, cv2.WINDOW_NORMAL)

    if isinstance(path, str):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    else:
        img = path

    height = img.shape[0]
    width = img.shape[1]
    ratio = height / width
    im_resize = cv2.resize(img, (960, int(960 / ratio)))
    cv2.imshow(name, im_resize)
    time = int(time * 1000)
    cv2.waitKey(time)
    cv2.destroyAllWindows()


def view_file_location(img_location):
    img = cv2.imread(img_location, cv2.IMREAD_GRAYSCALE)
    view_image(img)


def show_message(message, btn1=False, btn1_name="Button1", btn1_fun=lambda: None,
                 btn2=False, btn2_name="Button2", btn2_fun=lambda: None,
                 btn3=False, btn3_name="Button3", btn3_fun=lambda: None):  # Default layout has an OK Button

    msg_box = QMessageBox()
    msg_box.raise_()
    msg_box.setWindowFlags(Qt.WindowStaysOnTopHint)

    msg_box.setText(message)

    if btn1:
        btn1 = msg_box.addButton(btn1_name, QMessageBox.YesRole)
        btn1.clicked.connect(btn1_fun)

    if btn2:
        btn2 = msg_box.addButton(btn2_name, QMessageBox.NoRole)
        btn2.clicked.connect(btn2_fun)

    if btn3:
        btn3 = msg_box.addButton(btn3_name, QMessageBox.RejectRole)
        btn3.clicked.connect(btn3_fun)

    msg_box.exec_()


def btn1_fun():
    global show_message_btn1
    show_message_btn1 = True


def btn2_fun():
    global show_message_btn2
    show_message_btn2 = True


def btn3_fun():
    global show_message_btn3
    show_message_btn3 = True


def del_folder(folder, data_files, data_file_text=None):  # to delete the files in the text file in a list and folder
    new_path = os.path.join(curr_dir, folder)
    new_path_file = os.path.join(curr_dir, data_file_text)

    if not os.path.isdir(new_path):
        return 0

    else:
        if os.path.isfile(new_path_file):
            with open(new_path_file) as file:
                data_files = file.read().splitlines()

        for root, dirs, files in os.walk(new_path):
            for name in files:
                if any(os.path.join(root, name) in s for s in data_files):
                    data_files.remove(os.path.join(root, name))

                if os.path.isfile(os.path.join(root, name)):
                    os.remove(os.path.join(root, name))

        os.rmdir(new_path)
        return 1
