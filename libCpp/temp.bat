setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin/lasboundary64 -i D:/qLidarProjects/IES_Almassora/ies_almassora.laz -use_bb -merged -o D:/qLidarProjects/IES_Almassora/boundary.shp
endlocal
