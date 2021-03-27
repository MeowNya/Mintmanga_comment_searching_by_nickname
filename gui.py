#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import traceback


# Для отлова всех исключений, которые в слотах Qt могут "затеряться" и привести к тихому падению
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print('Error: ', text)
    QMessageBox.critical(None, 'Error', text)
    quit()

import sys
sys.excepthook = log_uncaught_exceptions


from main import collect_user_comments


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class CollectCommentsThread(QThread):
    about_new_text = pyqtSignal(str)
    about_progress = pyqtSignal(int)
    about_range_progress = pyqtSignal(int, int)

    def __init__(self, user=None, url=None):
        super().__init__()

        self.user = user
        self.url = url

        self._is_run = False

    def run(self):
        print('Start thread.')

        try:
            collect_user_comments(
                self.user, self.url,
                handler_log_func=self.about_new_text.emit,
                handler_progress_func=self.about_progress.emit,
                handler_range_progress_func=self.about_range_progress.emit,
                is_stop_func=lambda x=None: not self._is_run,
            )

        finally:
            print('Finish thread.')

    def start(self, priority=QThread.InheritPriority):
        self._is_run = True

        super().start(priority)

    def exit(self, return_code=0):
        self._is_run = False

        return super().exit(return_code)


class MainWindow(QWidget):
    # __init__ -- конструктор
    def __init__(self):
        # super() -- обращение к предку, т.е. в данном классе к QWidget и у него вызываем конструктор
        super().__init__()

        self.setWindowTitle('Mintmanga_comment_searching_by_nickname')

        layout = QVBoxLayout()

        self.nick_line_edit = QLineEdit()
        self.nick_line_edit.setText('gil9red')

        self.url_line_edit = QLineEdit()
        self.url_line_edit.setText('https://mintmanga.live/tokiiskii_gul/vol1/1?mtr=true')

        self.start_stop_button = QPushButton()
        self.start_stop_button.clicked.connect(self.start_stop)

        # TODO: кликабельные ссылки на главы
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.progress = QProgressBar()

        control_layout = QFormLayout()
        control_layout.addRow('Ник:', self.nick_line_edit)
        control_layout.addRow('Url манги:', self.url_line_edit)

        layout.addLayout(control_layout)
        layout.addWidget(self.start_stop_button)
        layout.addWidget(self.log)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.thread = CollectCommentsThread()
        self.thread.about_new_text.connect(self.log.append)
        self.thread.about_progress.connect(self.progress.setValue)
        self.thread.about_range_progress.connect(self.progress.setRange)
        self.thread.started.connect(self._start)
        self.thread.finished.connect(self._finished)

        self._update_states()

    def start_stop(self):
        # Если поток запущен, останавливаем его, иначе -- запускаем
        if self.thread.isRunning():
            self.thread.exit()
        else:
            self.thread.user = self.nick_line_edit.text()
            self.thread.url = self.url_line_edit.text()
            self.thread.start()

        self._update_states()

    def _start(self):
        self.log.clear()
        self.progress.setValue(0)

    def _finished(self):
        self._update_states()

    def _update_states(self):
        self.start_stop_button.setText('Стоп' if self.thread.isRunning() else 'Начать поиск')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)

    def closeEvent(self, event):
        quit()


if __name__ == '__main__':
    app = QApplication([])

    mw = MainWindow()
    mw.resize(650, 500)
    mw.show()

    app.exec()
