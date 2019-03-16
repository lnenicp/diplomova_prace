import arcpy
import parameters
import my_utils
#import utils
import sys

start = time.time()
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = 1

# nastaveni pracovni databaze
work_dtb = parameters.work_dtb
arcpy.env.workspace = '.\\{}.gdb'.format(work_dtb)
workspace = arcpy.env.workspace

# vstupni vrstvy
lower_edges = parameters.output_LE
contours_V = parameters.contours_V
rocks_contours = parameters.output_RC
left_buffer = parameters.left_LE_buffer_to_erase

# parametery
map_scale = parameters.map_scale
contours_size_3 = parameters.contour_size_3
gap_value = parameters.gap_value
gap_value = my_utils.calculate_real_size(map_scale, gap_value)
cheek_value = parameters.buff_size_V_value + gap_value #  misto parameters.buff_size_V_value byla hodnota 0.2
addition_value = gap_value
multiple = parameters.multiple
maximal_width_of_wall = parameters.maximal_width_of_wall
buff_size_cca_value = parameters.buff_size_cca_value
buff_size_V_value = parameters.buff_size_V_value

min_line_width = parameters.min_line_width
min_line_width = my_utils.calculate_real_size(map_scale, min_line_width)
max_line_width = parameters.max_line_width
max_line_width = my_utils.calculate_real_size(map_scale, max_line_width)

# vystupni vrstvy
output_CL = parameters.output_CL
basic_line_name = parameters.basic_line_name

