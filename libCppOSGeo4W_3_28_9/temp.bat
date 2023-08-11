setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCppOSGeo4W_3_28_9"
C:/lastools/bin/lasclip64 -i D:/Aicedrone/20230125_Rail/Metashape/202301XX_RAIL_recortada.las -olaz -poly  D:/Aicedrone/20230125_Rail/DatosAuxiliares/roi_1.shp -v -odir D:/Aicedrone/20230125_Rail/DatosAuxiliares
endlocal
