setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2021/bin\lastile64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/UAV_Lidar_LineaElectrica.laz -cores 4 -buffer 10.0 -tile_size 50.0 -flag_as_withheld -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\1
C:/LAStools2021/bin\lasthin64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\1\*.laz -step 0.9 -percentile 20.0 20.0 -classify_as 8 -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\2
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\1"
C:/LAStools2021/bin\lasnoise64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\2\*.laz -ignore_class 0 -step_xy 2.0 -step_z 0.5 -isolated 3 -classify_as 12 -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\3
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\2"
C:/LAStools2021/bin\lasground64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\3\*.laz -ignore_class 0 12 -town -ultra_fine -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\4
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\3"
C:/LAStools2021/bin\lasheight64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\4\*.laz -classify_below -0.20 7 -classify_above -0.20 1 -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\5
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\4"
C:/LAStools2021/bin\lasthin64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\5\*.laz -step 0.25 -ignore_class 7 -classify_as 8 -lowest -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\6
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\5"
C:/LAStools2021/bin\lasground64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\6\*.laz -ignore_class 1 7 -bulge 0.10 -town -extra_fine -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\7
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\6"
C:/LAStools2021/bin\lasheight64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\7\*.laz -classification 2 -drop_below 0.20 -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\8
C:/LAStools2021/bin\las2las64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\7\*.laz -keep_class 2 -v -olaz -odir C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\ground
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\7"
C:/LAStools2021/bin\lasmerge64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\ground\*.laz -drop_withheld -v -o C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\9\ground.laz
C:/LAStools2021/bin\lasmerge64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\8\*.laz -drop_withheld -v -o C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\9\objects.laz
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\8"
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\ground"
C:/LAStools2021/bin\lasmerge64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\9\*.laz -v -o C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\9\temp.laz
C:/LAStools2021/bin\lasthin64 -i C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\9\temp.laz -ignore_class 7 -adaptive 0.20 0.5 -v -o C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/UAV_Lidar_LineaElectrica_ground.laz
rd /s /q "C:/CursoCEDEX3D/CasosPracticos/LineaElectrica/UAV_Camera/temp\9"
endlocal
