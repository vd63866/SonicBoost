import sys

from PySide6.QtCore import Qt, QTimer, QThread, Signal

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTabWidget,
    QComboBox,
    QMessageBox,
)

from audio.controller import AudioController
from audio.equalizer import PipeWireEqualizer, BANDS


PRESETS = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Bass Boost": [4, 4, 3, 2, 1, 0, 0, 0, 0, 0],
    "Treble Boost": [0, 0, 0, 0, 0, 0, 1, 2, 3, 3],
    "Vocal": [-1, -1, 0, 2, 3, 2, 1, 0, -1, -1],
}


class EqualizerApplyWorker(QThread):
    result_ready = Signal(bool, str)

    def __init__(self, gains, parent=None):
        super().__init__(parent)
        self.gains = list(gains)

    def run(self):
        try:
            message = PipeWireEqualizer().apply(self.gains)
            self.result_ready.emit(True, message)

        except Exception as error:
            self.result_ready.emit(False, str(error))


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.audio = AudioController()
        self.equalizer = PipeWireEqualizer()

        self.eq_sliders = []
        self.apply_worker = None

        self.setWindowTitle("SonicBoost")
        self.setMinimumSize(940, 610)

        self.setup_ui()
        self.refresh_volume()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_volume)
        self.timer.start(2000)

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(15)

        title = QLabel("SonicBoost")
        title.setObjectName("title")

        subtitle = QLabel(
            "Linux Audio Enhancement"
        )
        subtitle.setObjectName("subtitle")

        self.tabs = QTabWidget()

        self.tabs.addTab(
            self.create_volume_tab(),
            "Volume"
        )

        self.tabs.addTab(
            self.create_equalizer_tab(),
            "Equalizer"
        )

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self.tabs)

        self.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: #eeeeee;
                font-family: sans-serif;
                font-size: 12px;
            }

            QLabel#title {
                font-size: 29px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #999999;
                font-size: 12px;
            }

            QTabWidget::pane {
                border: 1px solid #353535;
                border-radius: 10px;
            }

            QTabBar::tab {
                background-color: #252525;
                padding: 11px 24px;
                margin-right: 4px;
                border-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: #493477;
            }

            QPushButton {
                background-color: #303030;
                border: 1px solid #454545;
                border-radius: 7px;
                padding: 10px 16px;
            }

            QPushButton:hover {
                background-color: #424242;
            }

            QPushButton:disabled {
                color: #777777;
                background-color: #262626;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #444444;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #a78bfa;
                width: 17px;
                margin: -6px 0;
                border-radius: 8px;
            }

            QSlider::sub-page:horizontal {
                background: #a78bfa;
            }

            QSlider::groove:vertical {
                width: 6px;
                background: #444444;
                border-radius: 3px;
            }

            QSlider::handle:vertical {
                background: #a78bfa;
                height: 17px;
                margin: 0 -6px;
                border-radius: 8px;
            }

            QComboBox {
                background-color: #303030;
                border: 1px solid #454545;
                border-radius: 6px;
                padding: 8px;
                min-width: 130px;
            }
        """)

    def create_volume_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        heading = QLabel("Master Volume")
        heading.setStyleSheet(
            "font-size: 19px; font-weight: bold;"
        )

        self.volume_label = QLabel("100%")
        self.volume_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.volume_label.setStyleSheet(
            "font-size: 48px; font-weight: bold;"
        )

        self.volume_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.volume_slider.setRange(0, 125)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setPageStep(5)

        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_label.setText(
                f"{value}%"
            )
        )

        self.volume_slider.sliderReleased.connect(
            self.apply_volume
        )

        buttons = QHBoxLayout()

        reset_button = QPushButton("Reset to 100%")
        reset_button.clicked.connect(self.reset_volume)

        mute_button = QPushButton("Mute / Unmute")
        mute_button.clicked.connect(self.toggle_mute)

        buttons.addWidget(reset_button)
        buttons.addWidget(mute_button)

        self.volume_status = QLabel(
            "Checking PipeWire..."
        )
        self.volume_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(heading)
        layout.addStretch()
        layout.addWidget(self.volume_label)
        layout.addWidget(self.volume_slider)
        layout.addLayout(buttons)
        layout.addStretch()
        layout.addWidget(self.volume_status)

        return page

    def create_equalizer_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)

        top = QHBoxLayout()

        heading = QLabel("10-Band Equalizer")
        heading.setStyleSheet(
            "font-size: 19px; font-weight: bold;"
        )

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESETS.keys())
        self.preset_combo.currentTextChanged.connect(
            self.load_preset
        )

        top.addWidget(heading)
        top.addStretch()
        top.addWidget(QLabel("Preset:"))
        top.addWidget(self.preset_combo)

        layout.addLayout(top)

        description = QLabel(
            "Adjust each frequency band between -6 dB and +6 dB."
        )
        description.setStyleSheet("color: #999999;")
        layout.addWidget(description)

        bands_layout = QGridLayout()
        bands_layout.setSpacing(12)

        for index, (band_name, frequency, node_name) in enumerate(BANDS):
            band_widget = QWidget()
            band_layout = QVBoxLayout(band_widget)
            band_layout.setContentsMargins(2, 5, 2, 5)
            band_layout.setSpacing(9)

            frequency_label = QLabel(band_name)
            frequency_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            frequency_label.setStyleSheet(
                "font-weight: bold;"
            )

            gain_label = QLabel("0 dB")
            gain_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            gain_label.setStyleSheet(
                "color: #c4a7ff; font-weight: bold;"
            )

            slider = QSlider(
                Qt.Orientation.Vertical
            )

            slider.setRange(-6, 6)
            slider.setValue(0)
            slider.setTickPosition(
                QSlider.TickPosition.TicksBothSides
            )
            slider.setTickInterval(1)
            slider.setMinimumHeight(220)
            slider.setMaximumHeight(260)

            slider.valueChanged.connect(
                lambda value, label=gain_label:
                label.setText(f"{value:+d} dB")
            )

            band_layout.addWidget(
                frequency_label
            )
            band_layout.addWidget(
                gain_label
            )
            band_layout.addWidget(
                slider,
                alignment=Qt.AlignmentFlag.AlignCenter
            )

            bands_layout.addWidget(
                band_widget, 0, index
            )

            self.eq_sliders.append(slider)

        layout.addLayout(bands_layout)

        buttons = QHBoxLayout()

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(
            lambda: self.set_gains(PRESETS["Flat"])
        )

        self.apply_button = QPushButton(
            "Apply Equalizer"
        )
        self.apply_button.setStyleSheet(
            "background-color: #60439a; font-weight: bold;"
        )
        self.apply_button.clicked.connect(
            self.apply_equalizer
        )

        buttons.addWidget(reset_button)
        buttons.addStretch()
        buttons.addWidget(self.apply_button)

        layout.addLayout(buttons)

        self.eq_status = QLabel(
            "Ready — changes are not yet applied."
        )
        self.eq_status.setStyleSheet(
            "color: #999999;"
        )

        layout.addWidget(self.eq_status)

        return page

    def set_gains(self, gains):
        for slider, gain in zip(self.eq_sliders, gains):
            slider.setValue(int(gain))

    def load_preset(self, name):
        if name in PRESETS:
            self.set_gains(PRESETS[name])

            self.eq_status.setText(
                f"{name} preset selected. Click Apply Equalizer to activate."
            )

    def apply_equalizer(self):
        gains = [
            slider.value()
            for slider in self.eq_sliders
        ]

        confirmation = QMessageBox.question(
            self,
            "Apply Equalizer",
            "Applying the equalizer will briefly restart PipeWire "
            "and interrupt audio playback.\n\nContinue?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self.apply_button.setEnabled(False)
        self.eq_status.setText(
            "Applying equalizer... Please wait."
        )

        self.apply_worker = EqualizerApplyWorker(
            gains, self
        )

        self.apply_worker.result_ready.connect(
            self.on_apply_result
        )

        self.apply_worker.finished.connect(
            self.on_apply_finished
        )

        self.apply_worker.start()

    def on_apply_result(self, success, message):
        if success:
            self.eq_status.setText(message)
        else:
            self.eq_status.setText(
                "Equalizer application failed."
            )

            QMessageBox.critical(
                self,
                "SonicBoost Error",
                message
            )

    def on_apply_finished(self):
        self.apply_button.setEnabled(True)

        if self.apply_worker is not None:
            self.apply_worker.deleteLater()
            self.apply_worker = None

        self.refresh_volume()

    def apply_volume(self):
        try:
            self.audio.set_volume(
                self.volume_slider.value()
            )

            self.volume_status.setText(
                "Volume applied successfully"
            )

        except Exception as error:
            self.show_error(error)

    def refresh_volume(self):
        try:
            volume, muted = self.audio.get_volume()

            if not self.volume_slider.isSliderDown():
                self.volume_slider.blockSignals(True)

                self.volume_slider.setValue(
                    min(volume, 125)
                )

                self.volume_slider.blockSignals(False)

            self.volume_status.setText(
                "Audio muted" if muted
                else "PipeWire connected"
            )

        except Exception:
            self.volume_status.setText(
                "Audio connection unavailable"
            )

    def reset_volume(self):
        try:
            self.audio.reset_volume()
            self.refresh_volume()

        except Exception as error:
            self.show_error(error)

    def toggle_mute(self):
        try:
            self.audio.toggle_mute()
            self.refresh_volume()

        except Exception as error:
            self.show_error(error)

    def show_error(self, error):
        QMessageBox.warning(
            self,
            "SonicBoost Error",
            str(error)
        )


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("SonicBoost")
    app.setOrganizationName("SonicBoost")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
