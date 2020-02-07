# -*- coding: utf-8 -*-
import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QLineEdit, \
    QGridLayout, QWidget, QApplication, QSizePolicy, QFileDialog, QRadioButton, QButtonGroup, QSpinBox
from PyQt5.QtGui import QIcon, QFont

from parm import envi_hdr, envi_sml, gamma_par
import resource_rc

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
        self.setWindowIcon(QIcon(':/parameter.ico'))
        self.resize(700, 300)
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        self.label_type = QLabel('软件类型：', self)
        self.radio_envi = QRadioButton('ENVI', self)
        self.radio_envi.setChecked(True)
        self.radio_gamma = QRadioButton('GAMMA', self)
        self.radio_doris = QRadioButton('Doris', self)
        self.btn_group_type = QButtonGroup(self)
        self.btn_group_type.addButton(self.radio_envi)
        self.btn_group_type.addButton(self.radio_gamma)
        self.btn_group_type.addButton(self.radio_doris)

        self.label_dem_path = QLabel('dem 主文件：', self)
        self.le_dem_path = QLineEdit(self)
        self.btn_choose = QPushButton('打开', self)
        self.btn_start = QPushButton('生成', self)

        self.label_dem_res = QLabel('dem 分辨率：', self)
        self.radio_30 = QRadioButton('ALOS 30 m', self)
        self.radio_30.setChecked(True)
        self.radio_90 = QRadioButton('SRTM 90 m', self)
        self.btn_group_res = QButtonGroup(self)
        self.btn_group_res.addButton(self.radio_30)
        self.btn_group_res.addButton(self.radio_90)

        self.label_lon_west = QLabel('左上角经度：', self)
        self.label_lat_north = QLabel('左上角纬度：', self)
        self.sbox_lon_west = QSpinBox(self)
        self.sbox_lat_north = QSpinBox(self)
        self.sbox_lon_west.setMinimum(-180)
        self.sbox_lon_west.setMaximum(180)
        self.sbox_lat_north.setMinimum(-90)
        self.sbox_lat_north.setMaximum(90)

        self.label_sample = QLabel('dem 列数：', self)
        self.label_line = QLabel('dem 行数：', self)
        self.sbox_sample = QSpinBox(self)
        self.sbox_line = QSpinBox(self)
        self.sbox_sample.setMaximum(9999999)
        self.sbox_line.setMaximum(9999999)
        self.sbox_sample.setSingleStep(3600)
        self.sbox_line.setSingleStep(3600)

        self.ted_info = QTextEdit(self)
        self.ted_info.setReadOnly(True)
        self.le_dem_path.setReadOnly(True)
        self.btn_start.setEnabled(False)
        self.btn_choose.setFixedSize(self.btn_choose.sizeHint())
        self.btn_start.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.ted_info.setText("@author  : leiyuan \n@version : 2.1\n"
                              "@date    : 2020-01-29\n"
                              "-----------------------------------------"
                              "\nSRTM 90m dem (5° x 5°) 大小为 6000 x 6000"
                              "\nALOS 30m dem (1° x 1°) 大小为 3600 x 3600")

        # 信号与槽函数连接
        self.radio_30.toggled.connect(lambda: self.set_step_slot(self.radio_30))
        self.radio_90.toggled.connect(lambda: self.set_step_slot(self.radio_90))
        self.btn_choose.clicked.connect(self.get_path_slot)
        self.btn_start.clicked.connect(self.gen_parm_slot)
        self.le_dem_path.textChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.sbox_lat_north, self.sbox_lon_west,
                                              self.sbox_sample, self.sbox_line))
        self.sbox_lat_north.valueChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.sbox_lat_north, self.sbox_lon_west,
                                              self.sbox_sample, self.sbox_line))
        self.sbox_lon_west.valueChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.sbox_lat_north, self.sbox_lon_west,
                                              self.sbox_sample, self.sbox_line))
        self.sbox_sample.valueChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.sbox_lat_north, self.sbox_lon_west,
                                              self.sbox_sample, self.sbox_line))
        self.sbox_line.valueChanged.connect(
            lambda: self.set_start_state_slot(self.le_dem_path, self.sbox_lat_north, self.sbox_lon_west,
                                              self.sbox_sample, self.sbox_line))
        # 设置布局
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setSpacing(5)
        # 第一行
        layout.addWidget(self.label_type, 0, 1)
        layout.addWidget(self.radio_envi, 0, 2)
        layout.addWidget(self.radio_gamma, 0, 3)
        layout.addWidget(self.radio_doris, 0, 4)
        # 第二行
        layout.addWidget(self.label_dem_res, 1, 1)
        layout.addWidget(self.radio_30, 1, 2)
        layout.addWidget(self.radio_90, 1, 3)
        # 第三行
        layout.addWidget(self.label_dem_path, 2, 1)
        layout.addWidget(self.le_dem_path, 2, 2, 1, 3)
        layout.addWidget(self.btn_choose, 2, 5)
        # 第四行
        layout.addWidget(self.label_lon_west, 3, 1)
        layout.addWidget(self.sbox_lon_west, 3, 2)
        layout.addWidget(self.label_lat_north, 3, 3)
        layout.addWidget(self.sbox_lat_north, 3, 4)
        layout.addWidget(self.btn_start, 3, 5, 2, 1)
        # 第五行
        layout.addWidget(self.label_sample, 4, 1)
        layout.addWidget(self.sbox_sample, 4, 2)
        layout.addWidget(self.label_line, 4, 3)
        layout.addWidget(self.sbox_line, 4, 4)
        # 第六行
        layout.addWidget(self.ted_info, 5, 1, 1, 5)

    # 根据 dem 分辨率设置 QSpinBox 的步长
    def set_step_slot(self, radio):
        if radio.text() == 'ALOS 30 m':
            self.sbox_sample.setValue(0)
            self.sbox_line.setValue(0)
            self.sbox_sample.setSingleStep(3600)
            self.sbox_line.setSingleStep(3600)
        else:
            self.sbox_sample.setValue(0)
            self.sbox_line.setValue(0)
            self.sbox_sample.setSingleStep(6000)
            self.sbox_line.setSingleStep(6000)

    # 打开对话框选择 dem 主文件，并设置 QLineEdit 内容
    def get_path_slot(self):
        file_name = QFileDialog.getOpenFileName(
            self, '选择dem文件', './', 'All files(*.*)'
        )
        self.le_dem_path.setText(file_name[0])

    # 设置开始按钮的可用状态
    def set_start_state_slot(self, le1, le2, le3, le4, le5):
        if le1.text() and le2.value() and le3.value() and le4.value() and le5.value():
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

    # 获取 dem 信息
    def gen_dem_info(self, interval):
        sample = self.sbox_sample.value()
        line = self.sbox_line.value()
        lon_west = self.sbox_lon_west.value()
        lat_north = self.sbox_lat_north.value()
        lon_east = int(lon_west + sample * interval)
        lat_south = int(lat_north - line * interval)
        return [str(lon_west), str(lon_east), str(lat_north), str(lat_south), str(interval), str(sample), str(line)]

    def check_and_gen(self, path, interval):
        old = ['re_lon_west', 're_lon_east', 're_lat_north', 're_lat_south', 're_interval', 're_sample', 're_line']
        new = self.gen_dem_info(interval)
        # # SRTM 90m dem 参数文件行列数每 5°要加 1
        # if interval * 6000 == 5:
        #     new[5] = str(int(new[5]) + int(new[5]) // 6000)
        #     new[6] = str(int(new[6]) + int(new[6]) // 6000)
        if 'hdr' in path:
            GenerateParm.gen_envi_hdr(envi_hdr, old, new, path)
        elif 'sml' in path:
            GenerateParm.gen_envi_sml(envi_sml, old, new, path)
        elif 'par' in path:
            GenerateParm.gen_gamma_par(gamma_par, old, new, path)

    # 设置 QTextEdit 的内容（dem 信息）
    def set_dem_info(self, interval):
        dem_info = self.gen_dem_info(interval)
        self.ted_info.append('-' * 41)
        self.ted_info.append(
            '经度：' + dem_info[0] + '° - ' + dem_info[1] + '°    纬度：' + dem_info[3] + '° - ' + dem_info[2] + '°')
        self.ted_info.append('列数：' + dem_info[5] + '    行数：' + dem_info[6])

    def set_parm(self, interval):
        # EVNI
        if self.radio_envi.isChecked():
            hdr_path = self.le_dem_path.text() + '.hdr'
            sml_path = self.le_dem_path.text() + '.sml'
            self.check_and_gen(hdr_path, interval)
            self.check_and_gen(sml_path, interval)
            self.set_dem_info(interval)
            self.ted_info.append('-' * 41 + '\n已经生成了所需要的 dem 参数文件')
            self.ted_info.append(hdr_path + '\n' + sml_path)
        # GAMMA
        if self.radio_gamma.isChecked():
            par_path = self.le_dem_path.text() + '.par'
            self.check_and_gen(par_path, interval)
            self.set_dem_info(interval)
            self.ted_info.append('-' * 41 + '\n已经生成了所需要的 dem 参数文件')
            self.ted_info.append(par_path)
        # Doris
        if self.radio_doris.isChecked():
            self.ted_info.append('-' * 41 + '\n暂不支持Doris，参数文件里面的 dem 主文件路径为 Linux 下路径，Windows 下无法获取')

    # 生成相关的参数文件并设置 QTextEdit 内容
    def gen_parm_slot(self):
        # 30m
        if self.radio_30.isChecked():
            self.set_parm(1 / 3600)
        # 90m
        if self.radio_90.isChecked():
            self.set_parm(5 / 6000)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
