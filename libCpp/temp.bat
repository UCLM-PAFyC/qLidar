setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin/las2dem64 -i D:/qLidarProjects/IndustrialParkCampollanoAB/data/lidar_2009/pnoa_lidar_2009.laz -keep_class 2 6 -nodata -9999 -step 1.0 -o D:/qLidarProjects/IndustrialParkCampollanoAB/data/lidar_2009/pnoa_lidar_2009_dsm_building.tif
endlocal
