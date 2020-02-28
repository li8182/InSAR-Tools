from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QColor
import os
import sys
import time
import math
import datetime
import numpy as np
from osgeo import gdal
from subprocess import call
from dem_mosaic_ui import Ui_Form
from parm import envi_hdr, envi_sml, gamma_par, srtm_dem_no


class ExecIDMThread(QThread):
    """打开IDM下载器"""

    def __init__(self):
        super(ExecIDMThread, self).__init__()
        self.idm_path = ''
        self.url = []

    def run(self):
        if self.url:
            os.system(self.idm_path)


class AddToIDMThread(QThread):
    """添加任务到IDM下载器"""
    sin_no_url = pyqtSignal(str)
    sin_error_num = pyqtSignal(int)

    def __init__(self):
        super(AddToIDMThread, self).__init__()
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


class WriteXYZThread(QThread):
    sin_out_xyz_success = pyqtSignal(str)

    def __init__(self):
        super(WriteXYZThread, self).__init__()
        self.dem_par = []  # 原始dem参数，包含七个参数(lon_w, lon_e, lat_n, lat_s, interval, sample, line)
        self.lon_lat = []  # 获取的doubleSpinBox中的参数（4个）
        self.dem_data = []  # 原始的高程数据
        self.xyz_path = ""  # 保存路径，包含文件名

    def run(self):
        big_lon_w, big_lon_e = int(self.dem_par[0]), int(self.dem_par[1])
        big_lat_n, big_lat_s = int(self.dem_par[2]), int(self.dem_par[3])
        sample, line = int(self.dem_par[5]), int(self.dem_par[6])
        big_lon_interval = big_lon_e - big_lon_w
        big_lat_interval = big_lat_n - big_lat_s
        # 根据经纬度范围计算裁剪的行列号
        small_lon_w, small_lon_e = self.lon_lat[0], self.lon_lat[1]
        small_lat_n, small_lat_s = self.lon_lat[2], self.lon_lat[3]
        small_lon_interval = small_lon_e - small_lon_w
        small_lat_interval = small_lat_n - small_lat_s
        start_sample = int((small_lon_w - big_lon_w) / big_lon_interval * sample)
        sample_num = int(small_lon_interval / big_lon_interval * sample)
        end_sample = start_sample + sample_num
        start_line = int((big_lat_n - small_lat_n) / big_lat_interval * line)
        line_num = int(small_lat_interval / big_lat_interval * line)
        end_line = start_line + line_num
        # 生成经纬度数据
        a = np.linspace(small_lon_w, small_lon_e, sample_num)
        b = np.linspace(small_lat_s, small_lat_n, line_num)
        lon, lat = np.meshgrid(a, b)
        # 裁剪原始高程数据
        height = np.array(self.dem_data)[start_line:end_line, start_sample:end_sample]
        # 写文件
        with open(self.xyz_path, 'w+') as f:
            for i, j, k in zip(lon.flatten(), lat.flatten(), height.flatten()):
                f.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
        # 写文件完成，发射完成信号
        self.sin_out_xyz_success.emit("ok")


class WriteDEMThread(QThread):
    sin_out_success = pyqtSignal(str)

    def __init__(self):
        super(WriteDEMThread, self).__init__()
        self.data = []
        self.path = ""
        self.flag = ""
        self.new = []
        self.old = ['re_lon_west', 're_lon_east', 're_lat_north', 're_lat_south', 're_interval', 're_sample', 're_line']

    @staticmethod
    def replace_str(base_str, old, new, save_path):
        res = base_str
        for i, j in zip(old, new):
            res = res.replace(str(i), str(j))
        with open(save_path, 'w+') as f:
            f.write(res)

    @staticmethod
    def write_dem(h, save_path, dem_format):
        with open(save_path, 'wb+') as f:
            f.write(h.astype(dem_format))

    def run(self):
        if self.flag == "envi":
            self.write_dem(np.array(self.data), self.path, np.short)
            self.replace_str(envi_hdr, self.old, self.new, self.path + ".hdr")
            self.sin_out_success.emit("制作完成")
        elif self.flag == "gamma":
            self.write_dem(np.array(self.data), self.path, np.float32)
            self.replace_str(gamma_par, self.old, self.new, self.path + ".par")
            self.sin_out_success.emit("制作完成")
        else:
            print('不支持doris')


