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
valley = parameters.valley
valley_superelev = parameters.output_V
lower_edges_superelev = parameters.output_LE
in_wall = parameters.in_wall
output_LE = parameters.output_LE
lower_edges = "lower_edges " # PREDELAT!!!!!!!!!!!!!!!!!!!!!!!!!

# vstupni parametry
map_scale = parameters.map_scale
contour_size_1 = parameters.contour_size_1
contour_size_2 = parameters.contour_size_2
contour_size_3 = parameters.contour_size_3
buffer_size_smooth_value = parameters.buffer_size_smooth_value
left_buffer_size_value = my_utils.calculate_real_size(map_scale, contour_size_3)

# vystupni vrstvy
output_RC = parameters.output_RC
contours_V = parameters.contours_V
left_LE_buffer_to_erase = parameters.left_LE_buffer_to_erase


## VYPOCET

"UDOLNICE"
# vypocet sirky bufferu pro jednotlive hodnoty/segmenty
my_utils.classify_contour_size(valley_superelev, map_scale, contour_size_1, contour_size_2, contour_size_3, 'FULL')

"UDOLNICE SE DOTYKAJI DOLNI HRANY"
# vyberu udolnice, ktere se dotykaji dolni hrany
valley_lyr = arcpy.MakeFeatureLayer_management (valley, 'valley_lyr')
arcpy.SelectLayerByLocation_management (valley_lyr, 'BOUNDARY_TOUCHES',output_LE)
valley_LE_touches = arcpy.CopyFeatures_management(valley_lyr, 'tmp_valley_LE_touches')

# vyberu segmenty, ktere pochazi z udolnic, ktere so dotykaji dolni hrany
valley_superelev_lyr = arcpy.MakeFeatureLayer_management (valley_superelev, 'valley_superelev_lyr')
arcpy.SelectLayerByLocation_management(valley_superelev_lyr,'SHARE_A_LINE_SEGMENT_WITH',valley_LE_touches)
valley_superelev_LE_touches = arcpy.CopyFeatures_management(valley_superelev_lyr, 'tmp_valley_superelev_LE_touches')

# vyber/vytvoreni vrstvy "koncovych" segmentu
end_segments_valley_LE_touches = my_utils.select_end_segments(valley_superelev_LE_touches, 'tmp_end_segments_valley_LE_touches')
# vyber/vytvoreni vrstvy "prvniho a vnitrnich" segmentu
inner_segments_valley_LE_touches = arcpy.Erase_analysis(valley_superelev_LE_touches, end_segments_valley_LE_touches, 'tmp_inner_segments_valley_LE_touches')
# konocove segmenty - buffer
end_s_buf_valley_LE_touches = arcpy.Buffer_analysis(end_segments_valley_LE_touches, 'tmp_ens_v_buff_LE_touches', 'contour_size', 'FULL', 'FLAT', 'NONE', '', 'PLANAR')
# prvni a vnitrni segmenty - buffer
in_s_buf_valley_LE_touches = arcpy.Buffer_analysis(inner_segments_valley_LE_touches, 'tmp_ins_v_buff_LE_touches', 'contour_size', 'FULL', 'ROUND', 'NONE', '', 'PLANAR')

"UDOLNICE PROTINA UDOLNICI"
# vyberu udolnice, ktere protinaji jinou udolnici, ale nedotykaji se dolni hrany
valley_lyr = arcpy.MakeFeatureLayer_management (valley, 'valley_lyr')
arcpy.SelectLayerByLocation_management (valley_lyr, 'CROSSED_BY_THE_OUTLINE_OF', valley_LE_touches)
valley_cross_valley = arcpy.CopyFeatures_management(valley_lyr, 'tmp_valley_cross_valley')

# vyberu segmenty, ktere pochazi z udolnic, ktere so dotykaji dolni hrany
valley_superelev_lyr = arcpy.MakeFeatureLayer_management (valley_superelev, 'valley_superelev_lyr')
arcpy.SelectLayerByLocation_management(valley_superelev_lyr,'SHARE_A_LINE_SEGMENT_WITH',valley_cross_valley)
valley_superelev_cross_valley = arcpy.CopyFeatures_management(valley_superelev_lyr, 'tmp_valley_superelev_cross_valley')

