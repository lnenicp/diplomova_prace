import arcpy
import parameters
import my_utils
import time


start = time.time()

#Check the Spatial extension
arcpy.CheckOutExtension('Spatial')

arcpy.env.overwriteOutput = 1
arcpy.env.workspace = '.\\PB.gdb'
workspace = arcpy.env.workspace


# inputs
valley_superelev = parameters.valley_superelev
lower_edges_superelev = parameters.lower_edges_superelev
map_scale = parameters.map_scale
in_wall = parameters.in_wall
output98 = parameters.output98


## UDOLNICE
# vypocet sirky bufferu pro jednotlive hodnoty/segmenty
my_utils.classify_contour_size(valley_superelev, map_scale, 'FULL')
# vyber/vytvoreni vrstvy "koncovych/okrajovych" segmentu
end_segments_valley = my_utils.select_end_segments(valley_superelev, 'tmp_end_segments_valley')
# vyber/vytvoreni vrstvy "vnitrnich" segmentu
inner_segments_valley = arcpy.Erase_analysis(valley_superelev, end_segments_valley, 'tmp_inner_segments_valley')
# okrajove segmenty
end_s_buf_valley = arcpy.Buffer_analysis(end_segments_valley, 'tmp_ens_v_buff', 'contour_size', 'FULL', 'FLAT', 'NONE', '', 'PLANAR')
# vnitrni segmenty
in_s_buf_valley = arcpy.Buffer_analysis(inner_segments_valley, 'tmp_ins_v_buff', 'contour_size', 'FULL', 'ROUND', 'NONE', '', 'PLANAR')


## DOLNI HRANY
# vypocet sirky bufferu pro jednotlive hodnoty/segmenty
my_utils.classify_contour_size(lower_edges_superelev, map_scale, 'RIGHT')
# vyber/vytvoreni vrstvy "koncovych/okrajovych" segmentu
end_segments_lower_edges = my_utils.select_end_segments(lower_edges_superelev, 'tmp_end_segments_valley')
# vyber/vytvoreni vrstvy "vnitrnich" segmentu
inner_segments_lower_edges = arcpy.Erase_analysis(lower_edges_superelev, end_segments_valley, 'tmp_inner_segments_valley')
# okrajove segmenty
end_s_buf_lower_edges = arcpy.Buffer_analysis(end_segments_lower_edges, 'tmp_ens_le_buff', 'contour_size', 'RIGHT', 'FLAT', 'NONE', '', 'PLANAR')
# vnitrni segmenty
in_s_buf_lower_edges = arcpy.Buffer_analysis(inner_segments_lower_edges, 'tmp_ins_le_buff', 'contour_size', 'RIGHT', 'ROUND', 'NONE', '', 'PLANAR')

##
# slouceni okrajovych a vnitrnich segmentu DOLNICH HRAN zpet do jedne vrstvy
# merge_LE = arcpy.Merge_management ([end_s_buf_lower_edges, in_s_buf_lower_edges], 'tmp_merge_LE')


# oriznuti vznikle kontury podle sten - odstrani "osklivosti" u mensich meritek
#clip_merge_LE = arcpy.Clip_analysis (merge_LE, in_wall, 'tmp_clip_merge_LE')

# slouceni DOLNICH HRAN s ookrajovymi a vnitrnimi segmenty udolnic
# merge_all = arcpy.Merge_management ([clip_merge_LE, end_s_buf_valley, in_s_buf_valley ], 'tmp_merge_all')
# vytvoreni vystupu - jedna "multivrstva"
# dissolve = arcpy.Dissolve_management(merge_all, 'tmp_merge_diss')



merge_all = arcpy.Merge_management ([end_s_buf_lower_edges, in_s_buf_lower_edges, end_s_buf_valley, in_s_buf_valley ], 'tmp_merge_all')
dissolve = arcpy.Dissolve_management(merge_all, 'tmp_merge_diss')

# odmazani prave strany dolni hrany
left_buffer = arcpy.Buffer_analysis(lower_edges_superelev, 'left_buff', '2 Meters', 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
result = arcpy.Erase_analysis (dissolve, left_buffer, 'tmp_result')

###
# pomocna vrstva - kontury dolnich hran
merge_LE = arcpy.Merge_management ([end_s_buf_lower_edges, in_s_buf_lower_edges], 'tmp_merge_LE')
arcpy.Dissolve_management (merge_LE, 'tmp_contours_LE', 'id_line')
contours_LE = arcpy.Erase_analysis ('tmp_contours_LE', left_buffer, 'contours_LE_500')

# pomocna vrstva - kontury udolnic
merge_V = arcpy.Merge_management ([end_s_buf_valley, in_s_buf_valley ], 'tmp_merge_V')
arcpy.Dissolve_management (merge_V, 'tmp_contours_V', 'id_line')
contours_V = arcpy.Erase_analysis ('tmp_contours_V', left_buffer, 'contours_V_500')

# "zaobleni vysledne podoby
# '0,3 Meters' nahradit nejvetsi tloustkou kontury
arcpy.Buffer_analysis(result, 'tmp_add_buff', '0,3 Meters', 'FULL', 'ROUND', 'NONE', '', 'PLANAR')
arcpy.Buffer_analysis('tmp_add_buff', output98, '-0,3 Meters', 'FULL', 'ROUND', 'NONE', '', 'PLANAR')


# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)

end = time.time()
print 'time', end-start

'''
Mozna jeste procisteni vrstvy od zbytecnych atributu?
'''