from PyQt5.Qt import *
import os
import sys
import time
import math
import datetime
from subprocess import call
from srtm import srtm_dem_no
import resource


class QSSTool:
    @staticmethod
    def set_qss_to_obj(qss_path, obj):
        with open(qss_path, 'r') as f:
            obj.setStyleSheet(f.read())


class ExecIDMThread(QThread):
    """execute IDM class"""

    def __init__(self):
        super(ExecIDMThread, self).__init__()
        self.idm_path = ''
        self.url = []

    def run(self):
        if self.url:
            os.system(self.idm_path)


class IDMThread(QThread):
    """add tasks to IDM class"""
    sin_no_url = pyqtSignal(str)
    sin_error_num = pyqtSignal(int)

    def __init__(self):
        super(IDMThread, self).__init__()
        self.idm_path = ''
        self.save_path = ''
        self.error_num = 0
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
                    self.error_num += 1
        else:
            self.sin_no_url.emit('未找到任何下载链接，请先获取下载链接')
        self.sin_error_num.emit(self.error_num)


class TextEdit(QTextEdit):
    """reload mousePressEvent class"""

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

    def mousePressEvent(self, me):
        # 继承父类方法
        super().mousePressEvent(me)
        url = self.anchorAt(me.pos())
        if url.endswith('.zip') or url.endswith('.gz'):
            QDesktopServices.openUrl(QUrl(url))


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Download DEM')
        self.setWindowIcon(QIcon(':/download.png'))
        self.setFont(QFont('Consolas'))
        self.resize(800, 400)
        self.exec_thread = ExecIDMThread()
        self.idm_thread = IDMThread()
        self.setup_ui()

    def setup_ui(self):
        # 添加控件
        self.lb_dem = QLabel('DEM类型：')
        self.radio_srtm = QRadioButton('SRTM 90m DEM (3s)')
        self.radio_srtm.setChecked(True)
        self.radio_alos = QRadioButton('ALOS 30m DEM (1s)')
        self.lb_lon = QLabel('最小、最大经度：')
        self.spin_lon_w = QSpinBox()
        self.spin_lon_w.setRange(-180, 180)
        self.spin_lon_w.setToolTip('最小经度')
        self.spin_lon_w.setSuffix("°")
        self.spin_lon_w.setAccelerated(True)
        self.spin_lon_e = QSpinBox()
        self.spin_lon_e.setRange(-180, 180)
        self.spin_lon_e.setToolTip('最大经度')
        self.spin_lon_e.setSuffix("°")
        self.spin_lon_e.setAccelerated(True)

        self.lb_lat = QLabel('最小、最大纬度：')
        self.spin_lat_s = QSpinBox()
        self.spin_lat_s.setRange(-90, 90)
        self.spin_lat_s.setToolTip('最小纬度')
        self.spin_lat_s.setSuffix("°")
        self.spin_lat_s.setAccelerated(True)
        self.spin_lat_n = QSpinBox()
        self.spin_lat_n.setRange(-90, 90)
        self.spin_lat_n.setToolTip('最大纬度')
        self.spin_lat_n.setSuffix("°")
        self.spin_lat_n.setAccelerated(True)

        self.btn_url = QPushButton('获取DEM下载链接')
        font = QFont()
        font.setPixelSize(20)
        self.btn_url.setFont(font)
        self.btn_url.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.btn_add_idm = QPushButton('启动IDM\n 并添加任务 ')
        self.btn_add_idm.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.lb_dir = QLabel('DEM保存路径：')
        self.le_dir = QLineEdit()
        self.btn_dir = QPushButton('选择路径')
        self.btn_dir.setFixedSize(self.btn_dir.sizeHint())

        self.lb_idm = QLabel('IDMan.exe路径：')
        self.le_idm = QLineEdit()
        self.btn_idm = QPushButton('选择路径')
        self.btn_idm.setFixedSize(self.btn_idm.sizeHint())

        self.btn_url.setObjectName("btn")
        self.btn_dir.setObjectName("btn")
        self.btn_idm.setObjectName("btn")
        self.btn_add_idm.setObjectName("btn")

        self.ted_info = TextEdit()
        self.ted_info.setReadOnly(True)
        self.ted_info.setText(
            "@author  : leiyuan \n@version : 2.5\n"
            "@date    : 2020-02-23\n\n"
            "该工具包含两种下载模式:\n\n"
            "1. 利用电脑默认浏览器下载（设置好经纬度范围，点击<获取下载链接>即可）\n\n"
            "2. 利用IDM进行下载（获取下载链接后，设置DEM保存路径和IDMan.exe路径，点击<添加到IDM>即可）")

        # 布局设置
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        # 第一行
        layout.addWidget(self.lb_dem, 0, 0, Qt.AlignRight)
        layout.addWidget(self.radio_srtm, 0, 1)
        layout.addWidget(self.radio_alos, 0, 2)
        # 第二行
        layout.addWidget(self.lb_lon, 1, 0, Qt.AlignRight)
        layout.addWidget(self.spin_lon_w, 1, 1)
        layout.addWidget(self.spin_lon_e, 1, 2)
        layout.addWidget(self.btn_url, 1, 3, 2, 2)
        # 第三行
        layout.addWidget(self.lb_lat, 2, 0, Qt.AlignRight)
        layout.addWidget(self.spin_lat_s, 2, 1)
        layout.addWidget(self.spin_lat_n, 2, 2)
        # 第四行
        layout.addWidget(self.lb_dir, 3, 0, Qt.AlignRight)
        layout.addWidget(self.le_dir, 3, 1, 1, 2)
        layout.addWidget(self.btn_dir, 3, 3)
        layout.addWidget(self.btn_add_idm, 3, 4, 2, 1)
        # 第五行
        layout.addWidget(self.lb_idm, 4, 0, Qt.AlignRight)
        layout.addWidget(self.le_idm, 4, 1, 1, 2)
        layout.addWidget(self.btn_idm, 4, 3)
        # 第六行
        layout.addWidget(self.ted_info, 5, 0, 3, 5)

        # 信号与槽
        self.btn_url.clicked.connect(self.gen_url_slot)
        self.btn_dir.clicked.connect(self.open_dir_slot)
        self.btn_idm.clicked.connect(self.choose_idm_slot)
        self.btn_add_idm.clicked.connect(self.add_to_idm_slot)
        self.idm_thread.sin_no_url.connect(self.warning_slot)
        self.idm_thread.sin_error_num.connect(self.error_num_slot)

    def warning_slot(self, info):
        """弹出警告信息"""
        mb = QMessageBox(QMessageBox.Warning, "Warning", info, QMessageBox.Ok, self)
        mb.show()

    def error_num_slot(self, error_num):
        """是否全部添加到IDM"""
        if len(self.idm_thread.url):
            if error_num == 0:
                time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.ted_info.append('{} 所有任务都被添加到IDM'.format(time_now))
            else:
                time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.ted_info.append('{} 有 {} 个任务未被添加到IDM'.format(time_now, len(self.idm_thread.url) - error_num))

    def gen_url_slot(self):
        """获取DEM下载链接"""
        download_url = []
        html = []
        no_srtm = []  # for srtm
        srtm_url_header = "http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/tiff/srtm_"
        alos_url_header = "https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v1903/"
        lon_w = self.spin_lon_w.value()
        lon_e = self.spin_lon_e.value()
        lat_s = self.spin_lat_s.value()
        lat_n = self.spin_lat_n.value()
        if lon_w >= lon_e or lat_s >= lat_n:
            self.warning_slot('经纬度范围错误，请重新设置')
        # 获取SRTM DEM下载链接
        if self.radio_srtm.isChecked():
            if (lat_s < -60 or lat_n > 60) and lon_w < lon_e and lat_s < lat_n:
                self.warning_slot('SRTM DEM 纬度范围在-60° ~ 60°之间，请重新选择纬度范围，或者选择ALOS DEM')
            else:
                # 计算编号起始点经纬度
                lon_min = -180
                lat_max = 60
                # 计算dem编号
                num_min_lon = (self.spin_lon_w.value() - lon_min) / 5 + 1
                num_max_lon = (self.spin_lon_e.value() - lon_min) / 5 + 1
                num_min_lat = (lat_max - self.spin_lat_n.value()) / 5 + 1
                num_max_lat = (lat_max - self.spin_lat_s.value()) / 5 + 1
                if num_min_lon > int(num_min_lon):
                    num_min_lon = int(num_min_lon)
                if num_max_lon > int(num_max_lon):
                    num_max_lon = int(num_max_lon + 1)
                if num_min_lat > int(num_min_lat):
                    num_min_lat = int(num_min_lat)
                if num_max_lat > int(num_max_lat):
                    num_max_lat = int(num_max_lat + 1)
                # 遍历生成下载链接
                for i in range(int(num_min_lon), int(num_max_lon)):
                    for j in range(int(num_min_lat), int(num_max_lat)):
                        # 计算dem的经纬度范围
                        lon_w = i * 5 - 180
                        lon_e = lon_w - 5
                        lat_s = 60 - j * 5
                        lat_n = lat_s + 5
                        # 设置格式，补零
                        lon_w = "0" + str(lon_w) if len(str(lon_w)) == 1 else str(lon_w)
                        lon_e = "0" + str(lon_e) if len(str(lon_e)) == 1 else str(lon_e)
                        lat_s = "0" + str(lat_s) if len(str(lat_s)) == 1 else str(lat_s)
                        lat_n = "0" + str(lat_n) if len(str(lat_n)) == 1 else str(lat_n)
                        lon_lat = "({}° ~ {}° , {}° ~ {}°)".format(lon_e, lon_w, lat_s, lat_n)
                        num_lon = str(i)
                        num_lat = str(j)
                        if len(num_lon) == 1:
                            num_lon = "0" + num_lon
                        if len(num_lat) == 1:
                            num_lat = "0" + num_lat
                        name = "srtm_{}_{}.zip".format(num_lon, num_lat)
                        if name not in srtm_dem_no:
                            url = "{}{}_{}.zip".format(srtm_url_header, num_lon, num_lat)
                            download_url.append(url)
                            html.append("{} <a href={}>{}</a>".format(lon_lat, url, name))
                        else:
                            no_srtm.append("{} 此范围内无SRTM DEM".format(lon_lat))
        # 获取ALOS DEM下载链接
        else:
            # 计算经纬度，必须为5的倍数
            lon_min = (self.spin_lon_w.value()) // 5 * 5
            lon_max = math.ceil((self.spin_lon_e.value()) / 5) * 5
            lat_min = (self.spin_lat_s.value()) // 5 * 5
            lat_max = math.ceil((self.spin_lat_n.value()) / 5) * 5

            # 格式化函数，补零操作
            def format_num(num, flag):
                if num < 0:
                    zero_num = flag - len(str(num)[1:])
                    if zero_num > 0:
                        return "0" * zero_num + str(num)[1:]
                    else:
                        return str(num)[1:]
                else:
                    zero_num = flag - len(str(num))
                    if zero_num > 0:
                        return "0" * zero_num + str(num)
                    else:
                        return str(num)

            # 遍历获取下载链接
            for i in range(lat_min, lat_max, 5):
                for j in range(lon_min, lon_max, 5):
                    i_5, j_5 = i + 5, j + 5
                    i_0 = "S{}".format(format_num(i, 3)) if i < 0 else "N{}".format(format_num(i, 3))
                    j_0 = "W{}".format(format_num(j, 3)) if j < 0 else "E{}".format(format_num(j, 3))
                    i_5 = "S{}".format(format_num(i_5, 3)) if i_5 < 0 else "N{}".format(format_num(i_5, 3))
                    j_5 = "W{}".format(format_num(j_5, 3)) if j_5 < 0 else "E{}".format(format_num(j_5, 3))
                    lon_lat = "({}° ~ {}° , {}° ~ {}°)".format(j_0[1:], j_5[1:], i_0[1:], i_5[1:])
                    name = "{}{}_{}{}.tar.gz".format(i_0, j_0, i_5, j_5)
                    url = alos_url_header + name
                    download_url.append(url)
                    html.append("{} <a href={}>{}</a>".format(lon_lat, url, name))
        # 获取到下载链接时，才显示相关信息
        if len(download_url) or len(no_srtm):
            # 每次点击获取链接按钮后，清空内容
            self.ted_info.clear()
            # 设置不含超链接字体的下划线和颜色
            self.ted_info.setFontUnderline(False)
            self.ted_info.setTextColor(QColor('black'))
            # 添加一个开始锚点
            self.ted_info.append("<a name='begin'></a>")
            # 插入获取到的DEM链接总数
            self.ted_info.insertPlainText(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n获取到 " + str(
                    len(download_url)) + " 个DEM下载链接（点击文件名即可使用默认浏览器下载DEM）")
            self.ted_info.append("\n")
            # 插入获取到的DEM链接
            for i in range(len(html)):
                self.ted_info.insertHtml(str(i + 1) + "：" + html[i])
                self.ted_info.append('\n')
            # 设置不含超链接字体的下划线和颜色
            self.ted_info.setFontUnderline(False)
            self.ted_info.setTextColor(QColor('black'))
            # 插入不可用的DEM信息(适用于SRTM)
            for j in range(len(no_srtm)):
                self.ted_info.insertPlainText(str(len(html) + j + 1) + "：" + no_srtm[j] + "\n\n")
            # 滚动到开始锚点
            self.ted_info.scrollToAnchor('begin')
            self.idm_thread.url = download_url
            self.exec_thread.url = download_url

    def open_dir_slot(self):
        """打开对话框，选择DEM保存路径"""
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择保存路径', './')
        if dir_name:
            self.le_dir.setText(dir_name)
        self.idm_thread.save_path = self.le_dir.text()

    def choose_idm_slot(self):
        """打开对话框，选择IDMan.exe路径"""
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe', 'C:/thorly/Softwares/IDM', 'IDMan.exe(IDMan.exe)')
        if file_name[0]:
            self.le_idm.setText(file_name[0])
        self.idm_thread.idm_path = self.le_idm.text()
        self.exec_thread.idm_path = self.le_idm.text()

    def add_to_idm_slot(self):
        """打开IDM并添加任务到IDM"""
        # 未设置路径或路径设置有误时，发出警告
        save_path = self.le_dir.text()
        idm_path = self.le_idm.text()
        if not save_path and not idm_path:
            self.warning_slot("请设置DEM保存路径和IDMan.exe路径")
        elif not save_path and idm_path:
            self.warning_slot("请设置DEM保存路径")
        elif not idm_path and save_path:
            self.warning_slot("请设置IDMan.exe路径")
        elif not os.path.exists(save_path) and not os.path.exists(idm_path):
            self.warning_slot("DEM保存路径和IDMan.exe路径不存在，请重新设置")
        elif not os.path.exists(save_path):
            self.warning_slot("DEM保存路径不存在，请重新设置")
        elif not os.path.exists(idm_path):
            self.warning_slot("IDMan.exe路径不存在，请重新设置")
        else:
            self.exec_thread.start()
            self.idm_thread.start()
            if self.idm_thread.url:
                self.ted_info.clear()
                self.ted_info.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 开始添加任务到IDM\n')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    # 设置样式
    QSSTool.set_qss_to_obj('download_dem.qss', app)
    window.show()
    sys.exit(app.exec_())
