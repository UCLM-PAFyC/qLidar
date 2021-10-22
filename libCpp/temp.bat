setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin/las2dem64 -i D:/qLidarProjects/acopio_arcillas/acopio_arcillas_ground.laz -keep_class 0 1 2 -nodata -9999 -step 0.2 -o D:/qLidarProjects/acopio_arcillas/kk.tif
endlocal
