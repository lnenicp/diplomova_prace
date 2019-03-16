import arcpy
import parameters
import my_utils
import time


start = time.time()
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = 1

# nastaveni pracovni databaze
work_dtb = parameters.work_dtb
arcpy.env.workspace = '.\\{}.gdb'.format(work_dtb)
workspace = arcpy.env.workspace

## NASTAVENI
# vstupni vrstvy
valley_superelev = parameters.output_V
lower_edges_superelev = parameters.output_LE
in_wall = parameters.in_wall

# vstupni parametry
map_scale = parameters.map_scale
contour_size_1 = parameters.contour_size_1
contour_size_2 = parameters.contour_size_2
contour_size_3 = parameters.contour_size_3
buffer_size_smooth_value = parameters.buffer_size_smooth_value

# vystupni vrstvy
output_RC = parameters.output_RC
contours_LE = parameters.contours_LE
contours_V = parameters.contours_V
left_LE_buffer_to_erase = parameters.left_LE_buffer_to_erase

## VYPOCET

## UDOLNICE
# vypocet sirky bufferu pro jednotlive hodnoty/segmenty
my_utils.classify_contour_size(valley_superelev, map_scale, contour_size_1, contour_size_2, contour_size_3, 'FULL')
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
my_utils.classify_contour_size(lower_edges_superelev, map_scale, contour_size_1, contour_size_2, contour_size_3, 'RIGHT')
# vyber/vytvoreni vrstvy "koncovych/okrajovych" segmentu
end_segments_lower_edges = my_utils.select_end_segments(lower_edges_superelev, 'tmp_end_segments_valley')
# vyber/vytvoreni vrstvy "vnitrnich" segmentu
inner_segments_lower_edges = arcpy.Erase_analysis(lower_edges_superelev, end_segments_valley, 'tmp_inner_segments_valley')
# okrajove segmenty
end_s_buf_lower_edges = arcpy.Buffer_analysis(end_segments_lower_edges, 'tmp_ens_le_buff', 'contour_size', 'RIGHT', 'FLAT', 'NONE', '', 'PLANAR')
# vnitrni segmenty
in_s_buf_lower_edges = arcpy.Buffer_analysis(inner_segments_lower_edges, 'tmp_ins_le_buff', 'contour_size', 'RIGHT', 'ROUND', 'NONE', '', 'PLANAR')


## slouceni dolnich hran a udolnic
merge_all = arcpy.Merge_management ([end_s_buf_lower_edges, in_s_buf_lower_edges, end_s_buf_valley, in_s_buf_valley ], 'tmp_merge_all')
dissolve = arcpy.Dissolve_management(merge_all, 'tmp_merge_diss')

# odmazani podle dolni hrany
    # (casti presahovaly az za hranice dolni hrany)
left_buffer = arcpy.Buffer_analysis(lower_edges_superelev, left_LE_buffer_to_erase, '2 Meters', 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
result = arcpy.Erase_analysis (dissolve, left_buffer, 'tmp_result')

# "zaobleni" vysledne podoby
buffer_size_smooth_positive = '{} Meters'.format(buffer_size_smooth_value)
buffer_size_smooth_negative = '{} Meters'.format(buffer_size_smooth_value * (-1))

arcpy.Buffer_analysis(result, 'tmp_add_buff', buffer_size_smooth_positive, 'FULL', 'ROUND', 'NONE', '', 'PLANAR')
arcpy.Buffer_analysis('tmp_add_buff', output_RC, buffer_size_smooth_negative, 'FULL', 'ROUND', 'NONE', '', 'PLANAR')

### vytvoreni pomocnych vstupnich vrstev pro kresbu tvarovych car
# pomocna vrstva - kontury udolnic
merge_V = arcpy.Merge_management ([end_s_buf_valley, in_s_buf_valley ], 'tmp_merge_V')
arcpy.Dissolve_management (merge_V, 'tmp_contours_V', 'id_line')
contours_valley = arcpy.Erase_analysis ('tmp_contours_V', left_buffer, contours_V)


# "zaverecny_uklid"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)


end = time.time()
print 'time', end-start