# vyber/vytvoreni vrstvy "krajnich" segmentu
extreme_segments_valley_cross_valley = my_utils.select_extreme_segments(valley_superelev_cross_valley, 'tmp_extreme_segments_valley_cross_valley')
# vyber/vytvoreni vrstvy "vnitrnich" segmentu
inner_segments_valley_cross_valley = arcpy.Erase_analysis(valley_superelev_cross_valley, extreme_segments_valley_cross_valley, 'tmp_inner_segments_valley_cross_valley')
# krajni segmenty - buffer
extreme_s_buf_valley_cross_valley = arcpy.Buffer_analysis(extreme_segments_valley_cross_valley, 'tmp_ens_v_buff_cross_valley', 'contour_size', 'FULL', 'FLAT', 'NONE', '', 'PLANAR')
# vnitrni segmenty - buffer
in_s_buf_valley_LE_cross_valley = arcpy.Buffer_analysis(inner_segments_valley_cross_valley, 'tmp_ins_v_buff_cross_valley', 'contour_size', 'FULL', 'ROUND', 'NONE', '', 'PLANAR')



"DOLNI HRANY"
# vypocet sirky bufferu pro jednotlive hodnoty/segmenty
my_utils.classify_contour_size(lower_edges_superelev, map_scale, contour_size_1, contour_size_2, contour_size_3, 'RIGHT')
# vyber/vytvoreni vrstvy "koncovych/okrajovych" segmentu
extreme_segments_lower_edges = my_utils.select_extreme_segments(lower_edges_superelev, 'tmp_extreme_segments_valley')
# vyber/vytvoreni vrstvy "vnitrnich" segmentu
inner_segments_lower_edges = arcpy.Erase_analysis(lower_edges_superelev, extreme_segments_lower_edges, 'tmp_inner_segments_valley')
# okrajove segmenty
extreme_s_buf_lower_edges = arcpy.Buffer_analysis(extreme_segments_lower_edges, 'tmp_ens_le_buff', 'contour_size', 'RIGHT', 'FLAT', 'NONE', '', 'PLANAR')
# vnitrni segmenty
in_s_buf_lower_edges = arcpy.Buffer_analysis(inner_segments_lower_edges, 'tmp_ins_le_buff', 'contour_size', 'RIGHT', 'ROUND', 'NONE', '', 'PLANAR')


## slouceni dolnich hran a udolnic
#merge_all = arcpy.Merge_management ([end_s_buf_valley_LE_touches, in_s_buf_valley_LE_touches, extreme_s_buf_valley_cross_valley, in_s_buf_valley_LE_cross_valley, extreme_s_buf_lower_edges, in_s_buf_lower_edges], 'tmp_merge_all')
#dissolve = arcpy.Dissolve_management(merge_all, 'tmp_merge_diss', 'id_line', '', 'MULTI_PART ','')

# slouceni segmentu dolnich hran dle ID linie
merge_segments_LE =  arcpy.Merge_management ([extreme_s_buf_lower_edges, in_s_buf_lower_edges], 'tmp_merge_segments_LE')
dissolve_LE = arcpy.Dissolve_management(merge_segments_LE, 'tmp_merge_segments_LE_diss', 'id_line', '', 'MULTI_PART','')

# slouceni segmentu udolnic, dle ID linie
#try:
merge_segments_valley = arcpy.Merge_management([end_s_buf_valley_LE_touches, in_s_buf_valley_LE_touches, extreme_s_buf_valley_cross_valley, in_s_buf_valley_LE_cross_valley], 'tmp_merge_segments_valley')
#except:
#   merge_segments_valley = ([end_s_buf_valley_LE_touches, in_s_buf_valley_LE_touches], 'tmp_merge_segments_valley')
dissolve_valley = arcpy.Dissolve_management(merge_segments_valley, 'tmp_merge_segments_valley_diss', 'id_line', '', 'MULTI_PART','')

# odmazani podle dolni hrany
    # (casti presahovaly az za hranice dolni hrany)
