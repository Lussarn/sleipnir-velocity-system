from qtui.Ui_MainWindow import Ui_MainWindow

class SleipnirWindow(Ui_MainWindow):
    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)

        # We want the flight number buttons as an array
        self.radio_buttons_flights =  [
            self.radioButton_flight_1,
            self.radioButton_flight_2,
            self.radioButton_flight_3,
            self.radioButton_flight_4,
            self.radioButton_flight_5,
            self.radioButton_flight_6,
            self.radioButton_flight_7,
            self.radioButton_flight_8,
            self.radioButton_flight_9,
            self.radioButton_flight_10,
            self.radioButton_flight_11,
            self.radioButton_flight_12,
            self.radioButton_flight_13,
            self.radioButton_flight_14,
            self.radioButton_flight_15,
            self.radioButton_flight_16,
            self.radioButton_flight_17,
            self.radioButton_flight_18,
            self.radioButton_flight_19,
            self.radioButton_flight_20]
