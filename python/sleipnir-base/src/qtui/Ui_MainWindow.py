# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1090, 838)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, -1, 6, -1)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_top = QHBoxLayout()
        self.horizontalLayout_top.setObjectName(u"horizontalLayout_top")
        self.horizontalLayout_top.setContentsMargins(-1, 0, 0, 0)
        self.verticalLayout_video_1 = QVBoxLayout()
        self.verticalLayout_video_1.setObjectName(u"verticalLayout_video_1")
        self.verticalLayout_video_1.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_video_1_top = QHBoxLayout()
        self.horizontalLayout_video_1_top.setObjectName(u"horizontalLayout_video_1_top")
        self.label_video1_online = QLabel(self.centralwidget)
        self.label_video1_online.setObjectName(u"label_video1_online")
        self.label_video1_online.setStyleSheet(u"font-size: 20px;")

        self.horizontalLayout_video_1_top.addWidget(self.label_video1_online)

        self.pushButton_video1_align = QPushButton(self.centralwidget)
        self.pushButton_video1_align.setObjectName(u"pushButton_video1_align")

        self.horizontalLayout_video_1_top.addWidget(self.pushButton_video1_align)

        self.horizontalLayout_video_1_top.setStretch(0, 1)

        self.verticalLayout_video_1.addLayout(self.horizontalLayout_video_1_top)

        self.label_video1 = QLabel(self.centralwidget)
        self.label_video1.setObjectName(u"label_video1")
        self.label_video1.setFrameShape(QFrame.Box)
        self.label_video1.setScaledContents(True)

        self.verticalLayout_video_1.addWidget(self.label_video1)

        self.horizontalLayout_video_1_slider = QHBoxLayout()
        self.horizontalLayout_video_1_slider.setObjectName(u"horizontalLayout_video_1_slider")
        self.horizontalLayout_video_1_slider.setContentsMargins(-1, 10, -1, 10)
        self.slider_video1 = QSlider(self.centralwidget)
        self.slider_video1.setObjectName(u"slider_video1")
        self.slider_video1.setOrientation(Qt.Horizontal)

        self.horizontalLayout_video_1_slider.addWidget(self.slider_video1)

        self.label_time_video1 = QLabel(self.centralwidget)
        self.label_time_video1.setObjectName(u"label_time_video1")

        self.horizontalLayout_video_1_slider.addWidget(self.label_time_video1)


        self.verticalLayout_video_1.addLayout(self.horizontalLayout_video_1_slider)

        self.horizontalLayout_video_1_buttons = QHBoxLayout()
        self.horizontalLayout_video_1_buttons.setSpacing(0)
        self.horizontalLayout_video_1_buttons.setObjectName(u"horizontalLayout_video_1_buttons")
        self.horizontalLayout_video_1_buttons.setContentsMargins(-1, 0, -1, -1)
        self.pushbutton_video1_find = QPushButton(self.centralwidget)
        self.pushbutton_video1_find.setObjectName(u"pushbutton_video1_find")

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_find)

        self.horizontalSpacer_2 = QSpacerItem(16, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_video_1_buttons.addItem(self.horizontalSpacer_2)

        self.pushbutton_video1_playbackward = QPushButton(self.centralwidget)
        self.pushbutton_video1_playbackward.setObjectName(u"pushbutton_video1_playbackward")
        self.pushbutton_video1_playbackward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_playbackward)

        self.pushbutton_video1_backstep = QPushButton(self.centralwidget)
        self.pushbutton_video1_backstep.setObjectName(u"pushbutton_video1_backstep")
        self.pushbutton_video1_backstep.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_backstep)

        self.pushbutton_video1_pause = QPushButton(self.centralwidget)
        self.pushbutton_video1_pause.setObjectName(u"pushbutton_video1_pause")
        self.pushbutton_video1_pause.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_pause)

        self.pushbutton_video1_forwardstep = QPushButton(self.centralwidget)
        self.pushbutton_video1_forwardstep.setObjectName(u"pushbutton_video1_forwardstep")
        self.pushbutton_video1_forwardstep.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_forwardstep)

        self.pushbutton_video1_playforward = QPushButton(self.centralwidget)
        self.pushbutton_video1_playforward.setObjectName(u"pushbutton_video1_playforward")
        self.pushbutton_video1_playforward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_playforward)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_video_1_buttons.addItem(self.horizontalSpacer_3)

        self.pushbutton_video1_copy = QPushButton(self.centralwidget)
        self.pushbutton_video1_copy.setObjectName(u"pushbutton_video1_copy")

        self.horizontalLayout_video_1_buttons.addWidget(self.pushbutton_video1_copy)

        self.horizontalLayout_video_1_buttons.setStretch(7, 1)

        self.verticalLayout_video_1.addLayout(self.horizontalLayout_video_1_buttons)

        self.verticalLayout_video_1.setStretch(1, 1)

        self.horizontalLayout_top.addLayout(self.verticalLayout_video_1)

        self.verticalLayout_groundlevel = QVBoxLayout()
        self.verticalLayout_groundlevel.setObjectName(u"verticalLayout_groundlevel")
        self.verticalLayout_groundlevel.setContentsMargins(-1, -1, 0, -1)
        self.verticalSpacer_4 = QSpacerItem(1, 34, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout_groundlevel.addItem(self.verticalSpacer_4)

        self.verticalSlider_groundlevel = QSlider(self.centralwidget)
        self.verticalSlider_groundlevel.setObjectName(u"verticalSlider_groundlevel")
        self.verticalSlider_groundlevel.setMinimum(1)
        self.verticalSlider_groundlevel.setMaximum(480)
        self.verticalSlider_groundlevel.setValue(400)
        self.verticalSlider_groundlevel.setOrientation(Qt.Vertical)
        self.verticalSlider_groundlevel.setInvertedAppearance(True)

        self.verticalLayout_groundlevel.addWidget(self.verticalSlider_groundlevel)

        self.verticalSpacer_3 = QSpacerItem(1, 80, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout_groundlevel.addItem(self.verticalSpacer_3)


        self.horizontalLayout_top.addLayout(self.verticalLayout_groundlevel)

        self.verticalLayout_video_2 = QVBoxLayout()
        self.verticalLayout_video_2.setObjectName(u"verticalLayout_video_2")
        self.horizontalLayout_video_2_top = QHBoxLayout()
        self.horizontalLayout_video_2_top.setObjectName(u"horizontalLayout_video_2_top")
        self.label_video2_online = QLabel(self.centralwidget)
        self.label_video2_online.setObjectName(u"label_video2_online")
        self.label_video2_online.setStyleSheet(u"font-size: 20px;")

        self.horizontalLayout_video_2_top.addWidget(self.label_video2_online)

        self.pushButton_video2_align = QPushButton(self.centralwidget)
        self.pushButton_video2_align.setObjectName(u"pushButton_video2_align")

        self.horizontalLayout_video_2_top.addWidget(self.pushButton_video2_align)

        self.horizontalLayout_video_2_top.setStretch(0, 1)

        self.verticalLayout_video_2.addLayout(self.horizontalLayout_video_2_top)

        self.label_video2 = QLabel(self.centralwidget)
        self.label_video2.setObjectName(u"label_video2")
        self.label_video2.setFrameShape(QFrame.Box)
        self.label_video2.setScaledContents(True)

        self.verticalLayout_video_2.addWidget(self.label_video2)

        self.horizontalLayout_video_2_slider = QHBoxLayout()
        self.horizontalLayout_video_2_slider.setObjectName(u"horizontalLayout_video_2_slider")
        self.horizontalLayout_video_2_slider.setContentsMargins(-1, 10, -1, 10)
        self.slider_video2 = QSlider(self.centralwidget)
        self.slider_video2.setObjectName(u"slider_video2")
        self.slider_video2.setOrientation(Qt.Horizontal)

        self.horizontalLayout_video_2_slider.addWidget(self.slider_video2)

        self.label_time_video2 = QLabel(self.centralwidget)
        self.label_time_video2.setObjectName(u"label_time_video2")

        self.horizontalLayout_video_2_slider.addWidget(self.label_time_video2)


        self.verticalLayout_video_2.addLayout(self.horizontalLayout_video_2_slider)

        self.horizontalLayout_video_2_buttons = QHBoxLayout()
        self.horizontalLayout_video_2_buttons.setSpacing(0)
        self.horizontalLayout_video_2_buttons.setObjectName(u"horizontalLayout_video_2_buttons")
        self.horizontalLayout_video_2_buttons.setContentsMargins(-1, 0, -1, 0)
        self.pushbutton_video2_copy = QPushButton(self.centralwidget)
        self.pushbutton_video2_copy.setObjectName(u"pushbutton_video2_copy")

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_copy)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_video_2_buttons.addItem(self.horizontalSpacer_4)

        self.pushbutton_video2_find = QPushButton(self.centralwidget)
        self.pushbutton_video2_find.setObjectName(u"pushbutton_video2_find")

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_find)

        self.horizontalSpacer_5 = QSpacerItem(16, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_video_2_buttons.addItem(self.horizontalSpacer_5)

        self.pushbutton_video2_playbackward = QPushButton(self.centralwidget)
        self.pushbutton_video2_playbackward.setObjectName(u"pushbutton_video2_playbackward")
        self.pushbutton_video2_playbackward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_playbackward)

        self.pushbutton_video2_backstep = QPushButton(self.centralwidget)
        self.pushbutton_video2_backstep.setObjectName(u"pushbutton_video2_backstep")
        self.pushbutton_video2_backstep.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_backstep)

        self.pushbutton_video2_pause = QPushButton(self.centralwidget)
        self.pushbutton_video2_pause.setObjectName(u"pushbutton_video2_pause")
        self.pushbutton_video2_pause.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_pause)

        self.pushbutton_video2_forwardstep = QPushButton(self.centralwidget)
        self.pushbutton_video2_forwardstep.setObjectName(u"pushbutton_video2_forwardstep")
        self.pushbutton_video2_forwardstep.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_forwardstep)

        self.pushbutton_video2_playforward = QPushButton(self.centralwidget)
        self.pushbutton_video2_playforward.setObjectName(u"pushbutton_video2_playforward")
        self.pushbutton_video2_playforward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.pushbutton_video2_playforward)

        self.horizontalLayout_video_2_buttons.setStretch(1, 1)

        self.verticalLayout_video_2.addLayout(self.horizontalLayout_video_2_buttons)

        self.verticalLayout_video_2.setStretch(1, 1)

        self.horizontalLayout_top.addLayout(self.verticalLayout_video_2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalSpacer = QSpacerItem(170, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.label_distance = QLabel(self.centralwidget)
        self.label_distance.setObjectName(u"label_distance")

        self.verticalLayout_4.addWidget(self.label_distance)

        self.lineEdit_distance = QLineEdit(self.centralwidget)
        self.lineEdit_distance.setObjectName(u"lineEdit_distance")

        self.verticalLayout_4.addWidget(self.lineEdit_distance)

        self.checkBox_live = QCheckBox(self.centralwidget)
        self.checkBox_live.setObjectName(u"checkBox_live")
        self.checkBox_live.setChecked(True)

        self.verticalLayout_4.addWidget(self.checkBox_live)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.checkBox_motion_track = QCheckBox(self.centralwidget)
        self.checkBox_motion_track.setObjectName(u"checkBox_motion_track")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_motion_track.sizePolicy().hasHeightForWidth())
        self.checkBox_motion_track.setSizePolicy(sizePolicy)
        self.checkBox_motion_track.setMinimumSize(QSize(0, 0))
        self.checkBox_motion_track.setChecked(True)

        self.horizontalLayout_3.addWidget(self.checkBox_motion_track)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.listView_anouncements = QListView(self.centralwidget)
        self.listView_anouncements.setObjectName(u"listView_anouncements")
        self.listView_anouncements.setMinimumSize(QSize(0, 250))
        self.listView_anouncements.setMaximumSize(QSize(16777215, 400))

        self.verticalLayout_4.addWidget(self.listView_anouncements)

        self.pushButton_remove_announcement = QPushButton(self.centralwidget)
        self.pushButton_remove_announcement.setObjectName(u"pushButton_remove_announcement")

        self.verticalLayout_4.addWidget(self.pushButton_remove_announcement)

        self.label_average = QLabel(self.centralwidget)
        self.label_average.setObjectName(u"label_average")
        self.label_average.setStyleSheet(u"font-size: 24px")

        self.verticalLayout_4.addWidget(self.label_average)

        self.verticalSpacer_2 = QSpacerItem(170, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.label_flightnumber = QLabel(self.centralwidget)
        self.label_flightnumber.setObjectName(u"label_flightnumber")

        self.verticalLayout_4.addWidget(self.label_flightnumber)

        self.gridLayout_flights = QGridLayout()
        self.gridLayout_flights.setObjectName(u"gridLayout_flights")
        self.gridLayout_flights.setHorizontalSpacing(0)
        self.gridLayout_flights.setVerticalSpacing(15)
        self.radioButton_flight_1 = QRadioButton(self.centralwidget)
        self.radioButton_flight_1.setObjectName(u"radioButton_flight_1")
        self.radioButton_flight_1.setMaximumSize(QSize(16777215, 16777215))

        self.gridLayout_flights.addWidget(self.radioButton_flight_1, 1, 0, 1, 1)

        self.radioButton_flight_4 = QRadioButton(self.centralwidget)
        self.radioButton_flight_4.setObjectName(u"radioButton_flight_4")

        self.gridLayout_flights.addWidget(self.radioButton_flight_4, 1, 3, 1, 1)

        self.radioButton_flight_3 = QRadioButton(self.centralwidget)
        self.radioButton_flight_3.setObjectName(u"radioButton_flight_3")

        self.gridLayout_flights.addWidget(self.radioButton_flight_3, 1, 2, 1, 1)

        self.radioButton_flight_2 = QRadioButton(self.centralwidget)
        self.radioButton_flight_2.setObjectName(u"radioButton_flight_2")

        self.gridLayout_flights.addWidget(self.radioButton_flight_2, 1, 1, 1, 1)

        self.radioButton_flight_20 = QRadioButton(self.centralwidget)
        self.radioButton_flight_20.setObjectName(u"radioButton_flight_20")

        self.gridLayout_flights.addWidget(self.radioButton_flight_20, 5, 3, 1, 1)

        self.radioButton_flight_19 = QRadioButton(self.centralwidget)
        self.radioButton_flight_19.setObjectName(u"radioButton_flight_19")

        self.gridLayout_flights.addWidget(self.radioButton_flight_19, 5, 2, 1, 1)

        self.radioButton_flight_18 = QRadioButton(self.centralwidget)
        self.radioButton_flight_18.setObjectName(u"radioButton_flight_18")

        self.gridLayout_flights.addWidget(self.radioButton_flight_18, 5, 1, 1, 1)

        self.radioButton_flight_5 = QRadioButton(self.centralwidget)
        self.radioButton_flight_5.setObjectName(u"radioButton_flight_5")
        self.radioButton_flight_5.setMaximumSize(QSize(16777215, 16777215))

        self.gridLayout_flights.addWidget(self.radioButton_flight_5, 2, 0, 1, 1)

        self.radioButton_flight_6 = QRadioButton(self.centralwidget)
        self.radioButton_flight_6.setObjectName(u"radioButton_flight_6")

        self.gridLayout_flights.addWidget(self.radioButton_flight_6, 2, 1, 1, 1)

        self.radioButton_flight_7 = QRadioButton(self.centralwidget)
        self.radioButton_flight_7.setObjectName(u"radioButton_flight_7")

        self.gridLayout_flights.addWidget(self.radioButton_flight_7, 2, 2, 1, 1)

        self.radioButton_flight_8 = QRadioButton(self.centralwidget)
        self.radioButton_flight_8.setObjectName(u"radioButton_flight_8")

        self.gridLayout_flights.addWidget(self.radioButton_flight_8, 2, 3, 1, 1)

        self.radioButton_flight_9 = QRadioButton(self.centralwidget)
        self.radioButton_flight_9.setObjectName(u"radioButton_flight_9")

        self.gridLayout_flights.addWidget(self.radioButton_flight_9, 3, 0, 1, 1)

        self.radioButton_flight_12 = QRadioButton(self.centralwidget)
        self.radioButton_flight_12.setObjectName(u"radioButton_flight_12")

        self.gridLayout_flights.addWidget(self.radioButton_flight_12, 3, 3, 1, 1)

        self.radioButton_flight_11 = QRadioButton(self.centralwidget)
        self.radioButton_flight_11.setObjectName(u"radioButton_flight_11")

        self.gridLayout_flights.addWidget(self.radioButton_flight_11, 3, 2, 1, 1)

        self.radioButton_flight_10 = QRadioButton(self.centralwidget)
        self.radioButton_flight_10.setObjectName(u"radioButton_flight_10")

        self.gridLayout_flights.addWidget(self.radioButton_flight_10, 3, 1, 1, 1)

        self.radioButton_flight_13 = QRadioButton(self.centralwidget)
        self.radioButton_flight_13.setObjectName(u"radioButton_flight_13")

        self.gridLayout_flights.addWidget(self.radioButton_flight_13, 4, 0, 1, 1)

        self.radioButton_flight_14 = QRadioButton(self.centralwidget)
        self.radioButton_flight_14.setObjectName(u"radioButton_flight_14")

        self.gridLayout_flights.addWidget(self.radioButton_flight_14, 4, 1, 1, 1)

        self.radioButton_flight_16 = QRadioButton(self.centralwidget)
        self.radioButton_flight_16.setObjectName(u"radioButton_flight_16")

        self.gridLayout_flights.addWidget(self.radioButton_flight_16, 4, 3, 1, 1)

        self.radioButton_flight_17 = QRadioButton(self.centralwidget)
        self.radioButton_flight_17.setObjectName(u"radioButton_flight_17")

        self.gridLayout_flights.addWidget(self.radioButton_flight_17, 5, 0, 1, 1)

        self.radioButton_flight_15 = QRadioButton(self.centralwidget)
        self.radioButton_flight_15.setObjectName(u"radioButton_flight_15")

        self.gridLayout_flights.addWidget(self.radioButton_flight_15, 4, 2, 1, 1)


        self.verticalLayout_4.addLayout(self.gridLayout_flights)

        self.verticalSpacer_5 = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_5)

        self.verticalLayout_4.setStretch(11, 1)

        self.horizontalLayout_top.addLayout(self.verticalLayout_4)

        self.horizontalLayout_top.setStretch(0, 1)
        self.horizontalLayout_top.setStretch(2, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_top)

        self.horizontalLayout_bottom = QHBoxLayout()
        self.horizontalLayout_bottom.setObjectName(u"horizontalLayout_bottom")
        self.horizontalLayout_bottom.setContentsMargins(0, 0, -1, 1)
        self.pushbutton_start = QPushButton(self.centralwidget)
        self.pushbutton_start.setObjectName(u"pushbutton_start")
        self.pushbutton_start.setMinimumSize(QSize(0, 60))
        self.pushbutton_start.setBaseSize(QSize(0, 0))

        self.horizontalLayout_bottom.addWidget(self.pushbutton_start)

        self.pushbutton_stop = QPushButton(self.centralwidget)
        self.pushbutton_stop.setObjectName(u"pushbutton_stop")
        self.pushbutton_stop.setMinimumSize(QSize(0, 60))

        self.horizontalLayout_bottom.addWidget(self.pushbutton_stop)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, -1, 20, -1)
        self.label_speed_label = QLabel(self.centralwidget)
        self.label_speed_label.setObjectName(u"label_speed_label")
        self.label_speed_label.setStyleSheet(u"font-size: 24px;")
        self.label_speed_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_speed_label, 1, 0, 1, 1)

        self.label_time = QLabel(self.centralwidget)
        self.label_time.setObjectName(u"label_time")
        self.label_time.setStyleSheet(u"font-size: 24px;")
        self.label_time.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_time, 0, 1, 1, 1)

        self.label_time_label = QLabel(self.centralwidget)
        self.label_time_label.setObjectName(u"label_time_label")
        self.label_time_label.setStyleSheet(u"font-size: 24px;")
        self.label_time_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_time_label, 0, 0, 1, 1)

        self.label_speed = QLabel(self.centralwidget)
        self.label_speed.setObjectName(u"label_speed")
        self.label_speed.setStyleSheet(u"font-size: 24px;")
        self.label_speed.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_speed, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)

        self.horizontalLayout_bottom.addLayout(self.gridLayout)

        self.horizontalSpacer = QSpacerItem(170, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_bottom.addItem(self.horizontalSpacer)

        self.horizontalLayout_bottom.setStretch(2, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_bottom)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Speed", None))
        self.label_video1_online.setText(QCoreApplication.translate("MainWindow", u"Waiting...", None))
        self.pushButton_video1_align.setText(QCoreApplication.translate("MainWindow", u"Align Camera", None))
        self.label_video1.setText("")
        self.label_time_video1.setText(QCoreApplication.translate("MainWindow", u"00:00.000", None))
        self.pushbutton_video1_find.setText(QCoreApplication.translate("MainWindow", u"Find", None))
        self.pushbutton_video1_playbackward.setText(QCoreApplication.translate("MainWindow", u"<<", None))
        self.pushbutton_video1_backstep.setText(QCoreApplication.translate("MainWindow", u"<", None))
        self.pushbutton_video1_pause.setText(QCoreApplication.translate("MainWindow", u"||", None))
        self.pushbutton_video1_forwardstep.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.pushbutton_video1_playforward.setText(QCoreApplication.translate("MainWindow", u">>", None))
        self.pushbutton_video1_copy.setText(QCoreApplication.translate("MainWindow", u"Copy right", None))
        self.label_video2_online.setText(QCoreApplication.translate("MainWindow", u"Waiting...", None))
        self.pushButton_video2_align.setText(QCoreApplication.translate("MainWindow", u"Align Camera", None))
        self.label_video2.setText("")
        self.label_time_video2.setText(QCoreApplication.translate("MainWindow", u"00:00.000 ", None))
        self.pushbutton_video2_copy.setText(QCoreApplication.translate("MainWindow", u"Copy left", None))
        self.pushbutton_video2_find.setText(QCoreApplication.translate("MainWindow", u"Find", None))
        self.pushbutton_video2_playbackward.setText(QCoreApplication.translate("MainWindow", u"<<", None))
        self.pushbutton_video2_backstep.setText(QCoreApplication.translate("MainWindow", u"<", None))
        self.pushbutton_video2_pause.setText(QCoreApplication.translate("MainWindow", u"||", None))
        self.pushbutton_video2_forwardstep.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.pushbutton_video2_playforward.setText(QCoreApplication.translate("MainWindow", u">>", None))
        self.label_distance.setText(QCoreApplication.translate("MainWindow", u"Distance meters", None))
        self.checkBox_live.setText(QCoreApplication.translate("MainWindow", u"Live preview", None))
        self.checkBox_motion_track.setText(QCoreApplication.translate("MainWindow", u"Realtime Announcements", None))
        self.pushButton_remove_announcement.setText(QCoreApplication.translate("MainWindow", u"Remove Announcement", None))
        self.label_average.setText(QCoreApplication.translate("MainWindow", u"Average: ---", None))
        self.label_flightnumber.setText(QCoreApplication.translate("MainWindow", u"Flight number", None))
        self.radioButton_flight_1.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.radioButton_flight_4.setText(QCoreApplication.translate("MainWindow", u"4", None))
        self.radioButton_flight_3.setText(QCoreApplication.translate("MainWindow", u"3", None))
        self.radioButton_flight_2.setText(QCoreApplication.translate("MainWindow", u"2", None))
        self.radioButton_flight_20.setText(QCoreApplication.translate("MainWindow", u"20", None))
        self.radioButton_flight_19.setText(QCoreApplication.translate("MainWindow", u"19", None))
        self.radioButton_flight_18.setText(QCoreApplication.translate("MainWindow", u"18", None))
        self.radioButton_flight_5.setText(QCoreApplication.translate("MainWindow", u"5", None))
        self.radioButton_flight_6.setText(QCoreApplication.translate("MainWindow", u"6", None))
        self.radioButton_flight_7.setText(QCoreApplication.translate("MainWindow", u"7", None))
        self.radioButton_flight_8.setText(QCoreApplication.translate("MainWindow", u"8", None))
        self.radioButton_flight_9.setText(QCoreApplication.translate("MainWindow", u"9", None))
        self.radioButton_flight_12.setText(QCoreApplication.translate("MainWindow", u"12", None))
        self.radioButton_flight_11.setText(QCoreApplication.translate("MainWindow", u"11", None))
        self.radioButton_flight_10.setText(QCoreApplication.translate("MainWindow", u"10", None))
        self.radioButton_flight_13.setText(QCoreApplication.translate("MainWindow", u"13", None))
        self.radioButton_flight_14.setText(QCoreApplication.translate("MainWindow", u"14", None))
        self.radioButton_flight_16.setText(QCoreApplication.translate("MainWindow", u"16", None))
        self.radioButton_flight_17.setText(QCoreApplication.translate("MainWindow", u"17", None))
        self.radioButton_flight_15.setText(QCoreApplication.translate("MainWindow", u"15", None))
        self.pushbutton_start.setText(QCoreApplication.translate("MainWindow", u"Start cameras", None))
        self.pushbutton_stop.setText(QCoreApplication.translate("MainWindow", u"Stop Cameras", None))
        self.label_speed_label.setText(QCoreApplication.translate("MainWindow", u"Speed:", None))
        self.label_time.setText(QCoreApplication.translate("MainWindow", u"1.423 sec", None))
        self.label_time_label.setText(QCoreApplication.translate("MainWindow", u"Time:", None))
        self.label_speed.setText(QCoreApplication.translate("MainWindow", u"888.88 kmh", None))
    # retranslateUi

