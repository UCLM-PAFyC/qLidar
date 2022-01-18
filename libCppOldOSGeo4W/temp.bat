setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin/las2dem64 -i D:/PhotogrammetryToolsProjects/20210729_Tarazona_Cebolla/export/302-20210729_Tarazona_cebolla_MICA_ground.laz -keep_class 2 -nodata -9999 -step 0.05 -o D:/PhotogrammetryToolsProjects/20210729_Tarazona_Cebolla/export/DTM-302-Tarazona_Cebolla_20210729_25830_5cm.tif
endlocal
