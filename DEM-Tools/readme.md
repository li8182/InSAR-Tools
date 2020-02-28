## DEM Tools

1. 下载SRTM 90m DEM 和ALOS 30m DEM
2. 根据下载的SRTM和ALOS DEM的tif文件名，自动读取、拼接tif，并给出经纬度范围
3. 读取、拼接tif后，直接生成适用于ENVI（已验证）、GAMMA（待验证）和Doris（无法生成参数文件）的DEM
4. 读取、拼接tif后，再根据经纬度，将经纬度、高程写入到文本文件中，用于GMT绘图