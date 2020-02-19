import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, \
    QRadioButton, QGridLayout, QWidget, QApplication, QSizePolicy, QFileDialog, QProgressBar, QMessageBox
from PyQt5.QtGui import QIcon, QFont, QDesktopServices, QColor
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
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
    sin_out_warning = pyqtSignal(str)

    def __init__(self):
        super(ExecIDMThread, self).__init__()
        self.idm_path = ''
        self.urls = []

    def run(self):
        if self.urls:
            os.system(self.idm_path)
        else:
            self.sin_out_warning.emit('请先抓取精轨链接或着等待精轨链接被抓取完毕')


class GetUrlThread(QThread):
    sin_out_process = pyqtSignal(int)
    sin_out_task_num = pyqtSignal(int)
    sin_out_urls = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.images_path = ''
        self.urls = []
        self.url_prefix = 'https://qc.sentinel1.eo.esa.int/aux_poeorb/'
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36\
                     (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    def run(self):
        date_and_mission = ProcessData.get_sentinel1_date_and_mission(self.images_path)
        self.sin_out_task_num.emit(len(date_and_mission))
        for d in date_and_mission:
            url_param_json = {}
            url_param_json['sentinel1__mission'] = d[-3:]
            orbit_date = ProcessData.get_orbit_date(d[0:8])
            url_param_json['validity_start'] = \
                orbit_date[0:4] + '-' + orbit_date[4:6] + '-' + orbit_date[-2:]
            url_param = urllib.parse.urlencode(url_param_json)
            url = self.url_prefix + "?" + url_param
            html = requests.get(url, headers=self.headers)
            dom = BeautifulSoup(html.text, "html.parser")
            eof = re.findall(r"http.*EOF", str(dom))
            self.urls.append(eof[0])
            index = date_and_mission.index(d) + 1
            self.sin_out_process.emit(index)
        self.sin_out_urls.emit(self.urls)


class AddToIDMThread(QThread):
    sin_out_success = pyqtSignal(str)
    sin_out_error_num = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.orbits_path = ''
        self.idm_path = ''
        self.urls = []
        self.error_num = 0

    def run(self):
        if self.urls:
            url_num, error_num = ProcessData.add_to_idm(self.idm_path, self.urls, self.orbits_path)
            if not error_num and url_num:
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.sin_out_success.emit("{} 所有下载任务都被添加到了IDM".format(time))
            elif error_num:
                time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.sin_out_error_num.emit("{} 有 {} 个未被添加到IDM".format(time, error_num))


class TextEdit(QTextEdit):
    def mousePressEvent(self, me):
        super().mousePressEvent(me)
        anchor = self.anchorAt(me.pos())
        if anchor.endswith('.EOF'):
            QDesktopServices.openUrl(QUrl(anchor))


class DownloadOrbit(QWidget):
    def __init__(self):
        super().__init__()
        self.get_urls_thread = GetUrlThread()
        self.add_to_idm_thread = AddToIDMThread()
        self.exec_idm_thread = ExecIDMThread()

        self.setWindowTitle("Download Sentinel-1A/B Precise Orbit")
        self.setFont(QFont('Consolas'))
        self.setWindowIcon(QIcon(':/orbit.ico'))
        # self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.resize(800, 350)
        self.setup_ui()

    def setup_ui(self):
        self.label0 = QLabel('获取精轨日期模式：')
        self.radio_btn1 = QRadioButton('file mode')
        self.radio_btn2 = QRadioButton('dir mode')
        self.radio_btn1.setChecked(True)
        self.label1 = QLabel('文本文件路径：')
        self.images_path = QLineEdit()
        self.images_path.setReadOnly(True)

        self.label2 = QLabel('精轨保存路径：')
        self.orbits_path = QLineEdit()
        self.orbits_path.setReadOnly(True)

        self.label3 = QLabel('IDMan.exe路径：')
        self.idm_path = QLineEdit()
        self.idm_path.setReadOnly(True)

        self.open_images_path = QPushButton('选择路径')
        self.open_images_path.setFixedSize(self.open_images_path.sizeHint())
        self.open_orbits_path = QPushButton('选择路径')
        self.open_idm_path = QPushButton('选择路径')
        self.btn_get_urls = QPushButton('抓取\n精轨链接')
        self.btn_get_urls.setEnabled(False)
        self.btn_get_urls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_add_to_idm = QPushButton('启动IDM\n并添加任务')
        self.btn_add_to_idm.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_add_to_idm.setEnabled(False)
        self.label4 = QLabel('抓取链接进度：')
        self.url_process = QProgressBar()
        self.url_process.setValue(self.url_process.minimum() - 1)
        self.url_process.setFormat("%v/%m")
        self.info = TextEdit()
        self.info.setFontUnderline(False)
        self.info.setTextColor(QColor('black'))
        self.info.setReadOnly(True)
        self.info.setText("@author  : leiyuan \n@version : 3.1\n"
                          "@date    : 2020-01-11\n\n"
                          "file mode: 从'文本文件'获取Sentinel-1A/B影像名，用于获取影像日期，从而获取精轨日期"
                          "\ndir  mode: 从'压缩文件'获取Sentinel-1A/B影像名，用于获取影像日期，从而获取精轨日期"
                          "\n\n温馨提示：为了能够更快地完成任务，请尽量翻越长城")
        # 信号与槽
        self.get_urls_thread.sin_out_urls.connect(self.assign_urls_slot)
        self.get_urls_thread.sin_out_task_num.connect(self.task_num_slot)
        self.get_urls_thread.sin_out_process.connect(lambda value: self.url_process.setValue(value))
        self.exec_idm_thread.sin_out_warning.connect(self.warning_slot)
        self.add_to_idm_thread.sin_out_success.connect(lambda info: self.info.append(info))
        self.add_to_idm_thread.sin_out_error_num.connect(lambda info: self.info.append(info))
        self.url_process.valueChanged.connect(lambda value: self.success_get_slot(value))
        self.images_path.textChanged.connect(self.switch_btn_get_urls_state_slot)
        self.orbits_path.textChanged.connect(
            lambda: self.switch_btn_add_to_idm_state_slot(self.orbits_path, self.idm_path))
        self.idm_path.textChanged.connect(
            lambda: self.switch_btn_add_to_idm_state_slot(self.orbits_path, self.idm_path))
        self.open_orbits_path.clicked.connect(self.get_orbits_path_slot)
        self.open_idm_path.clicked.connect(self.get_idm_path_slot)
        self.open_images_path.clicked.connect(self.get_images_name_by_file_slot)
        self.radio_btn1.toggled.connect(lambda: self.radio_btn_state_slot(self.radio_btn1))
        self.radio_btn2.toggled.connect(lambda: self.radio_btn_state_slot(self.radio_btn2))
        self.btn_add_to_idm.clicked.connect(self.add_to_idm_slot)
        self.btn_get_urls.clicked.connect(lambda: self.get_urls_thread.start())

        # 设置布局
        layout = QGridLayout(self)
        self.setLayout(layout)
        layout.setSpacing(5)
        # 第一行
        layout.addWidget(self.label0, 0, 1, Qt.AlignRight)
        layout.addWidget(self.radio_btn1, 0, 2)
        layout.addWidget(self.radio_btn2, 0, 3)
        # 第二行
        layout.addWidget(self.label1, 1, 1, Qt.AlignRight)
        layout.addWidget(self.images_path, 1, 2, 1, 3)
        layout.addWidget(self.open_images_path, 1, 5)
        layout.addWidget(self.btn_get_urls, 1, 6, 2, 1)
        # 第三行
        layout.addWidget(self.label2, 2, 1, Qt.AlignRight)
        layout.addWidget(self.orbits_path, 2, 2, 1, 3)
        layout.addWidget(self.open_orbits_path, 2, 5)
        # 第四行
        layout.addWidget(self.label3, 3, 1, Qt.AlignRight)
        layout.addWidget(self.idm_path, 3, 2, 1, 3)
        layout.addWidget(self.open_idm_path, 3, 5)
        layout.addWidget(self.btn_add_to_idm, 3, 6, 2, 1)
        # 第五行
        layout.addWidget(self.label4, 4, 1, Qt.AlignRight)
        layout.addWidget(self.url_process, 4, 2, 1, 4)
        # 第六行
        layout.addWidget(self.info, 5, 1, 3, 6)

    def assign_urls_slot(self, urls):
        self.add_to_idm_thread.urls = urls

    def task_num_slot(self, num):
        if num:
            self.url_process.setEnabled(True)
            self.url_process.setMaximum(num)
            self.url_process.setValue(0)
            self.info.clear()
            self.info.setFontUnderline(False)
            self.info.setTextColor(QColor('black'))
            # 添加一个开始锚点
            self.info.append("<a name='begin'></a>")
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.info.insertPlainText("\n{} 需要抓取 {} 个精轨链接\n".format(time, num))
        else:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.info.setText("\n{} 输入文件或者文件夹路径有误，请查看".format(time))
            self.url_process.setEnabled(False)

    def success_get_slot(self, value):
        def get_date(u):
            temp = re.findall(r"\d{8}", u)[-1]
            temp = datetime.datetime(int(temp[:4]), int(temp[4:6]), int(temp[6:]))
            delta = datetime.timedelta(days=-1)
            date = temp + delta
            return date.strftime('%Y%m%d')

        if value == self.url_process.maximum():
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.info.insertPlainText('\n{} 成功抓取所有精轨链接\n\n{}\n\n'.format(time, '*' * 50))
            for url in self.get_urls_thread.urls:
                html = "精轨对应的影像日期（点击右侧日期即可下载）：<a href={}>{}</a>".format(url, get_date(url))
                self.info.insertHtml(html)
                self.info.append('\n')
            self.info.append("<a name='end'>{}</a>\n\n".format("*" * 50))
            self.info.scrollToAnchor('begin')

    def warning_slot(self, info):
        """没有获取链接而点击添加到IDM时，弹出警告信息"""
        mb = QMessageBox(QMessageBox.Warning, "Warning", info, QMessageBox.Ok, self)
        mb.show()

    def add_to_idm_slot(self):
        self.exec_idm_thread.idm_path = self.idm_path.text()
        self.exec_idm_thread.urls = self.add_to_idm_thread.urls
        self.exec_idm_thread.start()
        self.add_to_idm_thread.orbits_path = self.orbits_path.text()
        self.add_to_idm_thread.idm_path = self.idm_path.text()
        self.add_to_idm_thread.start()
        self.info.scrollToAnchor('end')

    def get_images_name_by_dir_slot(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择压缩文件路径', './')
        self.images_path.setText(dir_name)
        self.get_urls_thread.images_path = dir_name

    def get_images_name_by_file_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择文本文件路径', './', 'All files(*.*);;txt file(*.txt)', 'txt file(*.txt)')
        self.images_path.setText(str(file_name[0]))
        self.get_urls_thread.images_path = file_name[0]

    def switch_btn_get_urls_state_slot(self, val):
        if val:
            self.btn_get_urls.setEnabled(True)
        else:
            self.btn_get_urls.setEnabled(False)

    def get_orbits_path_slot(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择精轨保存路径', '../')
        self.orbits_path.setText(dir_name)

    def switch_btn_add_to_idm_state_slot(self, edit1, edit2):
        if edit1.text() and edit2.text():
            self.btn_add_to_idm.setEnabled(True)
        else:
            self.btn_add_to_idm.setEnabled(False)

    def get_idm_path_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe路径', 'C:/thorly/Softwares/IDM', 'IDMan.exe (IDMan.exe)')
        self.idm_path.setText(str(file_name[0]))

    def radio_btn_state_slot(self, radio_btn):
        if radio_btn.text() == 'file mode' and radio_btn.isChecked():
            try:
                self.open_images_path.clicked.disconnect(self.get_images_name_by_dir_slot)
                self.open_images_path.clicked.disconnect(self.get_images_name_by_file_slot)
            except:
                pass
            self.open_images_path.clicked.connect(self.get_images_name_by_file_slot)
            self.label1.setText('文本文件路径：')
        if radio_btn.text() == 'dir mode' and radio_btn.isChecked():
            try:
                self.open_images_path.clicked.disconnect(self.get_images_name_by_file_slot)
                self.open_images_path.clicked.disconnect(self.get_images_name_by_dir_slot)
            except:
                pass
            self.open_images_path.clicked.connect(self.get_images_name_by_dir_slot)
            self.label1.setText('压缩文件路径：')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloadOrbit()
    win.show()
    sys.exit(app.exec_())
