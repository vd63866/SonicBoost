from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox
)

from PySide6.QtCore import Qt, QTimer

from audio.controller import AudioController


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.audio = AudioController()

        self.setWindowTitle("SonicBoost")
        self.setMinimumSize(420, 330)

        self.setup_ui()
        self.refresh_volume()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_volume)
        self.timer.start(2000)

    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(18)

        title = QLabel("SonicBoost")
        title.setStyleSheet(
            "font-size: 27px; font-weight: bold;"
        )

        subtitle = QLabel("Linux Audio Enhancement")
        subtitle.setStyleSheet(
            "color: #999; font-size: 12px;"
        )

        self.volume_label = QLabel("100%")
        self.volume_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.volume_label.setStyleSheet(
            "font-size: 42px; font-weight: bold;"
        )

        self.slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.slider.setRange(0, 125)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(5)

        self.slider.valueChanged.connect(
            self.update_label
        )

        self.slider.sliderReleased.connect(
            self.apply_volume
        )

        self.boost_label = QLabel(
            "Master Volume"
        )

        self.boost_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.reset_button = QPushButton(
            "Reset to 100%"
        )

        self.reset_button.clicked.connect(
            self.reset_volume
        )

        self.mute_button = QPushButton(
            "Mute / Unmute"
        )

        self.mute_button.clicked.connect(
            self.toggle_mute
        )

        buttons = QHBoxLayout()
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.mute_button)

        self.status_label = QLabel(
            "PipeWire audio control"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setStyleSheet(
            "color: #999; font-size: 11px;"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.volume_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.boost_label)
        layout.addLayout(buttons)
        layout.addStretch()
        layout.addWidget(self.status_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: #eeeeee;
                font-family: sans-serif;
            }

            QPushButton {
                background-color: #303030;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 11px;
            }

            QPushButton:hover {
                background-color: #414141;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #444;
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
                border-radius: 3px;
            }
        """)

    def update_label(self, value):
        self.volume_label.setText(f"{value}%")

        if value > 100:
            self.boost_label.setText(
                "Software amplification active"
            )
        else:
            self.boost_label.setText(
                "Master Volume"
            )

    def apply_volume(self):
        try:
            self.audio.set_volume(
                self.slider.value()
            )
            self.status_label.setText(
                "Volume applied successfully"
            )
        except Exception as error:
            self.show_error(error)

    def refresh_volume(self):
        try:
            volume, muted = self.audio.get_volume()

            if not self.slider.isSliderDown():
                self.slider.blockSignals(True)
                self.slider.setValue(
                    min(volume, 125)
                )
                self.slider.blockSignals(False)

            self.status_label.setText(
                "Audio muted" if muted
                else "PipeWire connected"
            )

        except Exception as error:
            self.status_label.setText(
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
