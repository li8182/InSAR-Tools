# -*- coding: utf-8 -*-

envi_hdr = """ENVI
description = {
   ANCILLARY INFO = DEM.
   File generated with SARscape  5.2.1 }

samples                   = re_sample
lines                     = re_line
bands                     = 1
headeroffset              = 0
file type                 = ENVI Standard
data type                 = 2
sensor type               = Unknown
interleave                = bsq
byte order                = 0
map info = {Geographic Lat/Lon, 1, 1, re_lon_west, re_lat_north, re_interval, re_interval, WGS-84, 
 units=Degrees}
x start                   = 1
y start                   = 1
"""

envi_sml = """<?xml version="1.0" ?>
<HEADER_INFO xmlns="http://www.sarmap.ch/xml/SARscapeHeaderSchema"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://www.sarmap.ch/xml/SARscapeHeaderSchema
	http://www.sarmap.ch/xml/SARscapeHeaderSchema/SARscapeHeaderSchema_version_1.0.xsd">
   <RasterInfo>
      <HeaderOffset>0</HeaderOffset>
      <RowPrefix>0</RowPrefix>
      <RowSuffix>0</RowSuffix>
      <CellType>SHORT</CellType>
      <DataUnits>DEM</DataUnits>
      <NullCellValue>NaN</NullCellValue>
      <NrOfChannels>1</NrOfChannels>
      <NrOfPixelsPerLine>re_sample</NrOfPixelsPerLine>
      <NrOfLinesPerImage>re_line</NrOfLinesPerImage>
      <GeocodedImage>OK</GeocodedImage>
      <Interleave>LAYOUT_BSQ</Interleave>
      <BytesOrder>LSBF</BytesOrder>
      <OtherInfo>
         <MatrixString NumberOfRows = "3" NumberOfColumns = "2">
            <MatrixRowString ID = "0">
               <ValueString ID = "0">description</ValueString>
               <ValueString ID = "1">{ENVI Mosaic [Fri Jun 21 15:55:20 2019]}</ValueString>
            </MatrixRowString>
            <MatrixRowString ID = "1">
               <ValueString ID = "0">sensor type</ValueString>
               <ValueString ID = "1">Unknown</ValueString>
            </MatrixRowString>
            <MatrixRowString ID = "2">
               <ValueString ID = "0">SOFTWARE</ValueString>
               <ValueString ID = "1">SARscape ENVI  5.2.1 Jan  9 2017  W64</ValueString>
            </MatrixRowString>
         </MatrixString>
      </OtherInfo>
   </RasterInfo>
   <CartographicSystem>
      <State>GEO-GLOBAL</State>
      <Hemisphere></Hemisphere>
      <Projection>GEO</Projection>
      <Zone></Zone>
      <Ellipsoid>WGS84</Ellipsoid>
      <DatumShift></DatumShift>
   </CartographicSystem>
   <RegistrationCoordinates>
      <LatNorthing>re_lat_north</LatNorthing>
      <LonEasting>re_lon_west</LonEasting>
      <PixelSpacingLatNorth>-re_interval</PixelSpacingLatNorth>
      <PixelSpacingLonEast>re_interval</PixelSpacingLonEast>
   </RegistrationCoordinates>
   <DEMCoordinates>
      <EastingCoordinateBegin>re_lon_west</EastingCoordinateBegin>
      <EastingCoordinateEnd>re_lon_east</EastingCoordinateEnd>
      <EastingGridSize>re_interval</EastingGridSize>
      <NorthingCoordinateBegin>re_lat_south</NorthingCoordinateBegin>
      <NorthingCoordinateEnd>re_lat_north</NorthingCoordinateEnd>
      <NorthingGridSize>re_interval</NorthingGridSize>
   </DEMCoordinates>
</HEADER_INFO>
"""

gamma_par = """Gamma DIFF&GEO DEM/MAP parameter file
title: Xiongben
DEM_projection:     EQA
data_format:        REAL*4
DEM_hgt_offset:          0.00000
DEM_scale:               1.00000
width:                re_sample
nlines:               re_line
corner_lat:      re_lat_north.00  decimal degrees
corner_lon:      re_lon_west.00 decimal degrees
post_lat:    -re_interval decimal degrees
post_lon:    re_interval decimal degrees

ellipsoid_name: WGS 84
ellipsoid_ra:        6378137.000   m
ellipsoid_reciprocal_flattening:  298.2572236

datum_name: WGS 1984
datum_shift_dx:              0.000   m
datum_shift_dy:              0.000   m
datum_shift_dz:              0.000   m
datum_scale_m:         0.00000e+00
datum_rotation_alpha:  0.00000e+00   arc-sec
datum_rotation_beta:   0.00000e+00   arc-sec
datum_rotation_gamma:  0.00000e+00   arc-sec
datum_country_list Global Definition, WGS84, World
"""
