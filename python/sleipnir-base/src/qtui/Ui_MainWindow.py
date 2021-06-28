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
        MainWindow.resize(1058, 886)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_4 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontal_layout_top = QHBoxLayout()
        self.horizontal_layout_top.setObjectName(u"horizontal_layout_top")
        self.horizontal_layout_top.setContentsMargins(-1, 0, 0, 0)
        self.vertical_layout_video_1 = QVBoxLayout()
        self.vertical_layout_video_1.setObjectName(u"vertical_layout_video_1")
        self.vertical_layout_video_1.setContentsMargins(-1, 0, -1, 0)
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

        self.vertical_layout_video_1.addLayout(self.horizontalLayout_video_1_top)

        self.video_player_label_video1 = QLabel(self.centralwidget)
        self.video_player_label_video1.setObjectName(u"video_player_label_video1")
        self.video_player_label_video1.setFrameShape(QFrame.Box)
        self.video_player_label_video1.setScaledContents(True)

        self.vertical_layout_video_1.addWidget(self.video_player_label_video1)

        self.horizontalLayout_video_1_slider = QHBoxLayout()
        self.horizontalLayout_video_1_slider.setObjectName(u"horizontalLayout_video_1_slider")
        self.horizontalLayout_video_1_slider.setContentsMargins(-1, 10, -1, 10)
        self.video_player_slider_video1 = QSlider(self.centralwidget)
        self.video_player_slider_video1.setObjectName(u"video_player_slider_video1")
        self.video_player_slider_video1.setOrientation(Qt.Horizontal)

        self.horizontalLayout_video_1_slider.addWidget(self.video_player_slider_video1)

        self.video_player_label_time_video1 = QLabel(self.centralwidget)
        self.video_player_label_time_video1.setObjectName(u"video_player_label_time_video1")

        self.horizontalLayout_video_1_slider.addWidget(self.video_player_label_time_video1)


        self.vertical_layout_video_1.addLayout(self.horizontalLayout_video_1_slider)

        self.horizontalLayout_video_1_buttons = QHBoxLayout()
        self.horizontalLayout_video_1_buttons.setSpacing(0)
        self.horizontalLayout_video_1_buttons.setObjectName(u"horizontalLayout_video_1_buttons")
        self.horizontalLayout_video_1_buttons.setContentsMargins(-1, 0, -1, -1)
        self.video_player_push_button_video1_find = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_find.setObjectName(u"video_player_push_button_video1_find")

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_find)

        self.horizontalSpacer_2 = QSpacerItem(16, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_video_1_buttons.addItem(self.horizontalSpacer_2)

        self.video_player_push_button_video1_play_reverse = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_play_reverse.setObjectName(u"video_player_push_button_video1_play_reverse")
        self.video_player_push_button_video1_play_reverse.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_play_reverse)

        self.video_player_push_button_video1_step_reverse = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_step_reverse.setObjectName(u"video_player_push_button_video1_step_reverse")
        self.video_player_push_button_video1_step_reverse.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_step_reverse)

        self.video_player_push_button_video1_stop = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_stop.setObjectName(u"video_player_push_button_video1_stop")
        self.video_player_push_button_video1_stop.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_stop)

        self.video_player_push_button_video1_step_forward = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_step_forward.setObjectName(u"video_player_push_button_video1_step_forward")
        self.video_player_push_button_video1_step_forward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_step_forward)

        self.video_player_push_button_video1_play_forward = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_play_forward.setObjectName(u"video_player_push_button_video1_play_forward")
        self.video_player_push_button_video1_play_forward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_play_forward)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_video_1_buttons.addItem(self.horizontalSpacer_3)

        self.video_player_push_button_video1_copy = QPushButton(self.centralwidget)
        self.video_player_push_button_video1_copy.setObjectName(u"video_player_push_button_video1_copy")

        self.horizontalLayout_video_1_buttons.addWidget(self.video_player_push_button_video1_copy)

        self.horizontalLayout_video_1_buttons.setStretch(7, 1)

        self.vertical_layout_video_1.addLayout(self.horizontalLayout_video_1_buttons)

        self.vertical_layout_video_1.setStretch(1, 1)

        self.horizontal_layout_top.addLayout(self.vertical_layout_video_1)

        self.vertical_layout_groundlevel = QVBoxLayout()
        self.vertical_layout_groundlevel.setObjectName(u"vertical_layout_groundlevel")
        self.vertical_layout_groundlevel.setContentsMargins(-1, -1, 0, -1)
        self.verticalSpacer_4 = QSpacerItem(1, 34, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.vertical_layout_groundlevel.addItem(self.verticalSpacer_4)

        self.verticalSlider_groundlevel = QSlider(self.centralwidget)
        self.verticalSlider_groundlevel.setObjectName(u"verticalSlider_groundlevel")
        self.verticalSlider_groundlevel.setMinimum(1)
        self.verticalSlider_groundlevel.setMaximum(480)
        self.verticalSlider_groundlevel.setValue(400)
        self.verticalSlider_groundlevel.setOrientation(Qt.Vertical)
        self.verticalSlider_groundlevel.setInvertedAppearance(True)

        self.vertical_layout_groundlevel.addWidget(self.verticalSlider_groundlevel)

        self.verticalSpacer_3 = QSpacerItem(1, 80, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.vertical_layout_groundlevel.addItem(self.verticalSpacer_3)


        self.horizontal_layout_top.addLayout(self.vertical_layout_groundlevel)

        self.vertical_layout_video_2 = QVBoxLayout()
        self.vertical_layout_video_2.setObjectName(u"vertical_layout_video_2")
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

        self.vertical_layout_video_2.addLayout(self.horizontalLayout_video_2_top)

        self.video_player_label_video2 = QLabel(self.centralwidget)
        self.video_player_label_video2.setObjectName(u"video_player_label_video2")
        self.video_player_label_video2.setFrameShape(QFrame.Box)
        self.video_player_label_video2.setScaledContents(True)

        self.vertical_layout_video_2.addWidget(self.video_player_label_video2)

        self.horizontalLayout_video_2_slider = QHBoxLayout()
        self.horizontalLayout_video_2_slider.setObjectName(u"horizontalLayout_video_2_slider")
        self.horizontalLayout_video_2_slider.setContentsMargins(-1, 10, -1, 10)
        self.video_player_slider_video2 = QSlider(self.centralwidget)
        self.video_player_slider_video2.setObjectName(u"video_player_slider_video2")
        self.video_player_slider_video2.setOrientation(Qt.Horizontal)

        self.horizontalLayout_video_2_slider.addWidget(self.video_player_slider_video2)

        self.video_player_label_time_video2 = QLabel(self.centralwidget)
        self.video_player_label_time_video2.setObjectName(u"video_player_label_time_video2")

        self.horizontalLayout_video_2_slider.addWidget(self.video_player_label_time_video2)


        self.vertical_layout_video_2.addLayout(self.horizontalLayout_video_2_slider)

        self.horizontalLayout_video_2_buttons = QHBoxLayout()
        self.horizontalLayout_video_2_buttons.setSpacing(0)
        self.horizontalLayout_video_2_buttons.setObjectName(u"horizontalLayout_video_2_buttons")
        self.horizontalLayout_video_2_buttons.setContentsMargins(-1, 0, -1, 0)
        self.video_player_push_button_video2_copy = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_copy.setObjectName(u"video_player_push_button_video2_copy")

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_copy)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_video_2_buttons.addItem(self.horizontalSpacer_4)

        self.video_player_push_button_video2_find = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_find.setObjectName(u"video_player_push_button_video2_find")

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_find)

        self.horizontalSpacer_5 = QSpacerItem(16, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_video_2_buttons.addItem(self.horizontalSpacer_5)

        self.video_player_push_button_video2_play_reverse = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_play_reverse.setObjectName(u"video_player_push_button_video2_play_reverse")
        self.video_player_push_button_video2_play_reverse.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_play_reverse)

        self.video_player_push_button_video2_step_reverse = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_step_reverse.setObjectName(u"video_player_push_button_video2_step_reverse")
        self.video_player_push_button_video2_step_reverse.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_step_reverse)

        self.video_player_push_button_video2_stop = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_stop.setObjectName(u"video_player_push_button_video2_stop")
        self.video_player_push_button_video2_stop.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_stop)

        self.video_player_push_button_video2_step_forward = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_step_forward.setObjectName(u"video_player_push_button_video2_step_forward")
        self.video_player_push_button_video2_step_forward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_step_forward)

        self.video_player_push_button_video2_play_forward = QPushButton(self.centralwidget)
        self.video_player_push_button_video2_play_forward.setObjectName(u"video_player_push_button_video2_play_forward")
        self.video_player_push_button_video2_play_forward.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_video_2_buttons.addWidget(self.video_player_push_button_video2_play_forward)

        self.horizontalLayout_video_2_buttons.setStretch(1, 1)

        self.vertical_layout_video_2.addLayout(self.horizontalLayout_video_2_buttons)

        self.vertical_layout_video_2.setStretch(1, 1)

        self.horizontal_layout_top.addLayout(self.vertical_layout_video_2)

        self.vertical_layout_game = QVBoxLayout()
        self.vertical_layout_game.setSpacing(6)
        self.vertical_layout_game.setObjectName(u"vertical_layout_game")
        self.vertical_layout_game.setContentsMargins(3, 1, 3, -1)
        self.sleipnir_combo_box_game_select = QComboBox(self.centralwidget)
        self.sleipnir_combo_box_game_select.addItem("")
        self.sleipnir_combo_box_game_select.addItem("")
        self.sleipnir_combo_box_game_select.setObjectName(u"sleipnir_combo_box_game_select")
        self.sleipnir_combo_box_game_select.setMinimumSize(QSize(0, 21))
        self.sleipnir_combo_box_game_select.setEditable(False)

        self.vertical_layout_game.addWidget(self.sleipnir_combo_box_game_select)

        self.stacked_widget_game = QStackedWidget(self.centralwidget)
        self.stacked_widget_game.setObjectName(u"stacked_widget_game")
        self.stacked_widget_game.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stacked_widget_game.sizePolicy().hasHeightForWidth())
        self.stacked_widget_game.setSizePolicy(sizePolicy)
        self.stacked_widget_game.setMinimumSize(QSize(0, 0))
        self.stacked_widget_game.setMaximumSize(QSize(16777215, 16777215))
        self.stacked_widget_game.setLayoutDirection(Qt.LeftToRight)
        self.stacked_widget_game.setAutoFillBackground(False)
        self.speed_measure = QWidget()
        self.speed_measure.setObjectName(u"speed_measure")
        self.speed_measure.setMinimumSize(QSize(250, 500))
        self.speed_measure.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.speed_measure)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, -1, 0, -1)
        self.speed_trap_label_distance = QLabel(self.speed_measure)
        self.speed_trap_label_distance.setObjectName(u"speed_trap_label_distance")

        self.verticalLayout.addWidget(self.speed_trap_label_distance)

        self.speed_trap_line_edit_distance = QLineEdit(self.speed_measure)
        self.speed_trap_line_edit_distance.setObjectName(u"speed_trap_line_edit_distance")
        self.speed_trap_line_edit_distance.setMaximumSize(QSize(16777215, 16777215))

        self.verticalLayout.addWidget(self.speed_trap_line_edit_distance)

        self.speed_trap_check_box_speak = QCheckBox(self.speed_measure)
        self.speed_trap_check_box_speak.setObjectName(u"speed_trap_check_box_speak")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.speed_trap_check_box_speak.sizePolicy().hasHeightForWidth())
        self.speed_trap_check_box_speak.setSizePolicy(sizePolicy1)
        self.speed_trap_check_box_speak.setMinimumSize(QSize(0, 0))
        self.speed_trap_check_box_speak.setChecked(True)

        self.verticalLayout.addWidget(self.speed_trap_check_box_speak)

        self.speed_trap_table_view_announcement = QTableView(self.speed_measure)
        self.speed_trap_table_view_announcement.setObjectName(u"speed_trap_table_view_announcement")
        font = QFont()
        font.setFamily(u"Consolas")
        font.setPointSize(10)
        self.speed_trap_table_view_announcement.setFont(font)
        self.speed_trap_table_view_announcement.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.speed_trap_table_view_announcement.horizontalHeader().setDefaultSectionSize(60)
        self.speed_trap_table_view_announcement.horizontalHeader().setStretchLastSection(True)
        self.speed_trap_table_view_announcement.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.speed_trap_table_view_announcement)

        self.speed_trap_push_button_remove_announcement = QPushButton(self.speed_measure)
        self.speed_trap_push_button_remove_announcement.setObjectName(u"speed_trap_push_button_remove_announcement")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.speed_trap_push_button_remove_announcement.sizePolicy().hasHeightForWidth())
        self.speed_trap_push_button_remove_announcement.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.speed_trap_push_button_remove_announcement)

        self.speed_trap_label_time = QLabel(self.speed_measure)
        self.speed_trap_label_time.setObjectName(u"speed_trap_label_time")
        font1 = QFont()
        font1.setFamily(u"Consolas")
        font1.setPointSize(16)
        self.speed_trap_label_time.setFont(font1)
        self.speed_trap_label_time.setStyleSheet(u"")
        self.speed_trap_label_time.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.verticalLayout.addWidget(self.speed_trap_label_time)

        self.speed_trap_label_speed = QLabel(self.speed_measure)
        self.speed_trap_label_speed.setObjectName(u"speed_trap_label_speed")
        self.speed_trap_label_speed.setFont(font1)
        self.speed_trap_label_speed.setStyleSheet(u"")
        self.speed_trap_label_speed.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.verticalLayout.addWidget(self.speed_trap_label_speed)

        self.speed_trap_label_average = QLabel(self.speed_measure)
        self.speed_trap_label_average.setObjectName(u"speed_trap_label_average")
        self.speed_trap_label_average.setFont(font1)
        self.speed_trap_label_average.setStyleSheet(u"")

        self.verticalLayout.addWidget(self.speed_trap_label_average)

        self.verticalLayoutSpeed = QVBoxLayout()
        self.verticalLayoutSpeed.setSpacing(6)
        self.verticalLayoutSpeed.setObjectName(u"verticalLayoutSpeed")
        self.verticalLayoutSpeed.setSizeConstraint(QLayout.SetDefaultConstraint)

        self.verticalLayout.addLayout(self.verticalLayoutSpeed)

        self.stacked_widget_game.addWidget(self.speed_measure)
        self.gate_crasher = QWidget()
        self.gate_crasher.setObjectName(u"gate_crasher")
        self.verticalLayout_5 = QVBoxLayout(self.gate_crasher)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, -1, 0, -1)
        self.gate_crasher_label_select_course = QLabel(self.gate_crasher)
        self.gate_crasher_label_select_course.setObjectName(u"gate_crasher_label_select_course")

        self.verticalLayout_5.addWidget(self.gate_crasher_label_select_course)

        self.gate_crasher_combo_box_course_select = QComboBox(self.gate_crasher)
        self.gate_crasher_combo_box_course_select.setObjectName(u"gate_crasher_combo_box_course_select")

        self.verticalLayout_5.addWidget(self.gate_crasher_combo_box_course_select)

        self.gate_crasher_table_view_result = QTableView(self.gate_crasher)
        self.gate_crasher_table_view_result.setObjectName(u"gate_crasher_table_view_result")
        self.gate_crasher_table_view_result.setFont(font)
        self.gate_crasher_table_view_result.setStyleSheet(u"")
        self.gate_crasher_table_view_result.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gate_crasher_table_view_result.horizontalHeader().setDefaultSectionSize(60)
        self.gate_crasher_table_view_result.horizontalHeader().setStretchLastSection(True)
        self.gate_crasher_table_view_result.verticalHeader().setVisible(False)

        self.verticalLayout_5.addWidget(self.gate_crasher_table_view_result)

        self.gate_crasher_label_time = QLabel(self.gate_crasher)
        self.gate_crasher_label_time.setObjectName(u"gate_crasher_label_time")
        self.gate_crasher_label_time.setFont(font1)
        self.gate_crasher_label_time.setStyleSheet(u"")

        self.verticalLayout_5.addWidget(self.gate_crasher_label_time)

        self.stacked_widget_game.addWidget(self.gate_crasher)

        self.vertical_layout_game.addWidget(self.stacked_widget_game)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_game.addWidget(self.line)

        self.checkBox_live = QCheckBox(self.centralwidget)
        self.checkBox_live.setObjectName(u"checkBox_live")
        self.checkBox_live.setEnabled(True)
        sizePolicy1.setHeightForWidth(self.checkBox_live.sizePolicy().hasHeightForWidth())
        self.checkBox_live.setSizePolicy(sizePolicy1)
        self.checkBox_live.setChecked(True)

        self.vertical_layout_game.addWidget(self.checkBox_live)

        self.verticalSpacer = QSpacerItem(100, 5, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.vertical_layout_game.addItem(self.verticalSpacer)

        self.label_flightnumber = QLabel(self.centralwidget)
        self.label_flightnumber.setObjectName(u"label_flightnumber")

        self.vertical_layout_game.addWidget(self.label_flightnumber)

        self.gridLayout_flights = QGridLayout()
        self.gridLayout_flights.setObjectName(u"gridLayout_flights")
        self.gridLayout_flights.setHorizontalSpacing(0)
        self.gridLayout_flights.setVerticalSpacing(15)
        self.radioButton_flight_20 = QRadioButton(self.centralwidget)
        self.radioButton_flight_20.setObjectName(u"radioButton_flight_20")

        self.gridLayout_flights.addWidget(self.radioButton_flight_20, 5, 3, 1, 1)

        self.radioButton_flight_1 = QRadioButton(self.centralwidget)
        self.radioButton_flight_1.setObjectName(u"radioButton_flight_1")
        self.radioButton_flight_1.setMaximumSize(QSize(16777215, 16777215))

        self.gridLayout_flights.addWidget(self.radioButton_flight_1, 1, 0, 1, 1)

        self.radioButton_flight_4 = QRadioButton(self.centralwidget)
        self.radioButton_flight_4.setObjectName(u"radioButton_flight_4")

        self.gridLayout_flights.addWidget(self.radioButton_flight_4, 1, 3, 1, 1)

        self.radioButton_flight_2 = QRadioButton(self.centralwidget)
        self.radioButton_flight_2.setObjectName(u"radioButton_flight_2")

        self.gridLayout_flights.addWidget(self.radioButton_flight_2, 1, 1, 1, 1)

        self.radioButton_flight_9 = QRadioButton(self.centralwidget)
        self.radioButton_flight_9.setObjectName(u"radioButton_flight_9")

        self.gridLayout_flights.addWidget(self.radioButton_flight_9, 3, 0, 1, 1)

        self.radioButton_flight_17 = QRadioButton(self.centralwidget)
        self.radioButton_flight_17.setObjectName(u"radioButton_flight_17")

        self.gridLayout_flights.addWidget(self.radioButton_flight_17, 5, 0, 1, 1)

        self.radioButton_flight_13 = QRadioButton(self.centralwidget)
        self.radioButton_flight_13.setObjectName(u"radioButton_flight_13")

        self.gridLayout_flights.addWidget(self.radioButton_flight_13, 4, 0, 1, 1)

        self.radioButton_flight_10 = QRadioButton(self.centralwidget)
        self.radioButton_flight_10.setObjectName(u"radioButton_flight_10")

        self.gridLayout_flights.addWidget(self.radioButton_flight_10, 3, 1, 1, 1)

        self.radioButton_flight_16 = QRadioButton(self.centralwidget)
        self.radioButton_flight_16.setObjectName(u"radioButton_flight_16")

        self.gridLayout_flights.addWidget(self.radioButton_flight_16, 4, 3, 1, 1)

        self.radioButton_flight_5 = QRadioButton(self.centralwidget)
        self.radioButton_flight_5.setObjectName(u"radioButton_flight_5")
        self.radioButton_flight_5.setMaximumSize(QSize(16777215, 16777215))

        self.gridLayout_flights.addWidget(self.radioButton_flight_5, 2, 0, 1, 1)

        self.radioButton_flight_19 = QRadioButton(self.centralwidget)
        self.radioButton_flight_19.setObjectName(u"radioButton_flight_19")

        self.gridLayout_flights.addWidget(self.radioButton_flight_19, 5, 2, 1, 1)

        self.radioButton_flight_12 = QRadioButton(self.centralwidget)
        self.radioButton_flight_12.setObjectName(u"radioButton_flight_12")

        self.gridLayout_flights.addWidget(self.radioButton_flight_12, 3, 3, 1, 1)

        self.radioButton_flight_6 = QRadioButton(self.centralwidget)
        self.radioButton_flight_6.setObjectName(u"radioButton_flight_6")

        self.gridLayout_flights.addWidget(self.radioButton_flight_6, 2, 1, 1, 1)

        self.radioButton_flight_14 = QRadioButton(self.centralwidget)
        self.radioButton_flight_14.setObjectName(u"radioButton_flight_14")

        self.gridLayout_flights.addWidget(self.radioButton_flight_14, 4, 1, 1, 1)

        self.radioButton_flight_11 = QRadioButton(self.centralwidget)
        self.radioButton_flight_11.setObjectName(u"radioButton_flight_11")

        self.gridLayout_flights.addWidget(self.radioButton_flight_11, 3, 2, 1, 1)

        self.radioButton_flight_15 = QRadioButton(self.centralwidget)
        self.radioButton_flight_15.setObjectName(u"radioButton_flight_15")

        self.gridLayout_flights.addWidget(self.radioButton_flight_15, 4, 2, 1, 1)

        self.radioButton_flight_18 = QRadioButton(self.centralwidget)
        self.radioButton_flight_18.setObjectName(u"radioButton_flight_18")

        self.gridLayout_flights.addWidget(self.radioButton_flight_18, 5, 1, 1, 1)

        self.radioButton_flight_3 = QRadioButton(self.centralwidget)
        self.radioButton_flight_3.setObjectName(u"radioButton_flight_3")

        self.gridLayout_flights.addWidget(self.radioButton_flight_3, 1, 2, 1, 1)

        self.radioButton_flight_8 = QRadioButton(self.centralwidget)
        self.radioButton_flight_8.setObjectName(u"radioButton_flight_8")

        self.gridLayout_flights.addWidget(self.radioButton_flight_8, 2, 3, 1, 1)

        self.radioButton_flight_7 = QRadioButton(self.centralwidget)
        self.radioButton_flight_7.setObjectName(u"radioButton_flight_7")

        self.gridLayout_flights.addWidget(self.radioButton_flight_7, 2, 2, 1, 1)


        self.vertical_layout_game.addLayout(self.gridLayout_flights)

        self.horizontal_layout_start_stop = QHBoxLayout()
        self.horizontal_layout_start_stop.setObjectName(u"horizontal_layout_start_stop")
        self.horizontal_layout_start_stop.setContentsMargins(-1, 6, -1, 0)
        self.pushbutton_start = QPushButton(self.centralwidget)
        self.pushbutton_start.setObjectName(u"pushbutton_start")
        self.pushbutton_start.setMinimumSize(QSize(0, 60))
        self.pushbutton_start.setBaseSize(QSize(0, 0))
        font2 = QFont()
        font2.setPointSize(12)
        self.pushbutton_start.setFont(font2)

        self.horizontal_layout_start_stop.addWidget(self.pushbutton_start)

        self.pushbutton_stop = QPushButton(self.centralwidget)
        self.pushbutton_stop.setObjectName(u"pushbutton_stop")
        self.pushbutton_stop.setMinimumSize(QSize(0, 60))
        self.pushbutton_stop.setFont(font2)

        self.horizontal_layout_start_stop.addWidget(self.pushbutton_stop)


        self.vertical_layout_game.addLayout(self.horizontal_layout_start_stop)


        self.horizontal_layout_top.addLayout(self.vertical_layout_game)

        self.horizontal_layout_top.setStretch(0, 1)
        self.horizontal_layout_top.setStretch(2, 1)

        self.horizontalLayout_4.addLayout(self.horizontal_layout_top)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.stacked_widget_game.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Speed", None))
        self.label_video1_online.setText(QCoreApplication.translate("MainWindow", u"Waiting...", None))
        self.pushButton_video1_align.setText(QCoreApplication.translate("MainWindow", u"Align Camera", None))
        self.video_player_label_video1.setText("")
        self.video_player_label_time_video1.setText(QCoreApplication.translate("MainWindow", u"00:00.000", None))
        self.video_player_push_button_video1_find.setText(QCoreApplication.translate("MainWindow", u"Find", None))
        self.video_player_push_button_video1_play_reverse.setText(QCoreApplication.translate("MainWindow", u"<<", None))
        self.video_player_push_button_video1_step_reverse.setText(QCoreApplication.translate("MainWindow", u"<", None))
        self.video_player_push_button_video1_stop.setText(QCoreApplication.translate("MainWindow", u"||", None))
        self.video_player_push_button_video1_step_forward.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.video_player_push_button_video1_play_forward.setText(QCoreApplication.translate("MainWindow", u">>", None))
        self.video_player_push_button_video1_copy.setText(QCoreApplication.translate("MainWindow", u"Copy Right", None))
        self.label_video2_online.setText(QCoreApplication.translate("MainWindow", u"Waiting...", None))
        self.pushButton_video2_align.setText(QCoreApplication.translate("MainWindow", u"Align Camera", None))
        self.video_player_label_video2.setText("")
        self.video_player_label_time_video2.setText(QCoreApplication.translate("MainWindow", u"00:00.000 ", None))
        self.video_player_push_button_video2_copy.setText(QCoreApplication.translate("MainWindow", u"Copy Left", None))
        self.video_player_push_button_video2_find.setText(QCoreApplication.translate("MainWindow", u"Find", None))
        self.video_player_push_button_video2_play_reverse.setText(QCoreApplication.translate("MainWindow", u"<<", None))
        self.video_player_push_button_video2_step_reverse.setText(QCoreApplication.translate("MainWindow", u"<", None))
        self.video_player_push_button_video2_stop.setText(QCoreApplication.translate("MainWindow", u"||", None))
        self.video_player_push_button_video2_step_forward.setText(QCoreApplication.translate("MainWindow", u">", None))
        self.video_player_push_button_video2_play_forward.setText(QCoreApplication.translate("MainWindow", u">>", None))
        self.sleipnir_combo_box_game_select.setItemText(0, QCoreApplication.translate("MainWindow", u"Speed Trap", None))
        self.sleipnir_combo_box_game_select.setItemText(1, QCoreApplication.translate("MainWindow", u"Gate Crasher", None))

        self.sleipnir_combo_box_game_select.setCurrentText(QCoreApplication.translate("MainWindow", u"Speed Trap", None))
        self.speed_trap_label_distance.setText(QCoreApplication.translate("MainWindow", u"Distance Meters", None))
        self.speed_trap_check_box_speak.setText(QCoreApplication.translate("MainWindow", u"Realtime Announcements", None))
        self.speed_trap_push_button_remove_announcement.setText(QCoreApplication.translate("MainWindow", u"Remove Announcement", None))
        self.speed_trap_label_time.setText(QCoreApplication.translate("MainWindow", u"Time:    ---", None))
        self.speed_trap_label_speed.setText(QCoreApplication.translate("MainWindow", u"Speed:   ---", None))
        self.speed_trap_label_average.setText(QCoreApplication.translate("MainWindow", u"Average: ---", None))
        self.gate_crasher_label_select_course.setText(QCoreApplication.translate("MainWindow", u"Select Course", None))
        self.gate_crasher_label_time.setText(QCoreApplication.translate("MainWindow", u"Time: ---", None))
        self.checkBox_live.setText(QCoreApplication.translate("MainWindow", u"Live Video Feed", None))
        self.label_flightnumber.setText(QCoreApplication.translate("MainWindow", u"Flight Number", None))
        self.radioButton_flight_20.setText(QCoreApplication.translate("MainWindow", u"20", None))
        self.radioButton_flight_1.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.radioButton_flight_4.setText(QCoreApplication.translate("MainWindow", u"4", None))
        self.radioButton_flight_2.setText(QCoreApplication.translate("MainWindow", u"2", None))
        self.radioButton_flight_9.setText(QCoreApplication.translate("MainWindow", u"9", None))
        self.radioButton_flight_17.setText(QCoreApplication.translate("MainWindow", u"17", None))
        self.radioButton_flight_13.setText(QCoreApplication.translate("MainWindow", u"13", None))
        self.radioButton_flight_10.setText(QCoreApplication.translate("MainWindow", u"10", None))
        self.radioButton_flight_16.setText(QCoreApplication.translate("MainWindow", u"16", None))
        self.radioButton_flight_5.setText(QCoreApplication.translate("MainWindow", u"5", None))
        self.radioButton_flight_19.setText(QCoreApplication.translate("MainWindow", u"19", None))
        self.radioButton_flight_12.setText(QCoreApplication.translate("MainWindow", u"12", None))
        self.radioButton_flight_6.setText(QCoreApplication.translate("MainWindow", u"6", None))
        self.radioButton_flight_14.setText(QCoreApplication.translate("MainWindow", u"14", None))
        self.radioButton_flight_11.setText(QCoreApplication.translate("MainWindow", u"11", None))
        self.radioButton_flight_15.setText(QCoreApplication.translate("MainWindow", u"15", None))
        self.radioButton_flight_18.setText(QCoreApplication.translate("MainWindow", u"18", None))
        self.radioButton_flight_3.setText(QCoreApplication.translate("MainWindow", u"3", None))
        self.radioButton_flight_8.setText(QCoreApplication.translate("MainWindow", u"8", None))
        self.radioButton_flight_7.setText(QCoreApplication.translate("MainWindow", u"7", None))
        self.pushbutton_start.setText(QCoreApplication.translate("MainWindow", u"Start ", None))
        self.pushbutton_stop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
    # retranslateUi

