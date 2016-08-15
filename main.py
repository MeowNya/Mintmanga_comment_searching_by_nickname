#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def collect_user_comments(user, url_manga, about_new_text_signal=None):
    """Скрипт ищет комментарии указанного пользователя сайта http://readmanga.me/ и выводит их."""

    from urllib.parse import urljoin
    from lxml import etree
    from urllib.request import urlopen

    with urlopen(url_manga) as rs:
        html = rs.read()

    root = etree.HTML(html)

    xpath = '//*[@id="chapterSelectorSelect"]/option'
    match = root.xpath(xpath)

    number = 0

    # Из комбобокса вытаскиванием список всех глав
    for option in reversed(match):
        title = option.text

        # Относительную ссылку на главу делаем абсолютной
        volume_url = urljoin(url_manga, option.attrib['value'])

        print('Глава "{}": {}'.format(title, volume_url))

        with urlopen(volume_url) as rs:
            html = rs.read()
        root = etree.HTML(html)
        xpath = '//*[@id="twitts"]/div/div'
        match = root.xpath(xpath)

        comments = list()

        # Сбор всех комментариев главы
        for div in match:
            a = div.xpath('a')
            span = div.xpath('span')

            # Возможны div без комментов внутри, поэтому проверяем наличие тегов a (логин) и span (текст)
            if a and span:
                a = a[0].text
                span = span[0].text
                if a == user:
                    comments.append((a, span))

        # Если список не пуст
        if comments:
            number += len(comments)

            if about_new_text_signal:
                about_new_text_signal.emit('Глава "{}": {}'.format(title, volume_url))

            for login, text in comments:
                print('  {}: {}'.format(login, text))
                if about_new_text_signal:
                    about_new_text_signal.emit('  {}: {}'.format(login, text))

            print()
            if about_new_text_signal:
                about_new_text_signal.emit('')

    print()
    print('Найдено {} комментов "{}".'.format(number, user))
    if about_new_text_signal:
        about_new_text_signal.emit('')
        about_new_text_signal.emit('Найдено {} комментов "{}".'.format(number, user))


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class MyThread(QThread):
    about_new_text = pyqtSignal(str)

    def __init__(self, user, url):
        super().__init__()

        self.user = user
        self.url = url

    def run(self):
        try:
            print('run 1')
            collect_user_comments(self.user, self.url, self.about_new_text)
            print('run 2')
        except Exception as e:
            print(e)


class MainWindow(QWidget):
    # __init__ -- конструктор
    def __init__(self):
        # super() -- обращение к предку, т.е. в данном классе к QWidget и у него вызываем конструктор
        super().__init__()

        self.setWindowTitle('Test foo')

        layout = QVBoxLayout()

        self.nick_line_edit = QLineEdit()
        self.nick_line_edit.setText('Rihoko7')

        self.url_line_edit = QLineEdit()
        self.url_line_edit.setText('http://mintmanga.com/tokyo_ghoul/vol1/1?mature=1')

        self.go_button = QPushButton('Начать поиск')
        self.go_button.clicked.connect(self.go)

        self.text_comm = QTextEdit()
        self.text_comm.setReadOnly(True)

        control_layout = QFormLayout()
        control_layout.addRow('Ник:', self.nick_line_edit)
        control_layout.addRow('Url манги:', self.url_line_edit)

        layout.addLayout(control_layout)
        layout.addWidget(self.go_button)
        layout.addWidget(self.text_comm)
        self.setLayout(layout)

        self.thread = None
        self.go()

    def go(self):
        try:
            user = self.nick_line_edit.text()
            url_manga = self.url_line_edit.text()

            self.thread = MyThread(user, url_manga)
            self.thread.about_new_text.connect(self.text_comm.append)
            self.thread.start()
        except Exception as e:
            print(e)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)

    def closeEvent(self, event):
        quit()


if __name__ == '__main__':
    app = QApplication([])

    mw = MainWindow()
    mw.show()

    app.exec()
