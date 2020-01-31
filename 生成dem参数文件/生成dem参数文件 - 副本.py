# -*- coding: utf-8 -*-
import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, \
    QGridLayout, QWidget, QApplication, QSizePolicy, QFileDialog, QRadioButton, QButtonGroup
from PyQt5.QtGui import QIcon, QFont, QIntValidator
from PyQt5.QtCore import QThread, pyqtSignal
import datetime
import shutil
import re
from parm import envi_hdr, envi_sml, gamma_par


class GenerateParm:
    @staticmethod
    def replace_str(ori_str, old, new, save_path):
        res = ori_str
        for i, j in zip(old, new):
            res = res.replace(str(i), str(j))
        with open(save_path, 'w+') as f:
            f.write(res)

    @staticmethod
    def gen_envi_hdr(hdr, old, new, save_path):
        GenerateParm.replace_str(hdr, old, new, save_path)

    @staticmethod
    def gen_envi_sml(sml, old, new, save_path):
        GenerateParm.replace_str(sml, old, new, save_path)

    @staticmethod
    def gen_gamma_par(par, old, new, save_path):
        GenerateParm.replace_str(par, old, new, save_path)

    @staticmethod
    def gen_doris():
        pass


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('生成 dem 参数文件')
        self.setFont(QFont('Consolas'))
        self.setWindowIcon(QIcon('python.png'))
        self.resize(700, 300)
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        self.label1 = QLabel('软件类型：', self)
        self.radio1 = QRadioButton('ENVI', self)
        self.radio1.setChecked(True)
        self.radio2 = QRadioButton('GAMMA', self)
        self.radio3 = QRadioButton('Doris', self)
        self.btn_group_class = QButtonGroup(self)
        self.btn_group_class.addButton(self.radio1)
        self.btn_group_class.addButton(self.radio2)
        self.btn_group_class.addButton(self.radio3)

        self.label2 = QLabel('dem 主文件：', self)
        self.le_dem_path = QLineEdit(self)
        self.btn_choose = QPushButton('打开', self)
        self.btn_start = QPushButton('生成', self)

        self.label7 = QLabel('dem 分辨率：', self)
        self.radio4 = QRadioButton('30 m', self)
        self.radio4.setChecked(True)
        self.radio5 = QRadioButton('90 m', self)
        self.btn_group_res = QButtonGroup(self)
        self.btn_group_res.addButton(self.radio4)
        self.btn_group_res.addButton(self.radio5)

        self.label3 = QLabel('左上角经、纬度：', self)
        self.le_lon = QLineEdit(self)
        self.le_lat = QLineEdit(self)

        self.label5 = QLabel('dem 列、行数：', self)
        self.le_sample = QLineEdit(self)
        self.le_line = QLineEdit(self)

        self.ted_info = QTextEdit(self)

        self.le_sample.setPlaceholderText(' 列 (sample)')
        self.le_line.setPlaceholderText(' 行 (line)')
        self.le_lon.setPlaceholderText(' 经度 (lon)')
        self.le_lat.setPlaceholderText(' 纬度 (lat)')
        self.le_dem_path.setPlaceholderText(' dem 主文件路径')
        self.ted_info.setReadOnly(True)
        self.le_dem_path.setReadOnly(True)
        self.btn_start.setEnabled(False)
        self.btn_choose.setFixedSize(self.btn_choose.sizeHint())
        # self.btn_start.setFixedSize(self.btn_start.sizeHint())
        self.btn_start.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.ted_info.setText("@author  : leiyuan \n@version : 2.1\n"
                              "@date    : 2020-01-29\n"
                              "-----------------------------------------"
                              "\nSRTM 90m dem (5° x 5°) 大小为 6000 x 6000"
                              "\nALOS 30m dem (1° x 1°) 大小为 3600 x 3600")

        # 设置验证器
        self.le_lat.setValidator(QIntValidator())
        self.le_lon.setValidator(QIntValidator())
        self.le_sample.setValidator(QIntValidator())
        self.le_line.setValidator(QIntValidator())

        # 信号与槽函数连接
        self.btn_choose.clicked.connect(self.get_path_slot)
        self.le_dem_path.textChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.le_lat, self.le_lon, self.le_sample, self.le_line))
        self.le_lat.textChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.le_lat, self.le_lon, self.le_sample, self.le_line))
        self.le_lon.textChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.le_lat, self.le_lon, self.le_sample, self.le_line))
        self.le_sample.textChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.le_lat, self.le_lon, self.le_sample, self.le_line))
        self.le_line.textChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.le_lat, self.le_lon, self.le_sample, self.le_line))

        self.btn_start.clicked.connect(self.gen_parm_slot)

        # 设置布局
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setSpacing(5)
        # layout.setColumnMinimumWidth(3, 100)
        layout.addWidget(self.label1, 0, 1)
        layout.addWidget(self.radio1, 0, 2)
        layout.addWidget(self.radio2, 0, 3)
        layout.addWidget(self.radio3, 0, 4)

        layout.addWidget(self.label2, 2, 1)
        layout.addWidget(self.le_dem_path, 2, 2, 1, 2)
        layout.addWidget(self.btn_choose, 2, 4)

        layout.addWidget(self.label7, 1, 1)
        layout.addWidget(self.radio4, 1, 2)
        layout.addWidget(self.radio5, 1, 3)

        layout.addWidget(self.label3, 3, 1)
        layout.addWidget(self.le_lon, 3, 2)
        layout.addWidget(self.le_lat, 3, 3)
        layout.addWidget(self.btn_start, 3, 4, 2, 1)

        layout.addWidget(self.label5, 4, 1)
        layout.addWidget(self.le_sample, 4, 2)
        layout.addWidget(self.le_line, 4, 3)

        layout.addWidget(self.ted_info, 5, 1, 1, 5)

    def get_path_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择dem文件', './', 'All files(*.*)'
        )
        self.le_dem_path.setText(file_name[0])

    def set_start_state_slot(self, le1, le2, le3, le4, le5):
        if le1.text() and le2.text() and le3.text() and le4.text() and le5.text():
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

    def gen_dem_info(self, interval):
        sample = int(self.le_sample.text())
        line = int(self.le_line.text())
        lon_west = int(self.le_lon.text())
        lat_north = int(self.le_lat.text())
        lon_east = lon_west + sample * interval
        lat_south = lat_north - line * interval
        return [str(lon_west), str(lon_east), str(lat_north), str(lat_south), str(interval), str(sample), str(line)]

    def check_and_gen(self, path, interval):

        old = ['re_lon_west', 're_lon_east', 're_lat_north', 're_lat_south', 're_interval', 're_sample',
               're_line']
        new = self.gen_dem_info(interval)
        if 'hdr' in path:
            GenerateParm.gen_envi_hdr(envi_hdr, old, new, path)
        elif 'sml' in path:
            GenerateParm.gen_envi_sml(envi_sml, old, new, path)
        elif 'par' in path:
            GenerateParm.gen_gamma_par(gamma_par, old, new, path)

    def set_dem_info(self, interval):
        dem_info = self.gen_dem_info(interval)
        self.ted_info.append('-' * 41)
        self.ted_info.append(
            '经度：' + dem_info[0] + ' - ' + dem_info[1][:-2] + '    纬度：' + dem_info[3][:-2] + ' - ' + dem_info[2])
        self.ted_info.append('列数：' + dem_info[5] + '    行数：' + dem_info[6])

    def gen_parm_slot(self):
        # 30m
        if self.radio4.isChecked():
            interval = 1 / 3600
            # ENVI
            if self.radio1.isChecked():
                hdr_path = self.le_dem_path.text() + '.hdr'
                sml_path = self.le_dem_path.text() + '.sml'
                self.check_and_gen(hdr_path, interval)
                self.check_and_gen(sml_path, interval)
                self.set_dem_info(interval)
                self.ted_info.append('-' * 41 + '\n已经生成了所需要的 dem 参数文件')
                self.ted_info.append(hdr_path + '\n' + sml_path)
            # GAMMA
            if self.radio2.isChecked():
                par_path = self.le_dem_path.text() + '.par'
                self.check_and_gen(par_path, interval)
                self.set_dem_info(interval)
                self.ted_info.append('-' * 41 + '\n已经生成了所需要的 dem 参数文件')
                self.ted_info.append(par_path)
            # Doris
            if self.radio3.isChecked():
                self.ted_info.append('-' * 41 + '\n暂不支持Doris，参数文件里面的 dem 路径不好修改')
        # 90m
        if self.radio5.isChecked():
            interval = 5 / 6000
            # ENVI
            if self.radio1.isChecked():
                hdr_path = self.le_dem_path.text() + '.hdr'
                sml_path = self.le_dem_path.text() + '.sml'
                self.check_and_gen(hdr_path, interval)
                self.check_and_gen(sml_path, interval)
                self.set_dem_info(interval)
                self.ted_info.append('-' * 41 + '\n已经生成了所需要的 dem 参数文件')
                self.ted_info.append(hdr_path + '\n' + sml_path)
            # GAMMA
            if self.radio2.isChecked():
                par_path = self.le_dem_path.text() + '.par'
                self.check_and_gen(par_path, interval)
                self.set_dem_info(interval)
                self.ted_info.append('-' * 41 + '\n已经生成了所需要的 dem 参数文件')
                self.ted_info.append(par_path)
            # Doris
            if self.radio3.isChecked():
                self.ted_info.append('-' * 41 + '\n暂不支持Doris，参数文件里面的 dem 主文件路径不好修改')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