## VYPOCET
## vytvoreni zakladni linie, podle ktere se budou kreslit tvarove cary
buff_size_LE_value = buff_size_V_value + my_utils.calculate_real_size(map_scale, contours_size_3)
buff_size_LE = '{} Meters'.format(buff_size_LE_value)
buff_LE = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_LE', buff_size_LE, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
buff_size_V = '{} Meters'.format(buff_size_V_value)
buff_V_01 = arcpy.Buffer_analysis(contours_V, 'tmp_buff_V_01', buff_size_V, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
buff_V = arcpy.Erase_analysis (buff_V_01, left_buffer, 'tmp_buff_V')

buff_LE_V_merge = arcpy.Merge_management ([buff_LE, buff_V], 'tmp_buff_LE_V_merge')
buff_LE_V_merge_diss = arcpy.Dissolve_management (buff_LE_V_merge, 'tmp_buff_LE_V_merge_diss')
buff_LE_V_merge_diss_lyr = arcpy.MakeFeatureLayer_management (buff_LE_V_merge_diss, 'tmp_buff_LE_V_merge_diss_lyr')
buff_LE_V_merge_diss_line = arcpy.PolygonToLine_management (buff_LE_V_merge_diss_lyr, 'tmp_buff_LE_V_merge_diss_line')

buff_size_cca = '{} Meters'.format(buff_size_cca_value)
erase_mask = arcpy.Buffer_analysis(buff_LE_V_merge_diss_line, 'tmp_erase_mask', buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
rocks_contours_lyr = arcpy.MakeFeatureLayer_management (rocks_contours, 'tmp_rocks_contours_lyr')
rocks_contours_line = arcpy.PolygonToLine_management (rocks_contours_lyr, 'tmp_rocks_contours_line')
# prvotni zakldni linie
basic_line_01 = arcpy.Erase_analysis(rocks_contours_line, erase_mask, 'tmp_basic_line_01')


# slouceni pripadnych multipart 'basic_line'
    # 'basic_lines' jsou vytvoreny z bufferu/polygonu - nekdy tedy dochazi k tomu, ze je jedna linie tvorena vice prvky
    # je tedy potreba vrstvu rozdelit a opet spojit podle prislusneho id linie
# overit, jestli neni atribut id_basic line_uplne zbytecnej
arcpy.MultipartToSinglepart_management (basic_line_01, 'tmp_basic_line_01_singlepart')
arcpy.MakeFeatureLayer_management('tmp_basic_line_01_singlepart', 'singlepart_lyr')
# odstraneni 'basic_lines', ktere jsou mensi nez 1 metr - vznikly pravdepodobne geometrickymi neprestnostmi a dela to neplechu
arcpy.SelectLayerByAttribute_management ('singlepart_lyr', '', "Shape_Length > 1")
basic_line = arcpy.Dissolve_management ('singlepart_lyr', basic_line_name, 'ORIG_FID','','SINGLE_PART')

arcpy.AddField_management (basic_line, 'id_basic_line', "SHORT")
u_cursor = arcpy.da.UpdateCursor(basic_line, ['OBJECTID','id_basic_line'])
for row in u_cursor:
    id = row[0]
    row[1]= id
    u_cursor.updateRow(row)
del u_cursor


## VYTVORENI VZOROVE VRSTVY tvarovych car
gap = "{} Meters".format(gap_value)
cheek = "{} Meters".format(cheek_value)
count_cl = int(maximal_width_of_wall / gap_value) # necham i tady kvuli vypoctu tloustek linii

# vytvoreni vrstvy, do ktere se budou vkladat jednotlive tc/buffery (buffers, tvar_cary)
arcpy.MakeFeatureLayer_management(basic_line, 'model_bl_lyr', '"OBJECTID" = 1')
buffers = arcpy.Buffer_analysis('model_bl_lyr','tmp_buffers', gap, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
arcpy.PolygonToLine_management(buffers, 'tmp_buffers_line')
arcpy.Buffer_analysis('model_bl_lyr', 'tmp_buffers_to_erase', cheek, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
arcpy.PolygonToLine_management('tmp_buffers_to_erase', 'tmp_buffers_to_erase_line')
tvar_cary = arcpy.Erase_analysis('tmp_buffers_line', 'tmp_buffers_to_erase_line', output_CL)
#arcpy.DeleteFeatures_management (buffers)
arcpy.DeleteFeatures_management (tvar_cary)
#arcpy.AddField_management(buffers, 'id_tc', 'SHORT')
arcpy.AddField_management(tvar_cary, 'id_tc', 'SHORT')
arcpy.AddField_management(tvar_cary, 'id_order', 'SHORT')

## VYTVORENI TC A BUFFERU
basic_lines_list = my_utils.create_list_of_values(basic_line, 'OBJECTID')
# print(basic_lines_list)
# basic_lines_list_select = basic_lines_list[1:2]


for id in basic_lines_list:#_select:# smazat
    print('id', id)
    whereID = '"OBJECTID" = {}'.format(id) #(basic_lines_list[id])
    one_bl = arcpy.MakeFeatureLayer_management(basic_line, 'one_bl_lyr', whereID)

    # nastavit pocatecni hodnoty gap/cheek
    gap_value = parameters.gap_value
    gap_value = my_utils.calculate_real_size(map_scale, gap_value)
    gap = '{} Meters'.format(gap_value)
    cheek_value = parameters.buff_size_V_value + gap_value  # misto parameters.buff_size_V_value byla hodnota 0.2
    cheek = '{} Meters'.format(cheek_value)
    count_cl = int(maximal_width_of_wall / gap_value)


    order = 1
    try:
        for i in range(1, (count_cl + 1)):
            # print('i', i)
            # buffer pro tvorbu TC
            one_buff = arcpy.Buffer_analysis(one_bl, 'tmp_buff', gap, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
            buff_line = arcpy.PolygonToLine_management('tmp_buff', 'tmp_buff_line')
            # buffer na odmazani bocnic
            arcpy.Buffer_analysis(one_bl, 'tmp_buff_to_erase', cheek, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')

            buff_to_erase_line = arcpy.PolygonToLine_management('tmp_buff_to_erase', 'tmp_buff_to_erase_line')
            buff_to_erase_line_mask = arcpy.Buffer_analysis(buff_to_erase_line, 'tmp_buff_to_erase_line_mask',
                                                            buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
            # odmazani
            tc = arcpy.Erase_analysis(buff_line, buff_to_erase_line_mask, 'tmp_tc')
            arcpy.AddField_management(tc, 'id_tc', 'SHORT')
            arcpy.AddField_management(tc, 'id_order', 'SHORT')
            arcpy.CalculateField_management(tc, 'id_tc', id)
            arcpy.CalculateField_management(tc, 'id_order', order)
            arcpy.Append_management(tc, tvar_cary)

            gap_value = (gap_value + addition_value) * multiple
            gap = "{} Meters".format(gap_value)
            cheek_value = (cheek_value + addition_value) * multiple
            cheek = "{} Meters".format(cheek_value)

            order = order + 1

    except Exception:
        continue

    arcpy.Delete_management(one_bl)


## VYPOCET TLOUSTKY TVAROVYCH CAR
my_utils.calculate_contour_line_size(tvar_cary, 'id_order', count_cl, min_line_width, max_line_width)


# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)


end = time.time()
print 'time', end-start
