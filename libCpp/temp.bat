setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin/lasboundary64 -i C:/CursoCEDEX3D/CasosPracticos/PoligonoIndustrialAB/pnoa_lidar_2017.laz   -keep_class 6 -disjoint -concavity 3.0 -o C:/CursoCEDEX3D/CasosPracticos/PoligonoIndustrialAB/pnoa_lidar_2017_buildings.shp
endlocal
