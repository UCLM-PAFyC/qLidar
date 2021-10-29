setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin/las2dem64 -i C:/CursoCEDEX3D/CasosPracticos/Cubicacion/Cubicacion_ground.laz -nodata -9999 -step 0.1 -o C:/CursoCEDEX3D/CasosPracticos/Cubicacion/Cubicacion_dsm.tif
endlocal
