import arcpy
#import parameters
#import my_utils
#import utils

start = time.time()

#Check the Spatial extension
arcpy.CheckOutExtension('Spatial')

arcpy.env.overwriteOutput = 1
arcpy.env.workspace = '.\\PB.gdb'
workspace = arcpy.env.workspace

# inputs
lower_edges = 'superelevation_lower_edges'
# contours_LE = 'contours_LE'
contours_V = 'contours_V'
rocks_contours = 'rocks_contours_500'
left_buffer = 'left_buff'
# space_value = 2

buff_size_LE = '3,4 Meters' # promenlive podle meritka!!!
buff_LE = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_LE', buff_size_LE, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
buff_size_V = '0,5 Meters' # promenlive podle meritka!!!
buff_V_01 = arcpy.Buffer_analysis(contours_V, 'tmp_buff_c_V_01', buff_size_V, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
buff_V = arcpy.Erase_analysis (buff_V_01, left_buffer, 'tmp_buff_V')
# jeste odmazat podle leveho bufferu z predchoziho scriptu

buff_LE_V_merge = arcpy.Merge_management ([buff_LE, buff_V], 'tmp_buff_LE_V_merge')
buff_LE_V_merge_diss = arcpy.Dissolve_management (buff_LE_V_merge, 'tmp_buff_LE_V_merge_diss')
buff_LE_V_merge_diss_lyr = arcpy.MakeFeatureLayer_management (buff_LE_V_merge_diss, 'tmp_buff_LE_V_merge_diss_lyr')
buff_LE_V_merge_diss_line = arcpy.PolygonToLine_management (buff_LE_V_merge_diss_lyr, 'tmp_buff_LE_V_merge_diss_line')

buff_size_cca = '0,1 Meters'
erase_mask = arcpy.Buffer_analysis(buff_LE_V_merge_diss_line, 'tmp_erase_mask', buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')

rocks_contours_lyr = arcpy.MakeFeatureLayer_management (rocks_contours, 'tmp_rocks_contours_lyr')
rocks_contours_line = arcpy.PolygonToLine_management (rocks_contours_lyr, 'tmp_rocks_contours_line')


basic_line = arcpy.Erase_analysis(rocks_contours_line, erase_mask, 'tmp_basic_line')


'''
# vyber prislusne linie hlavni kontury
c_line = arcpy.PolygonToLine_management (contours_LE, 'tmp_contour_line')

# vytvoreni maleho bufferu okolo dolni hrany - slouzi k odmazani "shlazene" dolni hrany - mozna bude stacit jneom safe_2
buff_safe = '0,1 Meters'
#safe_1 = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_safe_1', buff_safe, 'FULL', 'FLAT', 'ALL', '', 'PLANAR')

# buffer slouzici k odmazani bocnic
buff_bocnice = '2,5 Meters'
safe_2 = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_safe_2', buff_bocnice, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
safe_2_line = arcpy.PolygonToLine_management (safe_2, 'tmp_buff_safe_line')
safe_2_line_buff = arcpy.Buffer_analysis(safe_2_line, 'tmp_buff_safe_line_buff', buff_safe, 'FULL', 'FLAT', 'ALL', '', 'PLANAR')

#arcpy.Erase_analysis (c_line, safe_1, 'tmp_erase_1')
base_line = arcpy.Erase_analysis (c_line, safe_2_line_buff, 'tmp_erase_2')
'''
mezera = '0,5 Meters'
mezera_val = 0.5
bocnice = '0,7 Meters'
mez = 20
pocet = int(mez / mezera_val)
zaklad = basic_line
for i in range(1,pocet):
    if i == 1:
        # buffer pro tvorbu TC
        arcpy.Buffer_analysis(zaklad, 'tmp_buff', mezera, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
        arcpy.PolygonToLine_management('tmp_buff', 'tmp_buff_line')
        # buffer na odmazani bocnic
        arcpy.Buffer_analysis(zaklad, 'tmp_buff_to_erase', bocnice, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
        arcpy.PolygonToLine_management('tmp_buff_to_erase', 'tmp_buff_to_erase_line')
        # odmazani
        tc = arcpy.Erase_analysis('tmp_buff_line', 'tmp_buff_to_erase_line', 'tvarove_cary_500_01_20')
    else:
        # buffer pro tvorbu TC
        arcpy.Buffer_analysis(zaklad, 'tmp_buff', mezera, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
        arcpy.PolygonToLine_management('tmp_buff', 'tmp_buff_line')
        # buffer na odmazani bocnic
        arcpy.Buffer_analysis(zaklad, 'tmp_buff_to_erase', bocnice, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
        arcpy.PolygonToLine_management('tmp_buff_to_erase', 'tmp_buff_to_erase_line')
        # odmazani
        tc = arcpy.Erase_analysis('tmp_buff_line', 'tmp_buff_to_erase_line', 'tmp_TC')
        arcpy.Append_management(tc, 'tvarove_cary_500_01_20')
    zaklad = tc
    i = i + 1

# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)

end = time.time()
print 'time', end-start
