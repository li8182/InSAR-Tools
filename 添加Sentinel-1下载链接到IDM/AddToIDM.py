#!coding = utf-8
import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, \
    QGridLayout, QWidget, QApplication, QSizePolicy, QFileDialog
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import datetime
import time
import re
import resource_rc
from subprocess import call


class ExecIDM(QThread):
    def __init__(self):
        super(ExecIDM, self).__init__()
        self.idm_path = ''

    def run(self):
        os.system(self.idm_path)


class AddThread(QThread):
    sin_out_file_error = pyqtSignal(str)
    sin_out_task_num = pyqtSignal(str)
    sin_out_success = pyqtSignal(str)
    sin_out_error_num = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.idm_path = ''
        self.url_path = ''
        self.save_path = ''
        self.error_num = 0
        self.key_name = r'S1\w{65}'
        self.key_url = r'https.*value'

    @staticmethod
    def find_sth_from_file(file_path, key_name):
        with open(file_path) as f:
            content = f.read()
            return re.findall(re.compile(key_name), content)

    def run(self):
        url = AddThread.find_sth_from_file(self.url_path, self.key_url)
        name = AddThread.find_sth_from_file(self.url_path, self.key_name)
        if len(url) != len(name):
            self.sin_out_file_error.emit('\n下载链接文件格式错误，无法添加到IDM')
            return None
        self.sin_out_task_num.emit('\n需要添加 ' + str(len(url)) + ' 个下载任务到IDM')
        for i, j in zip(url, name):
            try:
                call([
                    self.idm_path, '/d', i, '/p', self.save_path, '/f',
                    j + '.zip', '/n', '/a'
                ])
            except:
                self.error_num += 1
        if not self.error_num:
            self.sin_out_success.emit('\n所有下载任务都被添加到了IDM')
        else:
            self.sin_out_error_num.emit('\n有 ' + str(self.error_num) + ' 未添加到IDM')


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('添加 Sentinel-1A/B 下载链接到 IDM')
        self.setWindowIcon(QIcon(':/url.ico'))
        self.setFont(QFont('Consolas'))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.add_thread = AddThread()
        self.exec_idm_thread = ExecIDM()
        self.resize(700, 300)
        self.setup_ui()

    def setup_ui(self):
        label_idm = QLabel('IDMan.exe路径：', self)
        label_url = QLabel('S1下载链接路径：', self)
        label_save = QLabel('S1影像保存路径：', self)
        self.le_idm = QLineEdit(self)
        self.le_url = QLineEdit(self)
        self.le_save = QLineEdit(self)
        self.btn_idm = QPushButton('打开', self)
        self.btn_url = QPushButton('打开', self)
        self.btn_save = QPushButton('打开', self)
        self.btn_add = QPushButton('添加', self)
        self.ted_info = QTextEdit(self)
        self.ted_info.setText("@author  : leiyuan \n@version : 2.1\n"
                              "@date    : 2020-01-30\n")

        self.le_url.setReadOnly(True)
        self.le_idm.setReadOnly(True)
        self.ted_info.setReadOnly(True)
        self.btn_add.setEnabled(False)
        self.btn_idm.setFixedSize(self.btn_idm.sizeHint())
        self.btn_url.setFixedSize(self.btn_url.sizeHint())
        self.btn_add.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # 设置布局
        layout = QGridLayout()
        self.setLayout(layout)
        # 第一行
        layout.addWidget(label_idm, 0, 0)
        layout.addWidget(self.le_idm, 0, 1, 1, 3)
        layout.addWidget(self.btn_idm, 0, 4)
        layout.addWidget(self.btn_add, 0, 5, 3, 1)
        # 第二行
        layout.addWidget(label_url, 1, 0)
        layout.addWidget(self.le_url, 1, 1, 1, 3)
        layout.addWidget(self.btn_url, 1, 4)
        # 第三行
        layout.addWidget(label_save, 2, 0)
        layout.addWidget(self.le_save, 2, 1, 1, 3)
        layout.addWidget(self.btn_save, 2, 4)
        # 第四行
        layout.addWidget(self.ted_info, 3, 0, 1, 6)

        # 信号与槽
        self.btn_idm.clicked.connect(self.get_idm_slot)
        self.btn_url.clicked.connect(self.get_url_slot)
        self.btn_save.clicked.connect(self.get_save_slot)
        self.btn_add.clicked.connect(self.start_thread_slot)
        self.le_idm.textChanged.connect(lambda: self.set_btn_add_state_slot(self.le_idm, self.le_url, self.le_save))
        self.le_url.textChanged.connect(lambda: self.set_btn_add_state_slot(self.le_idm, self.le_url, self.le_save))
        self.le_save.textChanged.connect(lambda: self.set_btn_add_state_slot(self.le_idm, self.le_url, self.le_save))

        self.add_thread.sin_out_error_num.connect(lambda info: self.ted_info.append(info))
        self.add_thread.sin_out_success.connect(lambda info: self.ted_info.append(info))
        self.add_thread.sin_out_task_num.connect(lambda info: self.ted_info.append(info))
        self.add_thread.sin_out_file_error.connect(lambda info: self.ted_info.append(info))

    def get_idm_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择 IDMan.exe', r'C:\thorly\software\IDM', 'IDMan.exe(IDMan.exe)'
        )
        self.le_idm.setText(file_name[0])
        self.exec_idm_thread.idm_path = file_name[0]
        self.exec_idm_thread.start()

    def get_url_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择 S1 下载链接文件', './', 'All files(*.*);;txt file(*.txt)', 'txt file(*.txt)'
        )
        self.le_url.setText(file_name[0])

    def get_save_slot(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择保存路径', '../'
        )
        self.le_save.setText(dir_name)

    def set_btn_add_state_slot(self, le1, le2, le3):
        if le1.text() and le2.text() and le3.text():
            self.btn_add.setEnabled(True)
        else:
            self.btn_add.setEnabled(False)

    def start_thread_slot(self):
        self.add_thread.idm_path = self.le_idm.text()
        self.add_thread.url_path = self.le_url.text()
        self.add_thread.save_path = self.le_save.text()
        self.add_thread.start()
        # self.btn_add.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
