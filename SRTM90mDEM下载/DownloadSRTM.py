from PyQt5.Qt import *
import sys
import os
import time
import resource
from subprocess import call
from srtm import srtm_dem_no


class ExecIDMThread(QThread):
    def __init__(self):
        super(ExecIDMThread, self).__init__()
        self.idm_path = ''

    def run(self):
        os.system(self.idm_path)


class IDMThread(QThread):
    def __init__(self):
        super(IDMThread, self).__init__()
        self.idm_path = ''
        self.save_path = ''
        self.url = []

    def run(self):
        if self.url:
            time.sleep(1)
            for i in range(len(self.url)):
                try:
                    call([
                        self.idm_path, '/d', self.url[i], '/p', self.save_path, '/f',
                        self.url[i].split('/')[-1], '/n', '/a'
                    ])
                except:
                    print('error')
        else:
            print('没有下载链接，请生成下载链接')


class MyTextEdit(QTextEdit):

    def mousePressEvent(self, me):
        url = self.anchorAt(me.pos())
        if url.endswith('.zip'):
            QDesktopServices.openUrl(QUrl(url))


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('下载SRTM 90m DEM')
        self.setWindowIcon(QIcon(':/dem.ico'))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setFont(QFont('Consolas'))
        self.resize(700, 320)
        self.setup_ui()
        self.exec_thread = ExecIDMThread()
        self.idm_thread = IDMThread()

    def setup_ui(self):
        self.lb_lon_min = QLabel('最小经度：', self)
        self.lb_lon_max = QLabel('最大经度：', self)
        self.spin_lon_w = QSpinBox(self)
        self.spin_lon_w.setMaximum(180)
        self.spin_lon_w.setMinimum(-180)
        self.spin_lon_w.setSuffix("°")
        self.spin_lon_w.setValue(-180)
        self.spin_lon_e = QSpinBox(self)
        self.spin_lon_e.setMaximum(180)
        self.spin_lon_e.setMinimum(-180)
        self.spin_lon_e.setSuffix("°")
        self.spin_lon_e.setValue(-175)

        self.lb_lat_min = QLabel('最小纬度：', self)
        self.lb_lat_max = QLabel('最大纬度：', self)
        self.spin_lat_s = QSpinBox(self)
        self.spin_lat_s.setMaximum(60)
        self.spin_lat_s.setMinimum(-60)
        self.spin_lat_s.setSuffix("°")
        self.spin_lat_s.setValue(50)
        self.spin_lat_n = QSpinBox(self)
        self.spin_lat_n.setMaximum(60)
        self.spin_lat_n.setMinimum(-60)
        self.spin_lat_n.setSuffix("°")
        self.spin_lat_n.setValue(60)

        self.btn_url = QPushButton('获取\n下载链接', self)
        self.btn_url.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.btn_add_idm = QPushButton('添加到IDM', self)
        self.btn_add_idm.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_add_idm.setEnabled(False)

        self.lb_dir = QLabel('DEM保存路径：', self)
        self.le_dir = QLineEdit(self)
        self.btn_dir = QPushButton('打开', self)

        self.lb_idm = QLabel('IDMan.exe路径：', self)
        self.le_idm = QLineEdit(self)
        self.btn_idm = QPushButton('打开', self)

        self.ted_info = MyTextEdit(self)
        self.ted_info.setReadOnly(True)
        self.ted_info.setText(
            "@author  : leiyuan \n@version : 1.1\n"
            "@date    : 2020-02-11\n\n"
            "两种下载模式:\n"
            "1. 利用电脑默认浏览器下载（设置好经纬度范围，点击‘获取下载链接’即可）\n"
            "2. 利用IDM进行下载（获取下载链接后，设置保存路径和IDMan.exe路径，点击‘添加到IDM’即可）")

        # 布局设置
        layout = QGridLayout()
        self.setLayout(layout)
        # 第一行
        layout.addWidget(self.lb_lon_min, 0, 0)
        layout.addWidget(self.spin_lon_w, 0, 1)
        layout.addWidget(self.lb_lon_max, 0, 2)
        layout.addWidget(self.spin_lon_e, 0, 3)
        layout.addWidget(self.btn_url, 0, 4, 2, 1)
        # 第二行
        layout.addWidget(self.lb_lat_min, 1, 0)
        layout.addWidget(self.spin_lat_s, 1, 1)
        layout.addWidget(self.lb_lat_max, 1, 2)
        layout.addWidget(self.spin_lat_n, 1, 3)
        # 第三行
        layout.addWidget(self.lb_dir, 2, 0)
        layout.addWidget(self.le_dir, 2, 1, 1, 2)
        layout.addWidget(self.btn_dir, 2, 3)
        layout.addWidget(self.btn_add_idm, 2, 4, 2, 1)
        # 第四行
        layout.addWidget(self.lb_idm, 3, 0)
        layout.addWidget(self.le_idm, 3, 1, 1, 2)
        layout.addWidget(self.btn_idm, 3, 3)
        # 第五行
        layout.addWidget(self.ted_info, 4, 0, 3, 5)

        # 信号与槽
        self.btn_url.clicked.connect(self.gen_url_slot)
        self.btn_dir.clicked.connect(self.open_dir_slot)
        self.btn_idm.clicked.connect(self.choose_idm_slot)
        self.btn_add_idm.clicked.connect(self.add_to_idm_slot)
        self.le_idm.textChanged.connect(lambda: self.set_btn_add_state_slot(self.le_idm, self.le_dir))
        self.le_dir.textChanged.connect(lambda: self.set_btn_add_state_slot(self.le_idm, self.le_dir))

    def gen_url_slot(self):
        lon_min = -180
        lat_max = 60
        interval = 5
        srtm_url = []
        url_header = "http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/tiff/srtm_"
        lon0 = (self.spin_lon_w.value() - lon_min) / interval + 1
        lon1 = (self.spin_lon_e.value() - lon_min) / interval + 1
        lat0 = (lat_max - self.spin_lat_n.value()) / interval + 1
        lat1 = (lat_max - self.spin_lat_s.value()) / interval + 1
        if lon0 > int(lon0):
            lon0 = int(lon0)
        if lon1 > int(lon1):
            lon1 = int(lon1 + 1)
        if lat0 > int(lat0):
            lat0 = int(lat0)
        if lat1 > int(lat1):
            lat1 = int(lat1 + 1)
        html = []
        no_srtm = ""
        for i in range(int(lon0), int(lon1)):
            for j in range(int(lat0), int(lat1)):
                lon_w = i * 5 - 180
                lon_e = lon_w - 5
                lat_s = 60 - j * 5
                lat_n = lat_s + 5
                lon_w = "0" + str(lon_w) if len(str(lon_w)) == 1 else str(lon_w)
                lon_e = "0" + str(lon_e) if len(str(lon_e)) == 1 else str(lon_e)
                lat_s = "0" + str(lat_s) if len(str(lat_s)) == 1 else str(lat_s)
                lat_n = "0" + str(lat_n) if len(str(lat_n)) == 1 else str(lat_n)
                lon_lat = "(" + lon_e + "~" + lon_w + " " + lat_s + "~" + lat_n + ")"
                num_lon = str(i)
                num_lat = str(j)
                if len(num_lon) == 1:
                    num_lon = "0" + num_lon
                if len(num_lat) == 1:
                    num_lat = "0" + num_lat
                name = "srtm" + "-" + num_lon + "-" + num_lat + ".zip"
                if name not in srtm_dem_no:
                    url = url_header + num_lon + "_" + num_lat + ".zip"
                    srtm_url.append(url)
                    html.append("点击右侧文件名即可下载：" + lon_lat + " " + "<a href=" + url + ">" + name + "</a>")
                else:
                    no_srtm += "此范围内无DEM" + lon_lat + '\n\n'
        self.ted_info.clear()
        self.ted_info.append(no_srtm)
        for h in html:
            self.ted_info.insertHtml(h)
            self.ted_info.append('\n')
        self.idm_thread.url = srtm_url

    def open_dir_slot(self):
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择保存路径', './')
        self.le_dir.setText(dir_name)
        self.idm_thread.save_path = dir_name

    def choose_idm_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe', 'C:/thorly/Softwares/IDM', 'IDMan.exe(IDMan.exe)')
        self.le_idm.setText(file_name[0])
        self.idm_thread.idm_path = file_name[0]
        self.exec_thread.idm_path = file_name[0]
        self.exec_thread.start()

    def add_to_idm_slot(self):
        self.idm_thread.start()

    def set_btn_add_state_slot(self, le1, le2):
        if le1.text() and le2.text():
            self.btn_add_idm.setEnabled(True)
        else:
            self.btn_add_idm.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
