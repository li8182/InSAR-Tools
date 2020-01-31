import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, \
    QRadioButton, QGridLayout, QWidget, QApplication, QSizePolicy, QFileDialog, QProgressBar
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from bs4 import BeautifulSoup
from subprocess import call
import requests
import datetime
import urllib
import re
import resource_rc


class ProcessData:
    @staticmethod
    def get_orbit_date(date):
        """
        :param date: date of Sentinel-1A/B
        :return: date of orbit
        """
        image_date = datetime.datetime(int(date[0:4]),
                                       int(date[4:6]), int(date[6:8]))
        delta = datetime.timedelta(days=-1)
        orbit_date = image_date + delta
        return orbit_date.strftime('%Y%m%d')

    @staticmethod
    def get_sentinel1_date_and_mission1(images_path):
        """
        :param images_path: path of directory including Sentinel-1A/B (.zip)
        :return: date and mission (list)
        """
        images_date_and_mission = []
        files = os.listdir(images_path)
        for file in files:
            if file.endswith('.zip'):
                date_and_mission = re.findall(r"\d{8}", file)[0] + file[0:3]
                if date_and_mission not in images_date_and_mission:
                    images_date_and_mission.append(date_and_mission)
        return images_date_and_mission

    @staticmethod
    def get_sentinel1_date_and_mission2(txt_path):
        """
        :param txt_path: path of file including Sentinel-1A/B names
        :return: date and mission (list)
        """
        images_date_and_mission = []
        with open(txt_path, encoding='utf-8') as file:
            for f in file:
                if re.search(r'S1\w{65}', f):
                    date_and_mission = re.findall(r"\d{8}", f)[0] + f[0:3]
                    if date_and_mission not in images_date_and_mission:
                        images_date_and_mission.append(date_and_mission)
        return images_date_and_mission

    @staticmethod
    def get_sentinel1_date_and_mission(path):
        """
        :param path: path of directory or file
        :return: date and mission
        """
        if os.path.isdir(path):
            return ProcessData.get_sentinel1_date_and_mission1(path)
        else:
            return ProcessData.get_sentinel1_date_and_mission2(path)

    @staticmethod
    def add_to_idm(idm_path, urls, save_path):
        """
        :param idm_path: path of IDMan.exe
        :param urls: urls of orbits
        :param save_path: path of saving orbits
        :return: num of urls and error
        """
        download_urls = urls
        idm = idm_path
        error_num = 0
        for i in range(len(download_urls)):
            try:
                call([
                    idm, '/d', download_urls[i], '/p', save_path, '/f',
                    download_urls[i].split('/')[-1][:-4] + '.EOF', '/n', '/a'
                ])
            except:
                error_num += 1
        return len(download_urls), error_num


class ExecIDMThread(QThread):
    def __init__(self):
        super(ExecIDMThread, self).__init__()
        self.idm_path = ''

    def run(self):
        os.system(self.idm_path)


class DownloadThread(QThread):
    sin_out_process = pyqtSignal(int)
    sin_out_task_num = pyqtSignal(int)
    sin_out_success = pyqtSignal(str)
    sin_out_error_num = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.images_path = ''
        self.orbits_path = ''
        self.idm_path = ''
        self.error_num = 0

    def get_download_urls(self, date_and_mission):
        """
        :param date_and_mission: Sentinel-1A/B date and mission
        :return: urls of orbits
        """
        urls = []
        url_prefix = 'https://qc.sentinel1.eo.esa.int/aux_poeorb/'
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36\
                     (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }
        for d in date_and_mission:
            url_param_json = {}
            url_param_json['sentinel1__mission'] = d[-3:]
            orbit_date = ProcessData.get_orbit_date(d[0:8])
            url_param_json['validity_start'] = \
                orbit_date[0:4] + '-' + orbit_date[4:6] + '-' + orbit_date[-2:]
            url_param = urllib.parse.urlencode(url_param_json)
            url = url_prefix + "?" + url_param
            html = requests.get(url, headers=headers)
            dom = BeautifulSoup(html.text, "html.parser")
            eof = re.findall(r"http.*EOF", str(dom))
            urls.append(eof[0])
            index = date_and_mission.index(d) + 1
            self.sin_out_process.emit(index)
        return urls

    def run(self):
        images_date_and_mission = ProcessData.get_sentinel1_date_and_mission(
            self.images_path)
        self.sin_out_task_num.emit(len(images_date_and_mission))
        urls = self.get_download_urls(images_date_and_mission)
        url_num, error_num = ProcessData.add_to_idm(self.idm_path, urls, self.orbits_path)
        if error_num == 0 and url_num != 0:
            self.sin_out_success.emit(
                '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 所有下载任务都被添加到了IDM')
        elif error_num != 0:
            self.sin_out_error_num.emit(
                '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 有' + str(error_num) + '未添加到IDM')


