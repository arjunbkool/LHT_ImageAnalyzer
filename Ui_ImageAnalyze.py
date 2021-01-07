# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Ui_ImageAnalyze.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(893, 775)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pushButton_1 = QtWidgets.QPushButton(self.frame)
        self.pushButton_1.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_1.setMaximumSize(QtCore.QSize(150, 50))
        self.pushButton_1.setObjectName("pushButton_1")
        self.gridLayout_2.addWidget(self.pushButton_1, 2, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 2, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.frame)
        font = QtGui.QFont()
        font.setFamily("Palatino Linotype")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAutoFillBackground(True)
        self.label.setInputMethodHints(QtCore.Qt.ImhNone)
        self.label.setLineWidth(1)
        self.label.setTextFormat(QtCore.Qt.AutoText)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 3)
        self.treeWidget = QtWidgets.QTreeWidget(self.frame)
        self.treeWidget.setAutoFillBackground(False)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.gridLayout_2.addWidget(self.treeWidget, 1, 0, 1, 4)
        self.pushButton_2 = QtWidgets.QPushButton(self.frame)
        self.pushButton_2.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_2.setMaximumSize(QtCore.QSize(150, 50))
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_2.addWidget(self.pushButton_2, 2, 3, 1, 1)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionChange_Source_Directory = QtWidgets.QAction(MainWindow)
        self.actionChange_Source_Directory.setObjectName("actionChange_Source_Directory")
        self.actionChange_Destination_Directory = QtWidgets.QAction(MainWindow)
        self.actionChange_Destination_Directory.setObjectName("actionChange_Destination_Directory")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "LHT-Image Analyzer"))
        self.pushButton_1.setText(_translate("MainWindow", "Back"))
        self.label.setText(_translate("MainWindow", "Image Tree"))
        self.pushButton_2.setText(_translate("MainWindow", "Finish"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionChange_Source_Directory.setText(_translate("MainWindow", "Change Source Directory"))
        self.actionChange_Destination_Directory.setText(_translate("MainWindow", "Change Destination Directory"))

import icons_ImageSort_rc
