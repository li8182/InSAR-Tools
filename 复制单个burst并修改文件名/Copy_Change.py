# -*- coding: utf-8 -*-
import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, \
    QGridLayout, QWidget, QApplication, QSizePolicy, QFileDialog
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import datetime
import shutil
import re
import resource_rc


class ProcessFile:
    @staticmethod
    def get_date_burst(burst_info_path):
        """
        :param burst_info_path: file including date and burst info of S1 (str)
        :return: date and burst information (dict)
        """
        date_burst = {}
        with open(burst_info_path) as file:
            for line in file:
                if line:
                    text = re.split(r'\s+', line.strip())
                    date_burst[text[0]] = text[1]
        return date_burst

    @staticmethod
    def copy_change_filename(file_path, date, burst, save_path):
        """
        :param file_path: directory of ENVI imported data (str)
        :param date: date of S1 (str)
        :param burst: burst information of S1 (str)
        :param save_path: directory of saving slc (str)
        :return:
        """
        files = os.listdir(file_path)
        for file in files:
            abs_path = os.path.join(file_path, file)  # burst所在文件夹路径
            if date in file and os.path.isdir(abs_path) and 'VV' in file:
                # 该文件夹下所有burst文件
                iw_files = os.listdir(os.path.join(file_path, file))
                for f in iw_files:
                    if not f.endswith('.enp'):
                        if burst in f:
                            old_path = os.path.join(os.path.join(file_path, file), f)
                            new_path = os.path.join(save_path, f.replace(burst, date))
                            shutil.copy(old_path, new_path)


class CopyThread(QThread):
    sin_out_start = pyqtSignal(str)
    sin_out_finish = pyqtSignal(str)
    sin_out_time = pyqtSignal(str)

    def __init__(self):
        super(CopyThread, self).__init__()
        self.burst_path = ''
        self.save_path = ''
        self.imported_path = ''

    def run(self):
        start_time = datetime.datetime.now()
        date_burst_dict = ProcessFile.get_date_burst(self.burst_path)
        self.sin_out_start.emit('需要复制并重命名 ' + str(len(date_burst_dict)) + ' * 9 个文件\n')
        for i, j in date_burst_dict.items():
            j = 'burst_IW' + j[0] + '_' + j[-1:]
            ProcessFile.copy_change_filename(self.imported_path, i, j, self.save_path)
        end_time = datetime.datetime.now()
        self.sin_out_finish.emit('最终复制并重命名了 ' + str(len(os.listdir(self.save_path)) // 9) + ' * 9 个文件\n')
        self.sin_out_time.emit('耗时 ' + str((end_time - start_time).seconds) + ' 秒\n')


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('复制单个 burst 到指定文件夹并重命名')
        self.setWindowIcon(QIcon(':/copy.ico'))
        self.setFont(QFont('Consolas'))
        self.resize(850, 340)
        self.thread = CopyThread()
        self.setup_ui()

    def setup_ui(self):
        # 添加控件
        self.label1 = QLabel('burst 信息文件：', self)
        self.label2 = QLabel('保存文件路径：', self)
        self.label3 = QLabel('ENVI 导出文件路径：', self)
        self.le_burst_path = QLineEdit(self)
        self.le_burst_path.setReadOnly(True)
        self.le_saving_path = QLineEdit(self)
        self.le_saving_path.setReadOnly(True)
        self.le_imported_path = QLineEdit(self)
        self.le_imported_path.setReadOnly(True)

        self.btn_burst = QPushButton('选择文件', self)
        self.btn_saving = QPushButton('选择路径', self)
        self.btn_import = QPushButton('选择路径', self)
        self.btn_start = QPushButton('开始复制', self)
        self.btn_start.setEnabled(False)
        self.btn_start.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.ted_info = QTextEdit(self)
        self.ted_info.setReadOnly(True)
        self.ted_info.setText(
            "@author  : leiyuan \n@version : 2.12\n"
            "@date    : 2020-02-04\n\n"
            "burst信息文件说明:文件中含有两列数据(date和burst)，每行以空格作为分隔符，"
            "date表示日期，burst表示相关信息。\n\n"
            "以下示例数据中，20200102表示影像日期，19代表burst_IW1_9；"
            "20200103表示影像日期，110代表burst_IW1_10\n\n"
            "20200102 19\n20200103 110")
        # 设置布局
        layout = QGridLayout()
        layout.setSpacing(5)
        layout.addWidget(self.label1, 0, 1, Qt.AlignRight)
        layout.addWidget(self.le_burst_path, 0, 2, 1, 3)
        layout.addWidget(self.btn_burst, 0, 5)
        self.btn_burst.setFixedSize(self.btn_burst.sizeHint())

        layout.addWidget(self.label3, 1, 1, Qt.AlignRight)
        layout.addWidget(self.le_imported_path, 1, 2, 1, 3)
        layout.addWidget(self.btn_import, 1, 5)

        layout.addWidget(self.label2, 2, 1, Qt.AlignRight)
        layout.addWidget(self.le_saving_path, 2, 2, 1, 3)
        layout.addWidget(self.btn_saving, 2, 5)

        layout.addWidget(self.btn_start, 0, 6, 3, 1)
        layout.addWidget(self.ted_info, 3, 1, 1, 6)
        self.setLayout(layout)
        # 设置信号与槽连接
        self.btn_burst.clicked.connect(self.get_burst_slot)
        self.btn_saving.clicked.connect(self.get_saving_slot)
        self.btn_import.clicked.connect(self.get_imported_slot)
        self.le_imported_path.textChanged.connect(
            lambda: self.set_state_slot(self.le_burst_path, self.le_saving_path, self.le_imported_path))
        self.le_saving_path.textChanged.connect(
            lambda: self.set_state_slot(self.le_burst_path, self.le_saving_path, self.le_imported_path))
        self.le_burst_path.textChanged.connect(
            lambda: self.set_state_slot(self.le_burst_path, self.le_saving_path, self.le_imported_path))
        self.thread.sin_out_start.connect(lambda info: self.ted_info.setText(info))
        self.thread.sin_out_finish.connect(lambda info: self.ted_info.append(info))
        self.thread.sin_out_time.connect(lambda info: self.ted_info.append(info))
        self.btn_start.clicked.connect(self.start_thread_slot)

    def start_thread_slot(self):
        """开始复制文件"""
        self.thread.burst_path = self.le_burst_path.text()
        self.thread.imported_path = self.le_imported_path.text()
        self.thread.save_path = self.le_saving_path.text()
        self.thread.start()

    def set_state_slot(self, le1, le2, le3):
        """设置开始复制按钮是否可用"""
        if le1.text() and le2.text() and le3.text():
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

    def get_burst_slot(self):
        """打开对话框，选择burst信息文件"""
        file_name = QFileDialog.getOpenFileName(
            self, '选择burst信息文件', './', 'All files(*.*);;txt file(*.txt)', 'txt file(*.txt)')
        self.le_burst_path.setText(file_name[0])

    def get_saving_slot(self):
        """打开对话框，选择保存路径"""
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择保存路径', './')
        self.le_saving_path.setText(dir_name)

    def get_imported_slot(self):
        """打开对话框，选择ENVI导出文件路径"""
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择ENVI导出路径', '../')
        self.le_imported_path.setText(dir_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
