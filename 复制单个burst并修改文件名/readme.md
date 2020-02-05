## 复制单个burst到指定文件夹并重命名

### 1. 若有以下ENVI导出文件文件数（示例）
```text
C:\THORLY\FILE\ENVI_IMPORTED
├─sentinel1_128_20170819_110849564_IW_SIW1_A_VV_slc_list.split_bursts
│      burst_IW2_3_slc
│      burst_IW2_3_slc.dbf
│      burst_IW2_3_slc.enp
│      burst_IW2_3_slc.hdr
│      burst_IW2_3_slc.kml
│      burst_IW2_3_slc.prj
│      burst_IW2_3_slc.shp
│      burst_IW2_3_slc.shp.hdr
│      burst_IW2_3_slc.shx
│      burst_IW2_3_slc.sml
│
├─sentinel1_128_20180801_110849564_IW_SIW1_A_VV_slc_list.split_bursts
│      burst_IW1_4_slc
│      burst_IW1_4_slc.dbf
│      burst_IW1_4_slc.enp
│      burst_IW1_4_slc.hdr
│      burst_IW1_4_slc.kml
│      burst_IW1_4_slc.prj
│      burst_IW1_4_slc.shp
│      burst_IW1_4_slc.shp.hdr
│      burst_IW1_4_slc.shx
│      burst_IW1_4_slc.sml
│
├─sentinel1_128_20180813_110849564_IW_SIW1_A_VV_slc_list.split_bursts
│      burst_IW2_9_slc
│      burst_IW2_9_slc.dbf
│      burst_IW2_9_slc.enp
│      burst_IW2_9_slc.hdr
│      burst_IW2_9_slc.kml
│      burst_IW2_9_slc.prj
│      burst_IW2_9_slc.shp
│      burst_IW2_9_slc.shp.hdr
│      burst_IW2_9_slc.shx
│      burst_IW2_9_slc.sml
│
└─sentinel1_128_20180825_110849564_IW_SIW1_A_VV_slc_list.split_bursts
        burst_IW2_4_slc
        burst_IW2_4_slc.dbf
        burst_IW2_4_slc.enp
        burst_IW2_4_slc.hdr
        burst_IW2_4_slc.kml
        burst_IW2_4_slc.prj
        burst_IW2_4_slc.shp
        burst_IW2_4_slc.shp.hdr
        burst_IW2_4_slc.shx
        burst_IW2_4_slc.sml
```

### 2. 若要复制并重命名以上文件，如何撰写burst信息文件
1. 格式要求：纯文本文件，包含两列数据，第一列为date，第二列为burst
2. 该纯文本文件的内容应为：
  ```text
    20180801 14
    20180813 29
    20180825 24
    20170819 23
   ```

### 3. 如何设置ENVI导出文件路径
`C:\THORLY\FILE\ENVI_IMPORTED`即为所要求的路径

### 4. 如何设置保存文件路径
自由选择，此处选为`C:\THORLY\FILE\SLC`，复制并重命名后的文件树为：
```text
C:\THORLY\FILE\SLC
    20170819_slc
    20170819_slc.dbf
    20170819_slc.hdr
    20170819_slc.kml
    20170819_slc.prj
    20170819_slc.shp
    20170819_slc.shp.hdr
    20170819_slc.shx
    20170819_slc.sml
    20180801_slc
    20180801_slc.dbf
    20180801_slc.hdr
    20180801_slc.kml
    20180801_slc.prj
    20180801_slc.shp
    20180801_slc.shp.hdr
    20180801_slc.shx
    20180801_slc.sml
    20180813_slc
    20180813_slc.dbf
    20180813_slc.hdr
    20180813_slc.kml
    20180813_slc.prj
    20180813_slc.shp
    20180813_slc.shp.hdr
    20180813_slc.shx
    20180813_slc.sml
    20180825_slc
    20180825_slc.dbf
    20180825_slc.hdr
    20180825_slc.kml
    20180825_slc.prj
    20180825_slc.shp
    20180825_slc.shp.hdr
    20180825_slc.shx
    20180825_slc.sml
```