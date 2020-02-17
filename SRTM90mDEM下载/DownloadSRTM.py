from PyQt5.Qt import *
import sys
import os
import time
import datetime
import resource
from subprocess import call
from srtm import srtm_dem_no


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
            self.sin_no_url.emit('未找到下载链接，请先获取下载链接')
        self.sin_error_num.emit(self.error_num)


class MyTextEdit(QTextEdit):
    """reload mousePressEvent class"""
    def mousePressEvent(self, me):
        # 继承父类方法
        super().mousePressEvent(me)
        url = self.anchorAt(me.pos())
        if url.endswith('.zip'):
            QDesktopServices.openUrl(QUrl(url))


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('下载SRTM 90m DEM')
        self.setWindowIcon(QIcon(':/download.ico'))
        # self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setFont(QFont('Consolas'))
        self.resize(700, 320)
        self.exec_thread = ExecIDMThread()
        self.idm_thread = IDMThread()
        self.setup_ui()

    def setup_ui(self):
        # 添加控件
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
        self.spin_lon_e.setValue(-100)

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

        self.btn_add_idm = QPushButton('启动IDM\n并添加任务', self)
        self.btn_add_idm.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_add_idm.setEnabled(False)

        self.lb_dir = QLabel('DEM保存路径：', self)
        self.le_dir = QLineEdit(self)
        self.btn_dir = QPushButton('选择保存路径', self)

        self.lb_idm = QLabel('IDMan.exe路径：', self)
        self.le_idm = QLineEdit(self)
        self.btn_idm = QPushButton('选择IDM路径', self)

        self.ted_info = MyTextEdit(self)
        self.ted_info.setReadOnly(True)
        self.ted_info.setText(
            "@author  : leiyuan \n@version : 1.4\n"
            "@date    : 2020-02-16\n\n"
            "该工具包含两种下载模式:\n"
            "1. 利用电脑默认浏览器下载（设置好经纬度范围，点击“获取下载链接”即可）\n"
            "2. 利用IDM进行下载（获取下载链接后，设置保存路径和IDMan.exe路径，点击“添加到IDM”即可）")

        # 布局设置
        layout = QGridLayout()
        self.setLayout(layout)
        # 第一行
        layout.addWidget(self.lb_lon_min, 0, 0, Qt.AlignRight)
        layout.addWidget(self.spin_lon_w, 0, 1)
        layout.addWidget(self.lb_lon_max, 0, 2, Qt.AlignRight)
        layout.addWidget(self.spin_lon_e, 0, 3)
        layout.addWidget(self.btn_url, 0, 4, 2, 1)
        # 第二行
        layout.addWidget(self.lb_lat_min, 1, 0, Qt.AlignRight)
        layout.addWidget(self.spin_lat_s, 1, 1)
        layout.addWidget(self.lb_lat_max, 1, 2, Qt.AlignRight)
        layout.addWidget(self.spin_lat_n, 1, 3)
        # 第三行
        layout.addWidget(self.lb_dir, 2, 0, Qt.AlignRight)
        layout.addWidget(self.le_dir, 2, 1, 1, 2)
        layout.addWidget(self.btn_dir, 2, 3)
        layout.addWidget(self.btn_add_idm, 2, 4, 2, 1)
        # 第四行
        layout.addWidget(self.lb_idm, 3, 0, Qt.AlignRight)
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
        self.idm_thread.sin_no_url.connect(self.warning_slot)
        self.idm_thread.sin_error_num.connect(self.error_num_slot)

    def warning_slot(self, info):
        """没有获取链接而点击添加到IDM时，弹出警告信息"""
        mb = QMessageBox(QMessageBox.Warning, "Warning", info, QMessageBox.Ok, self)
        mb.show()

    def error_num_slot(self, error_num):
        """是否全部添加到IDM"""
        if error_num == 0 and self.idm_thread.url:
            # 添加一个开始锚点
            self.ted_info.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 所有任务都被添加到IDM')
        else:
            self.ted_info.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '有 ' + str(
                len(self.idm_thread.url) - error_num) + ' 个任务未被添加到IDM')

    def gen_url_slot(self):
        """获取DEM下载链接"""
        lon_min = -180
        lat_max = 60
        interval = 5
        srtm_url = []
        url_header = "http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/tiff/srtm_"
        # 计算dem编号
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
        no_srtm = []
        for i in range(int(lon0), int(lon1)):
            for j in range(int(lat0), int(lat1)):
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
                lon_lat = "(" + lon_e + "° ~ " + lon_w + "° " + lat_s + "° ~ " + lat_n + "°)"
                num_lon = str(i)
                num_lat = str(j)
                if len(num_lon) == 1:
                    num_lon = "0" + num_lon
                if len(num_lat) == 1:
                    num_lat = "0" + num_lat
                name = "srtm" + "_" + num_lon + "_" + num_lat + ".zip"
                if name not in srtm_dem_no:
                    url = url_header + num_lon + "_" + num_lat + ".zip"
                    srtm_url.append(url)
                    html.append(lon_lat + " " + "<a href=" + url + ">" + name + "</a>")
                else:
                    no_srtm.append(lon_lat + " 此范围内无DEM")
        # 每次点击获取链接按钮后，清空内容
        self.ted_info.clear()
        # 添加一个开始锚点
        self.ted_info.append("<a name='begin'></a>")
        self.ted_info.insertPlainText(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n获取到 " + str(
                len(srtm_url)) + " 个DEM下载链接（点击文件名即可使用默认浏览器下载DEM）")
        self.ted_info.append("\n")
        # 插入可用的dem链接
        for i in range(len(html)):
            self.ted_info.insertHtml(str(i + 1) + "：" + html[i])
            self.ted_info.append('\n')
        # 插入不可用的dem信息
        self.ted_info.setFontUnderline(False)
        self.ted_info.setTextColor(QColor('black'))
        for j in range(len(no_srtm)):
            self.ted_info.insertPlainText(str(len(html) + j + 1) + "：" + no_srtm[j] + "\n\n")
        # 滚动到锚点
        self.ted_info.scrollToAnchor('begin')
        self.idm_thread.url = srtm_url
        self.exec_thread.url = srtm_url

    def open_dir_slot(self):
        """打开对话框，选择DEM保存路径"""
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择保存路径', './')
        self.le_dir.setText(dir_name)
        self.idm_thread.save_path = dir_name

    def choose_idm_slot(self):
        """打开对话框，选择IDMan.exe路径"""
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe', 'C:/thorly/Softwares/IDM', 'IDMan.exe(IDMan.exe)')
        self.le_idm.setText(file_name[0])
        self.idm_thread.idm_path = file_name[0]
        self.exec_thread.idm_path = file_name[0]

    def add_to_idm_slot(self):
        """打开IDM并添加任务到IDM"""
        self.exec_thread.start()
        self.idm_thread.start()
        if self.idm_thread.url:
            self.ted_info.clear()
            self.ted_info.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 开始添加任务到IDM\n')

    def set_btn_add_state_slot(self, le1, le2):
        """设置添加到IDM按钮是否可用"""
        if le1.text() and le2.text():
            self.btn_add_idm.setEnabled(True)
        else:
            self.btn_add_idm.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