class DownloadOrbit(QWidget):
    def __init__(self):
        super().__init__()
        self.download_thread = DownloadThread()
        self.exec_idm_thread = ExecIDMThread()

        self.setWindowTitle("Download Sentinel-1A/B Precise Orbit by IDM")
        self.setFont(QFont('Consolas'))
        self.setWindowIcon(QIcon(':/orbit.ico'))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.resize(800, 350)

        self.label0 = QLabel('获取精轨日期模式: ', self)
        self.radio_btn1 = QRadioButton('file mode', self)
        self.radio_btn2 = QRadioButton('dir mode', self)
        self.radio_btn1.setChecked(True)
        self.label1 = QLabel('文本文件路径:', self)
        self.images_path = QLineEdit(self)
        self.images_path.setReadOnly(True)
        self.label1.setBuddy(self.images_path)
        self.label2 = QLabel('精轨保存路径:', self)
        self.orbits_path = QLineEdit(self)
        self.orbits_path.setReadOnly(True)
        self.label2.setBuddy(self.orbits_path)
        self.label3 = QLabel('IDMan.exe路径:', self)
        self.idm_path = QLineEdit(self)
        self.idm_path.setReadOnly(True)
        self.label3.setBuddy(self.idm_path)
        self.open_images_path = QPushButton('打开')
        self.open_images_path.setFixedSize(self.open_images_path.sizeHint())
        self.open_orbits_path = QPushButton('打开')
        self.open_idm_path = QPushButton('打开')
        self.btn_add_to_idm = QPushButton('抓取链接\n\n并添加到IDM')
        self.btn_add_to_idm.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_add_to_idm.setEnabled(False)
        self.label4 = QLabel('抓取链接进度：', self)
        self.url_process = QProgressBar(self)
        self.url_process.setValue(0)
        self.info = QTextEdit(self)
        self.info.setReadOnly(True)
        self.info.setText("@author  : leiyuan \n@version : 3.1\n"
                          "@date    : 2020-01-11\n\n"
                          "file mode: 从'文本文件'获取Sentinel-1A/B影像名，用于获取影像日期，从而获取精轨日期"
                          "\ndir  mode: 从'压缩文件'获取Sentinel-1A/B影像名，用于获取影像日期，从而获取精轨日期"
                          "\n\n温馨提示：为了能够更快地完成任务，请尽量翻越长城")
        # 信号与槽
        self.download_thread.sin_out_task_num.connect(lambda num: self.task_num_slot(num))
        self.download_thread.sin_out_process.connect(lambda value: self.url_process.setValue(value))
        self.download_thread.sin_out_success.connect(lambda info: self.info.append(info))
        self.download_thread.sin_out_error_num.connect(lambda info: self.info.append(info))
        self.url_process.valueChanged.connect(lambda value: self.success_get_slot(value))
        self.open_orbits_path.clicked.connect(self.get_orbits_path_slot)
        self.open_idm_path.clicked.connect(self.get_idm_path_slot)
        self.open_images_path.clicked.connect(self.get_images_name_by_file_slot)
        self.radio_btn1.toggled.connect(lambda: self.radio_btn_state_slot(self.radio_btn1))
        self.radio_btn2.toggled.connect(lambda: self.radio_btn_state_slot(self.radio_btn2))
        self.btn_add_to_idm.clicked.connect(self.start_thread_slot)
        # layout setting
        layout = QGridLayout(self)
        self.setLayout(layout)
        layout.setSpacing(5)
        # 第一行
        layout.addWidget(self.label0, 0, 1)
        layout.addWidget(self.radio_btn1, 0, 2)
        layout.addWidget(self.radio_btn2, 0, 3)
        # 第二行
        layout.addWidget(self.label1, 1, 1)
        layout.addWidget(self.images_path, 1, 2, 1, 3)
        layout.addWidget(self.open_images_path, 1, 5)
        layout.addWidget(self.btn_add_to_idm, 1, 6, 4, 1)
        # 第三行
        layout.addWidget(self.label2, 2, 1)
        layout.addWidget(self.orbits_path, 2, 2, 1, 3)
        layout.addWidget(self.open_orbits_path, 2, 5)
        # 第四行
        layout.addWidget(self.label3, 3, 1)
        layout.addWidget(self.idm_path, 3, 2, 1, 3)
        layout.addWidget(self.open_idm_path, 3, 5)
        # 第五行
        layout.addWidget(self.label4, 4, 1)
        layout.addWidget(self.url_process, 4, 2, 1, 4)
        # 第六行
        layout.addWidget(self.info, 5, 1, 3, 6)

    def task_num_slot(self, num):
        if num != 0:
            self.info.setText(
                '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 需要抓取 ' + str(num) + ' 个精轨链接')
            self.url_process.setEnabled(True)
            self.url_process.setMaximum(num)
        else:
            self.info.setText(
                '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 输入文件或者文件夹路径有误，请查看')
            self.url_process.setEnabled(False)

    def success_get_slot(self, value):
        if value == self.url_process.maximum():
            self.info.append('\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 成功抓取所有精轨链接，开始添加到IDM')

    def start_thread_slot(self):
        self.url_process.setValue(0)
        self.download_thread.images_path = self.images_path.text()
        self.download_thread.orbits_path = self.orbits_path.text()
        self.download_thread.idm_path = self.idm_path.text()
        self.download_thread.start()

    def get_images_name_by_dir_slot(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择压缩文件路径', '../')
        self.images_path.setText(dir_name)
        self.switch_btn_state(self.images_path, self.orbits_path, self.idm_path)

    def get_images_name_by_file_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择文本文件路径', './', 'All files(*.*);;txt file(*.txt)', 'txt file(*.txt)')
        self.images_path.setText(str(file_name[0]))
        self.switch_btn_state(self.images_path, self.orbits_path, self.idm_path)

    def get_orbits_path_slot(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择精轨保存路径', '../')
        self.orbits_path.setText(dir_name)
        self.switch_btn_state(self.images_path, self.orbits_path, self.idm_path)

    def switch_btn_state(self, edit1, edit2, edit3):
        if edit1.text() and edit2.text() and edit3.text():
            self.btn_add_to_idm.setEnabled(True)
        else:
            self.btn_add_to_idm.setEnabled(False)

    def get_idm_path_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe路径', 'C:/thorly/software/IDM', 'IDMan.exe (IDMan.exe)')
        self.idm_path.setText(str(file_name[0]))
        self.switch_btn_state(self.images_path, self.orbits_path, self.idm_path)
        self.exec_idm_thread.idm_path = file_name[0]
        self.exec_idm_thread.start()

    def radio_btn_state_slot(self, radio_btn):
        if radio_btn.text() == 'file mode' and radio_btn.isChecked():
            try:
                self.open_images_path.clicked.disconnect(self.get_images_name_by_dir_slot)
                self.open_images_path.clicked.disconnect(self.get_images_name_by_file_slot)
            except:
                pass
            self.open_images_path.clicked.connect(self.get_images_name_by_file_slot)
            self.label1.setText('文本文件路径:')
        if radio_btn.text() == 'dir mode' and radio_btn.isChecked():
            try:
                self.open_images_path.clicked.disconnect(self.get_images_name_by_file_slot)
                self.open_images_path.clicked.disconnect(self.get_images_name_by_dir_slot)
            except:
                pass
            self.open_images_path.clicked.connect(self.get_images_name_by_dir_slot)
            self.label1.setText('压缩文件路径:')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloadOrbit()
    win.show()
    sys.exit(app.exec_())