class MosaicThread(QThread):
    sin_out_dem_info = pyqtSignal(str)
    sin_out_success = pyqtSignal(str)

    def __init__(self):
        super(MosaicThread, self).__init__()
        self.abs_path_list = []
        self.dem_data = []
        self.dem_info = ""

    @staticmethod
    def read_tif(tif):
        dem = gdal.Open(tif)
        return dem.ReadAsArray()

    @staticmethod
    def get_lon_lat(abs_path):
        names = []
        lon_str = []
        lat_str = []
        base_path = ''
        for i in abs_path:
            base_path, name = os.path.split(i)
            names.append(name)
            if 'srtm' in name:
                lon_str.append(name[5:7])
                lat_str.append(name[8:10])
            elif 'AVE_DSM' in name:
                lat_str.append(name[0:4])
                lon_str.append(name[4:8])
        lat_str = sorted(list(set(lat_str)))
        lon_str = sorted(list(set(lon_str)))
        names = list(set(names))
        return base_path, names, lon_str, lat_str

    @staticmethod
    def get_num(str_list):
        num_list = []
        for i in str_list:
            if len(i) == 4:
                if i[1] != '0':
                    num_list.append(int(i[1:]))
                elif i[2] != '0':
                    num_list.append(int(i[2:]))
                else:
                    num_list.append(int(i[3:]))
            else:
                if i[0] != '0':
                    num_list.append(int(i))
                else:
                    num_list.append(int(i[1:]))
        return num_list

    def run(self):
        base_path, names, lon_str, lat_str = self.get_lon_lat(self.abs_path_list)
        lat_num = self.get_num(lat_str)
        lon_num = self.get_num(lon_str)
        line = []
        sample = []
        num_equal = (len(names) == len(lat_str) * len(lon_str))
        lon_equal = (list(range(min(lon_num), max(lon_num) + 1)) == lon_num)
        lat_equal = (list(range(min(lat_num), max(lat_num) + 1)) == lat_num)
        if num_equal and lon_equal and lat_equal:
            if "AVE_DSM" in names[0]:
                for lat in lat_str:
                    for lon in lon_str:
                        name = "{}{}_AVE_DSM.tif".format(lat, lon)
                        abs_path = os.path.join(base_path, name)
                        line.append(self.read_tif(abs_path))
                    sample.append(np.concatenate(line, axis=1))
                    line = []
                sample.reverse()
                dem = np.concatenate(sample, axis=0)
                self.dem_data = dem.tolist()
                lon_w = min(lon_num)
                lon_e = max(lon_num) + 1
                lat_s = min(lat_num)
                lat_n = max(lat_num) + 1
                interval = 1 / 3600
                line = 3600 * len(lat_num)
                sample = 3600 * len(lon_num)
                self.dem_info = "{},{},{},{},{},{},{}".format(lon_w, lon_e, lat_n, lat_s, interval, sample, line)
                self.sin_out_success.emit('拼接完成')
            elif "srtm" in names[0]:
                for lat in lat_str:
                    for lon in lon_str:
                        name = "srtm_{}_{}.tif".format(lon, lat)
                        abs_path = os.path.join(base_path, name)
                        line.append(self.read_tif(abs_path))
                    sample.append(np.concatenate(line, axis=1))
                    line = []
                dem = np.concatenate(sample, axis=0)
                self.dem_data = dem.tolist()
                lon_w = min(lon_num) * 5 - 180 - 5
                lon_e = max(lon_num) * 5 - 180
                lat_s = 60 - max(lat_num) * 5
                lat_n = 60 - min(lat_num) * 5 + 5
                interval = 5 / 6000
                line = 6000 * len(lat_num)
                sample = 6000 * len(lon_num)
                self.dem_info = "{},{},{},{},{},{},{}".format(lon_w, lon_e, lat_n, lat_s, interval, sample, line)
                self.sin_out_success.emit('拼接完成')
        else:
            print('error')
        self.sin_out_dem_info.emit(self.dem_info)


