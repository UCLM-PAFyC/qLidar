setlocal
cd "E:/dev/src/python/qgis3/qLidar/libCpp"
C:/LAStools2022/bin\lastile64 -i C:/temp/rover_balazote/20221021_Rover_Balazote.las -cores 4 -buffer 10.00 -tile_size 50.00 -flag_as_withheld -v -olaz -odir C:/temp/rover_balazote/temp\1
C:/LAStools2022/bin\lasthin64 -i C:/temp/rover_balazote/temp\1\*.laz -step 0.90 -percentile 20.00 20.00 -classify_as 8 -v -olaz -odir C:/temp/rover_balazote/temp\2
rd /s /q "C:/temp/rover_balazote/temp\1"
C:/LAStools2022/bin\lasnoise64 -i C:/temp/rover_balazote/temp\2\*.laz -ignore_class 0 -step_xy 2.00 -step_z 0.50 -isolated 3 -classify_as 12 -v -olaz -odir C:/temp/rover_balazote/temp\3
rd /s /q "C:/temp/rover_balazote/temp\2"
C:/LAStools2022/bin\lasground64 -i C:/temp/rover_balazote/temp\3\*.laz -ignore_class 0 12 -town -ultra_fine -v -olaz -odir C:/temp/rover_balazote/temp\4
rd /s /q "C:/temp/rover_balazote/temp\3"
C:/LAStools2022/bin\lasheight64 -i C:/temp/rover_balazote/temp\4\*.laz -classify_below -0.20 7 -classify_above -0.20 1 -v -olaz -odir C:/temp/rover_balazote/temp\5
rd /s /q "C:/temp/rover_balazote/temp\4"
C:/LAStools2022/bin\lasthin64 -i C:/temp/rover_balazote/temp\5\*.laz -step 0.25 -ignore_class 7 -classify_as 8 -lowest -v -olaz -odir C:/temp/rover_balazote/temp\6
rd /s /q "C:/temp/rover_balazote/temp\5"
C:/LAStools2022/bin\lasground64 -i C:/temp/rover_balazote/temp\6\*.laz -ignore_class 1 7 -bulge 0.10 -town -extra_fine -v -olaz -odir C:/temp/rover_balazote/temp\7
rd /s /q "C:/temp/rover_balazote/temp\6"
C:/LAStools2022/bin\lasheight64 -i C:/temp/rover_balazote/temp\7\*.laz -classification 2 -drop_below 0.20 -v -olaz -odir C:/temp/rover_balazote/temp\8
C:/LAStools2022/bin\las2las64 -i C:/temp/rover_balazote/temp\7\*.laz -keep_class 2 -v -olaz -odir C:/temp/rover_balazote/temp\ground
rd /s /q "C:/temp/rover_balazote/temp\7"
C:/LAStools2022/bin\lasmerge64 -i C:/temp/rover_balazote/temp\ground\*.laz -drop_withheld -v -o C:/temp/rover_balazote/temp\9\ground.laz
C:/LAStools2022/bin\lasmerge64 -i C:/temp/rover_balazote/temp\8\*.laz -drop_withheld -v -o C:/temp/rover_balazote/temp\9\objects.laz
rd /s /q "C:/temp/rover_balazote/temp\8"
rd /s /q "C:/temp/rover_balazote/temp\ground"
C:/LAStools2022/bin\lasmerge64 -i C:/temp/rover_balazote/temp\9\*.laz -v -o C:/temp/rover_balazote/temp\9\temp.laz
C:/LAStools2022/bin\lasthin64 -i C:/temp/rover_balazote/temp\9\temp.laz -ignore_class 7 -adaptive 0.20 0.50 -v -o C:/temp/rover_balazote/20221021_Rover_Balazote_classified.laz
rd /s /q "C:/temp/rover_balazote/temp\9"
endlocal
