setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2022/bin/lasclip64 -i D:/qLidarProjects/IncendioLietor2016/data/lidar_2016/pnoa_lidar_2016.laz -olaz -poly  D:/qLidarProjects/IncendioLietor2016/data/roi/DelimitacionFotoInterpretadaPNOA2018.shp -v -odir D:/qLidarProjects/IncendioLietor2016/data
endlocal