class ProcessDEM(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.mosaic_thread = MosaicThread()
        self.write_dem_thread = WriteDEMThread()
        self.write_xyz_thread = WriteXYZThread()
        self.exec_idm_thread = ExecIDMThread()
        self.add_to_idm_thread = AddToIDMThread()
        self.setupUi(self)
        self.connect_slots()

    def connect_slots(self):
        # 拼接
        self.mosaic_thread.sin_out_dem_info.connect(self.assign_dem_info)
        self.mosaic_thread.sin_out_success.connect(self.mosaic_success)
        self.pushButton_open_tif.clicked.connect(self.get_tif_path)
        self.pushButton_clear.clicked.connect(lambda: self.textEdit_tif.clear())
        self.pushButton_mosaic.clicked.connect(self.mosaic_data)
        self.pushButton_plot.clicked.connect(self.plot_mosaic_data)
        # 下载
        self.pushButton_get_url.clicked.connect(self.get_urls)
        self.pushButton_dem_path_d.clicked.connect(self.get_dem_save_path_d)
        self.pushButton_idm_path_d.clicked.connect(self.get_idm_path_d)
        self.pushButton_add_to_idm.clicked.connect(self.add_to_idm)
        self.add_to_idm_thread.sin_no_url.connect(self.popup_warning)
        self.add_to_idm_thread.sin_error_num.connect(self.get_error_num)
        # 制作DEM
        self.pushButton_dem_path.clicked.connect(self.get_dem_path)
        self.pushButton_make_dem.clicked.connect(self.make_dem)
        self.radioButton_envi.toggled.connect(lambda: self.get_flag(self.radioButton_envi))
        self.radioButton_gamma.toggled.connect(lambda: self.get_flag(self.radioButton_gamma))
        self.radioButton_doris.toggled.connect(lambda: self.get_flag(self.radioButton_doris))
        self.write_dem_thread.sin_out_success.connect(self.make_dem_success)
        # 制作xyz
        self.write_xyz_thread.sin_out_xyz_success.connect(self.write_xyz_success)
        self.pushButton_xyz_path.clicked.connect(self.get_xyz_path)
        self.pushButton_to_xyz.clicked.connect(self.write_xyz)

    def get_urls(self):
        """获取DEM下载链接"""
        download_url = []
        html = []
        no_srtm = []  # for srtm
        srtm_url_header = "http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/tiff/srtm_"
        alos_url_header = "https://www.eorc.jaxa.jp/ALOS/aw3d30/data/release_v1903/"
        lon_w = self.spinBox_lon_w.value()
        lon_e = self.spinBox_lon_e.value()
        lat_s = self.spinBox_lat_s.value()
        lat_n = self.spinBox_lat_n.value()
        if lon_w >= lon_e or lat_s >= lat_n:
            self.popup_warning('经纬度范围错误，请重新设置')
        # 获取SRTM DEM下载链接
        if self.radioButton_srtm.isChecked():
            if (lat_s < -60 or lat_n > 60) and lon_w < lon_e and lat_s < lat_n:
                self.popup_warning('SRTM DEM 纬度范围在-60° ~ 60°之间，请重新选择纬度范围，或者选择ALOS DEM')
            else:
                # 计算编号起始点经纬度
                lon_min = -180
                lat_max = 60
                # 计算dem编号
                num_min_lon = (lon_w - lon_min) / 5 + 1
                num_max_lon = (lon_e - lon_min) / 5 + 1
                num_min_lat = (lat_max - lat_n) / 5 + 1
                num_max_lat = (lat_max - lat_s) / 5 + 1
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
        elif self.radioButton_alos.isChecked():
            # 计算经纬度，必须为5的倍数
            lon_min = lon_w // 5 * 5
            lon_max = math.ceil(lon_e / 5) * 5
            lat_min = lat_s // 5 * 5
            lat_max = math.ceil(lat_n / 5) * 5

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
            self.textEdit_info.clear()
            # 设置不含超链接字体的下划线和颜色
            self.textEdit_info.setFontUnderline(False)
            self.textEdit_info.setTextColor(QColor('black'))
            # 添加一个开始锚点
            self.textEdit_info.append("<a name='begin'></a>")
            # 插入获取到的DEM链接总数
            self.textEdit_info.insertPlainText(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n获取到 " + str(
                    len(download_url)) + " 个DEM下载链接（点击文件名即可使用默认浏览器下载DEM）")
            self.textEdit_info.append("\n")
            # 插入获取到的DEM链接
            for i in range(len(html)):
                self.textEdit_info.insertHtml(str(i + 1) + "：" + html[i])
                self.textEdit_info.append('\n')
            # 设置不含超链接字体的下划线和颜色
            self.textEdit_info.setFontUnderline(False)
            self.textEdit_info.setTextColor(QColor('black'))
            # 插入不可用的DEM信息(适用于SRTM)
            for j in range(len(no_srtm)):
                self.textEdit_info.insertPlainText(str(len(html) + j + 1) + "：" + no_srtm[j] + "\n\n")
            # 滚动到开始锚点
            self.textEdit_info.scrollToAnchor('begin')
            self.add_to_idm_thread.url = download_url
            self.exec_idm_thread.url = download_url

    def get_dem_save_path_d(self):
        """打开对话框，选择DEM保存路径"""
        dir_name = QFileDialog.getExistingDirectory(
            self, '选择保存路径', './')
        if dir_name:
            self.lineEdit_dem_path_d.setText(dir_name)
        self.add_to_idm_thread.save_path = self.lineEdit_dem_path_d.text()

    def get_idm_path_d(self):
        """打开对话框，选择IDMan.exe路径"""
        file_name = QFileDialog.getOpenFileName(
            self, '选择IDMan.exe', 'C:/thorly/Softwares/IDM', 'IDMan.exe(IDMan.exe)')
        if file_name[0]:
            self.lineEdit_idm_path.setText(file_name[0])
        self.add_to_idm_thread.idm_path = self.lineEdit_idm_path.text()
        self.exec_idm_thread.idm_path = self.lineEdit_idm_path.text()

    def add_to_idm(self):
        """打开IDM并添加任务到IDM"""
        # 未设置路径或路径设置有误时，发出警告
        save_path = self.lineEdit_dem_path_d.text()
        idm_path = self.lineEdit_idm_path.text()
        if not save_path and not idm_path:
            self.popup_warning("请设置DEM保存路径和IDMan.exe路径")
        elif not save_path and idm_path:
            self.popup_warning("请设置DEM保存路径")
        elif not idm_path and save_path:
            self.popup_warning("请设置IDMan.exe路径")
        elif not os.path.exists(save_path) and not os.path.exists(idm_path):
            self.popup_warning("DEM保存路径和IDMan.exe路径不存在，请重新设置")
        elif not os.path.exists(save_path):
            self.popup_warning("DEM保存路径不存在，请重新设置")
        elif not os.path.exists(idm_path):
            self.popup_warning("IDMan.exe路径不存在，请重新设置")
        else:
            self.exec_idm_thread.start()
            self.add_to_idm_thread.start()
            if self.add_to_idm_thread.url:
                self.textEdit_info.clear()
                self.textEdit_info.setFontUnderline(False)
                self.textEdit_info.setTextColor(QColor('black'))
                self.textEdit_info.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 开始添加任务到IDM\n')

    def get_error_num(self, error_num):
        """是否全部添加到IDM"""
        if len(self.add_to_idm_thread.url):
            if error_num == 0:
                time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.textEdit_info.append('{} 所有任务都被添加到IDM'.format(time_now))
            else:
                time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.textEdit_info.append(
                    '{} 有 {} 个任务未被添加到IDM'.format(time_now, len(self.add_to_idm_thread.url) - error_num))

    def write_xyz(self):
        self.write_xyz_thread.xyz_path = self.lineEdit_xyz_path.text()
        self.write_xyz_thread.dem_data = self.mosaic_thread.dem_data
        self.write_xyz_thread.lon_lat = [self.doubleSpinBox_lon_w.value(), self.doubleSpinBox_lon_e.value(),
                                         self.doubleSpinBox_lat_n.value(), self.doubleSpinBox_lat_s.value()]
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.textEdit_info.append("{} {}".format(time_now, "ok"))
        self.pushButton_to_xyz.setEnabled(False)
        self.write_xyz_thread.start()

    def write_xyz_success(self, info):
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.textEdit_info.append("{} {}".format(time_now, info))
        self.pushButton_to_xyz.setEnabled(True)

    def get_xyz_path(self):
        file_name = QFileDialog.getSaveFileName(
            self, "保存文件", "./", "text file(*.xyz);;text file(*.txt)")
        self.lineEdit_xyz_path.setText(file_name[0])

    def popup_warning(self, info):
        mb = QMessageBox(QMessageBox.Warning, "Warning", info, QMessageBox.Ok, self)
        mb.show()

    def make_dem_success(self, info):
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.textEdit_info.append("{} {}".format(time_now, info))
        self.pushButton_make_dem.setEnabled(True)

    def mosaic_success(self, info):
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.textEdit_info.append("{} {}".format(time_now, info))
        self.pushButton_mosaic.setEnabled(True)

    def get_flag(self, r1):
        if r1.text() == 'envi' and r1.isChecked():
            self.write_dem_thread.flag = 'envi'
        elif r1.text() == 'gamma' and r1.isChecked():
            self.write_dem_thread.flag = 'gamma'
        else:
            self.write_dem_thread.flag = 'doris'

    def make_dem(self):
        self.write_dem_thread.path = self.lineEdit_dem_path.text()
        self.write_dem_thread.data = self.mosaic_thread.dem_data
        data = self.write_dem_thread.data
        new = self.write_dem_thread.new
        path = self.write_dem_thread.path
        flag = self.write_dem_thread.flag
        if data and new and path and flag:
            time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.textEdit_info.append("{} {}".format(time_now, "开始制作DEM"))
            self.pushButton_make_dem.setEnabled(False)
            self.write_dem_thread.start()
        elif not data and not new:
            self.popup_warning("请先读取/拼接tif格式文件")
        else:
            self.popup_warning("请先设置DEM保存路径")

    def assign_dem_info(self, dem_info):
        self.write_dem_thread.new = dem_info.split(',')
        self.doubleSpinBox_lon_w.setValue(int(dem_info.split(',')[0]))
        self.doubleSpinBox_lon_e.setValue(int(dem_info.split(',')[1]))
        self.doubleSpinBox_lat_n.setValue(int(dem_info.split(',')[2]))
        self.doubleSpinBox_lat_s.setValue(int(dem_info.split(',')[3]))
        self.write_xyz_thread.dem_par = dem_info.split(',')

    def get_tif_path(self):
        files = QFileDialog.getOpenFileNames(
            self, '选择tif格式文件', './', 'SRTM DEM(srtm*.tif);;ALOS DEM(*AVE_DSM.tif)')
        for f in files[0]:
            self.textEdit_tif.append(f)

    def mosaic_data(self):
        if self.textEdit_tif.toPlainText():
            time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.textEdit_info.append("{} {}".format(time_now, "开始读取/拼接"))
            self.pushButton_mosaic.setEnabled(False)
            self.mosaic_thread.abs_path_list = self.textEdit_tif.toPlainText().split('\n')
            self.mosaic_thread.start()
        else:
            self.popup_warning("请先选择tif格式文件")

    def plot_mosaic_data(self):
        self.popup_warning("加紧实现中...")

    def get_dem_path(self):
        dem_name = QFileDialog.getSaveFileName(
            self, '保存dem', './')
        self.lineEdit_dem_path.setText(dem_name[0])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProcessDEM()
    window.show()
    sys.exit(app.exec_())