left_buffer_size = '{} Meters'.format(left_buffer_size_value)
# pro kazdou dolni hranu vytvorim samostatny polygon left bufferu (nakonec vse v jedne vrstve)
s_cur = arcpy.da.SearchCursor(lower_edges, ['OBJECTID'])
for row in s_cur:
    # vyberu jednu linii (podle id)
    if row[0] == 1:
        whereID = '"OBJECTID" = {}'.format(row[0])
        one_line = arcpy.MakeFeatureLayer_management(lower_edges, 'one_line_lyr', whereID)
        left_buffer = arcpy.Buffer_analysis(one_line, left_LE_buffer_to_erase, left_buffer_size, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
        arcpy.AddField_management(left_buffer, 'id_line', 'SHORT')
        arcpy.CalculateField_management(left_buffer, 'id_line', row[0])
    else:
        whereID = '"OBJECTID" = {}'.format(row[0])
        one_line = arcpy.MakeFeatureLayer_management(lower_edges, 'one_line_lyr', whereID)
        one_buff = arcpy.Buffer_analysis(one_line, 'tmp_one_buff', left_buffer_size, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
        arcpy.AddField_management(one_buff, 'id_line', 'SHORT')
        arcpy.CalculateField_management(one_buff, 'id_line', row[0])
        arcpy.Append_management(one_buff, left_buffer)
del s_cur

# odmazavni nezadoucich "presahu"
# pokud byla kontura a buffer vytvoreny od stejne linie, bude kontura odmazana bufferem
contours_cursor = arcpy.da.SearchCursor(dissolve_LE, ['id_line'])
for contur in contours_cursor:
    id_contour = contur[0]

    whereID = '"id_line" = {}'.format(id_contour)
    one_contour = arcpy.MakeFeatureLayer_management(dissolve_LE, 'one_contour_lyr', whereID)

    buffer_cursor = arcpy.da.SearchCursor(left_buffer, ['id_line'])
    for buffer in buffer_cursor:
        id_buffer = buffer[0]

        if id_buffer == id_contour:
            whereID = '"id_line" = {}'.format(id_contour)
            one_buffer = arcpy.MakeFeatureLayer_management(left_buffer, 'one_buffer_lyr', whereID)
            if id_contour == 1:
                contours_LE = arcpy.Erase_analysis(one_contour, one_buffer, 'tmp_contours_LE')
            else:
                one_clipped_contour = arcpy.Erase_analysis(one_contour, one_buffer, 'tmp_one_clipped_contour')
                arcpy.Append_management(one_clipped_contour, contours_LE)
    del buffer_cursor
del contours_cursor


contours_valley = arcpy.Erase_analysis (dissolve_valley, left_buffer, 'tmp_contours_valley')

merge_all = arcpy.Merge_management ([contours_LE, contours_valley], 'tmp_merge_all')
dissolve_all = arcpy.Dissolve_management(merge_all, 'tmp_merge_diss') #, 'id_line', '', 'MULTI_PART ','')

            


#left_buffer_size = '{} Meters'.format(left_buffer_size_value)
#print('left_buffer_size',left_buffer_size)
#left_buffer = arcpy.Buffer_analysis(lower_edges_superelev, left_LE_buffer_to_erase, left_buffer_size, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
#result = arcpy.Erase_analysis (dissolve, left_buffer, 'tmp_result')

# "zaobleni" vysledne podoby
buffer_size_smooth_positive = '{} Meters'.format(buffer_size_smooth_value)
buffer_size_smooth_negative = '{} Meters'.format(buffer_size_smooth_value * (-1))

arcpy.Buffer_analysis(dissolve_all, 'tmp_add_buff', buffer_size_smooth_positive, 'FULL', 'ROUND', 'NONE', '', 'PLANAR')
arcpy.Buffer_analysis('tmp_add_buff', output_RC, buffer_size_smooth_negative, 'FULL', 'ROUND', 'NONE', '', 'PLANAR')

### vytvoreni pomocnych vstupnich vrstev pro kresbu tvarovych car
# pomocna vrstva - kontury udolnic
merge_V = arcpy.Merge_management ([extreme_s_buf_valley_cross_valley, in_s_buf_valley_LE_cross_valley, extreme_s_buf_lower_edges, in_s_buf_lower_edges], 'tmp_merge_V')
arcpy.Dissolve_management (merge_V, 'tmp_contours_V', 'id_line')
arcpy.Erase_analysis ('tmp_contours_V', left_buffer, contours_V)


# "zaverecny_uklid"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)


end = time.time()
print 'time', end-start


