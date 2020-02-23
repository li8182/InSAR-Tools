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


class QSSTool:
    @staticmethod
    def set_qss_to_obj(qss_path, obj):
        with open(qss_path, 'r') as f:
            obj.setStyleSheet(f.read())


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

    def run(self):
        os.system(self.idm_path)


class GetUrlThread(QThread):
    sin_out_process = pyqtSignal(int)
    sin_out_task_num = pyqtSignal(int)
    sin_out_urls = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.image_path = ''
        self.urls = []
        self.url_prefix = 'https://qc.sentinel1.eo.esa.int/aux_poeorb/'
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36\
                     (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    def run(self):
        date_and_mission = ProcessData.get_sentinel1_date_and_mission(self.image_path)
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
        self.le_orbit_path = ''
        self.idm_path = ''
        self.urls = []
        self.error_num = 0

    def run(self):
        if self.urls:
            url_num, error_num = ProcessData.add_to_idm(self.idm_path, self.urls, self.le_orbit_path)
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
        self.resize(800, 400)
        self.setup_ui()

    def setup_ui(self):
        self.label_mode = QLabel('获取精轨日期模式：')
        self.radio_btn_file = QRadioButton('file mode')
        self.radio_btn_dir = QRadioButton('dir mode')
        self.radio_btn_file.setChecked(True)
        self.label_type = QLabel('文本文件路径：')
        self.le_image_path = QLineEdit()
        self.label_orbit = QLabel('精轨保存路径：')
        self.le_orbit_path = QLineEdit()
        self.label_idm = QLabel('IDMan.exe路径：')
        self.le_idm_path = QLineEdit()
        self.btn_image_path = QPushButton('选择路径')
        self.btn_image_path.setFixedSize(self.btn_image_path.sizeHint())
        self.btn_orbit_path = QPushButton('选择路径')
        self.btn_orbit_path.setFixedSize(self.btn_orbit_path.sizeHint())
        self.btn_idm_path = QPushButton('选择路径')
        self.btn_idm_path.setFixedSize(self.btn_idm_path.sizeHint())
        self.btn_get_urls = QPushButton('抓取精轨链接')
        self.btn_add_to_idm = QPushButton('启动IDM\n 并添加任务 ')
        self.btn_add_to_idm.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_get_urls.setObjectName('btn_get_urls')
        self.btn_add_to_idm.setObjectName('btn_add_to_idm')
        self.btn_idm_path.setObjectName('btn_idm_path')
        self.btn_image_path.setObjectName('btn_image_path')
        self.btn_orbit_path.setObjectName('btn_orbit_path')
        self.label_progress = QLabel('抓取链接进度：')
        self.pb_progress = QProgressBar()
        self.pb_progress.setValue(self.pb_progress.minimum() - 1)
        self.pb_progress.setFormat("%v/%m")
        self.ted_info = TextEdit()
        self.ted_info.setFontUnderline(False)
        self.ted_info.setTextColor(QColor('black'))
        self.ted_info.setReadOnly(True)
        self.ted_info.setText("@author  : leiyuan \n@version : 3.5\n"
                              "@date    : 2020-02-23\n\n"
                              "file mode: 从'文本文件'获取Sentinel-1A/B影像名，用于获取影像日期，从而获取精轨日期"
                              "\ndir  mode: 从'压缩文件'获取Sentinel-1A/B影像名，用于获取影像日期，从而获取精轨日期"
                              "\n\n温馨提示：为了能够更快地完成任务，请尽量翻越长城")
        # 设置布局
        layout = QGridLayout(self)
        self.setLayout(layout)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(4, 1)
        # 第一行
        layout.addWidget(self.label_mode, 0, 1, Qt.AlignRight)
        layout.addWidget(self.radio_btn_file, 0, 2)
        layout.addWidget(self.radio_btn_dir, 0, 3)
        # 第二行
        layout.addWidget(self.label_type, 1, 1, Qt.AlignRight)
        layout.addWidget(self.le_image_path, 1, 2, 1, 3)
        layout.addWidget(self.btn_image_path, 1, 5)
        layout.addWidget(self.btn_get_urls, 1, 6, 1, 2)
        # 第三行
        layout.addWidget(self.label_orbit, 2, 1, Qt.AlignRight)
        layout.addWidget(self.le_orbit_path, 2, 2, 1, 3)
        layout.addWidget(self.btn_orbit_path, 2, 5)
        layout.addWidget(self.btn_add_to_idm, 2, 6, 2, 2)
        # 第四行
        layout.addWidget(self.label_idm, 3, 1, Qt.AlignRight)
        layout.addWidget(self.le_idm_path, 3, 2, 1, 3)
        layout.addWidget(self.btn_idm_path, 3, 5)
        # 第五行
        layout.addWidget(self.label_progress, 4, 1, Qt.AlignRight)
        layout.addWidget(self.pb_progress, 4, 2, 1, 6)
        # 第六行
        layout.addWidget(self.ted_info, 5, 1, 3, 7)

        # 信号与槽
        self.btn_get_urls.clicked.connect(self.get_urls)
        self.get_urls_thread.sin_out_task_num.connect(self.task_num)
        self.get_urls_thread.sin_out_process.connect(lambda value: self.pb_progress.setValue(value))
        self.get_urls_thread.sin_out_urls.connect(self.assign_urls)
        self.exec_idm_thread.sin_out_warning.connect(self.warning)
        self.add_to_idm_thread.sin_out_success.connect(self.success_add_to_idm)
        self.add_to_idm_thread.sin_out_error_num.connect(self.error_add_to_idm)
        self.pb_progress.valueChanged.connect(lambda value: self.success_get_urls(value))
        self.btn_orbit_path.clicked.connect(self.get_orbit_path)
        self.btn_idm_path.clicked.connect(self.get_idm_path)
        self.btn_image_path.clicked.connect(self.get_images_name_by_file)
        self.radio_btn_file.toggled.connect(lambda: self.switch_btn_slot(self.radio_btn_file))
        self.radio_btn_dir.toggled.connect(lambda: self.switch_btn_slot(self.radio_btn_dir))
        self.btn_add_to_idm.clicked.connect(self.add_to_idm)

    def warning(self, info):
        """弹出警告信息"""
        mb = QMessageBox(QMessageBox.Warning, "Warning", info, QMessageBox.Ok, self)
        mb.show()

    def assign_urls(self, urls):
        self.add_to_idm_thread.urls = urls

    def task_num(self, num):
        if num:
            self.pb_progress.setEnabled(True)
            self.pb_progress.setMaximum(num)
            self.pb_progress.setValue(0)
            self.ted_info.clear()
            self.ted_info.setFontUnderline(False)
            self.ted_info.setTextColor(QColor('black'))
            # 添加一个开始锚点
            self.ted_info.append("<a name='begin'></a>")
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.ted_info.insertPlainText("{} 需要抓取 {} 个精轨链接\n".format(time, num))
        else:
            self.warning("未找到哨兵影像名，请重新设置{}".format(self.label_type.text()[:-1]))
            self.pb_progress.setEnabled(False)

    def success_add_to_idm(self, info):
        self.ted_info.setFontUnderline(False)
        self.ted_info.setTextColor(QColor('black'))
        self.ted_info.append(info)

    def error_add_to_idm(self, info):
        self.ted_info.setFontUnderline(False)
        self.ted_info.setTextColor(QColor('black'))
        self.ted_info.append(info)

    def success_get_urls(self, value):
        def get_date(u):
            temp = re.findall(r"\d{8}", u)[-1]
            temp = datetime.datetime(int(temp[:4]), int(temp[4:6]), int(temp[6:]))
            delta = datetime.timedelta(days=-1)
            date = temp + delta
            return date.strftime('%Y%m%d')

        if value == self.pb_progress.maximum():
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.ted_info.insertPlainText('\n{} 成功抓取所有精轨链接\n\n{}\n\n'.format(time, '*' * 50))
            for url in self.get_urls_thread.urls:
                html = "精轨对应的影像日期（点击右侧日期即可下载）：<a href={}>{}</a>".format(url, get_date(url))
                self.ted_info.insertHtml(html)
                self.ted_info.append('\n')
            self.ted_info.append("<a name='end'>{}</a>\n\n".format("*" * 50))
            self.ted_info.scrollToAnchor('begin')

    def add_to_idm(self):
        idm_path = self.le_idm_path.text()
        orbit_path = self.le_orbit_path.text()
        if not idm_path and not orbit_path:
            self.warning("请设置精轨保存路径和IDMan.exe路径")
        elif not idm_path and orbit_path:
            self.warning("请设置IDMan.exe路径")
        elif not orbit_path and idm_path:
            self.warning("请设置精轨保存路径")
        elif not os.path.exists(orbit_path) and not os.path.exists(idm_path):
            self.warning("精轨保存路径和IDMan.exe路径不存在，请重新设置")
        elif not os.path.exists(orbit_path):
            self.warning("精轨保存路径不存在，请重新设置")
        elif not os.path.exists(idm_path):
            self.warning("IDMan.exe路径不存在，请重新设置")
        else:
            self.exec_idm_thread.idm_path = idm_path
            self.add_to_idm_thread.le_orbit_path = orbit_path
            self.add_to_idm_thread.idm_path = idm_path
            if self.add_to_idm_thread.urls:
                self.exec_idm_thread.start()
                self.add_to_idm_thread.start()
                self.ted_info.scrollToAnchor('end')
            else:
                self.warning("请先抓取精轨链接")

    def get_images_name_by_dir(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择压缩文件路径', './')
        if dir_name:
            self.le_image_path.setText(dir_name)
        self.get_urls_thread.image_path = self.le_image_path.text()

    def get_images_name_by_file(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择文本文件路径', './示例文件', 'All files(*.*);;txt file(*.txt)', 'txt file(*.txt)')
        if file_name[0]:
            self.le_image_path.setText(str(file_name[0]))
        self.get_urls_thread.image_path = self.le_image_path.text()

    def get_orbit_path(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择精轨保存路径', '../')
        self.le_orbit_path.setText(dir_name)

    def get_urls(self):
        path = self.le_image_path.text()
        if not path:
            self.warning("请设置{}".format(self.label_type.text()[:-1]))
        elif not os.path.exists(path):
            self.warning("{}不存在，请重新设置".format(self.label_type.text()[:-1]))
        else:
            self.get_urls_thread.urls = []
            self.get_urls_thread.start()

    def get_idm_path(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe路径', 'C:/thorly/Softwares/IDM', 'IDMan.exe (IDMan.exe)')
        self.le_idm_path.setText(str(file_name[0]))

    def switch_btn_slot(self, radio_btn):
        if radio_btn.text() == 'file mode' and radio_btn.isChecked():
            try:
                self.btn_image_path.clicked.disconnect(self.get_images_name_by_dir)
                self.btn_image_path.clicked.disconnect(self.get_images_name_by_file)
            except:
                pass
            self.btn_image_path.clicked.connect(self.get_images_name_by_file)
            self.label_type.setText('文本文件路径：')
        if radio_btn.text() == 'dir mode' and radio_btn.isChecked():
            try:
                self.btn_image_path.clicked.disconnect(self.get_images_name_by_file)
                self.btn_image_path.clicked.disconnect(self.get_images_name_by_dir)
            except:
                pass
            self.btn_image_path.clicked.connect(self.get_images_name_by_dir)
            self.label_type.setText('压缩文件路径：')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloadOrbit()
    QSSTool.set_qss_to_obj("download_orbits.qss", app)
    win.show()
    sys.exit(app.exec_())
