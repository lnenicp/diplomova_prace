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
cheek_value = 0.2 + gap_value
addition_value = gap_value # parameters.
multiple = parameters.multiple
maximal_width_of_wall = parameters.maximal_width_of_wall

min_line_width = parameters.min_line_width
min_line_width = my_utils.calculate_real_size(map_scale, min_line_width)
max_line_width = parameters.max_line_width
max_line_width = my_utils.calculate_real_size(map_scale, max_line_width)
# vystupni vrstvy
output_CL = parameters.output_CL
#buffers_CL = parameters.buffers_CL

## vytvoreni zakladni linie, podle ktere se budou kreslit tvarove cary
# buff_size_LE = '3,4 Meters' # promenlive podle meritka!!!
buff_size_LE_value = 0.3 + my_utils.calculate_real_size(map_scale, contours_size_3)
buff_size_LE = '{} Meters'.format(buff_size_LE_value)
buff_LE = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_LE', buff_size_LE, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
buff_size_V = '0.3 Meters'
buff_V_01 = arcpy.Buffer_analysis(contours_V, 'tmp_buff_V_01', buff_size_V, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
buff_V = arcpy.Erase_analysis (buff_V_01, left_buffer, 'tmp_buff_V')

buff_LE_V_merge = arcpy.Merge_management ([buff_LE, buff_V], 'tmp_buff_LE_V_merge')
buff_LE_V_merge_diss = arcpy.Dissolve_management (buff_LE_V_merge, 'tmp_buff_LE_V_merge_diss')
buff_LE_V_merge_diss_lyr = arcpy.MakeFeatureLayer_management (buff_LE_V_merge_diss, 'tmp_buff_LE_V_merge_diss_lyr')
buff_LE_V_merge_diss_line = arcpy.PolygonToLine_management (buff_LE_V_merge_diss_lyr, 'tmp_buff_LE_V_merge_diss_line')

buff_size_cca = '0.1 Meters'
erase_mask = arcpy.Buffer_analysis(buff_LE_V_merge_diss_line, 'tmp_erase_mask', buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
rocks_contours_lyr = arcpy.MakeFeatureLayer_management (rocks_contours, 'tmp_rocks_contours_lyr')
rocks_contours_line = arcpy.PolygonToLine_management (rocks_contours_lyr, 'tmp_rocks_contours_line')
# prvotni zakldni linie
basic_line_01 = arcpy.Erase_analysis(rocks_contours_line, erase_mask, 'tmp_basic_line_01')

'''
# odmazani problematickych zakonceni
# nutne kvuli pripadum dolnich hran v okoli puklin, kdy se vytvorena maska kolem puklin nedotyka dolnich hran na jejich
    # uplnem konci, ale kousek od neho a potom tedy nejsou odmazany bocni steny bufferu zakladni kontury
#buff_size_LE_2 = '0,9 Meters' # promenlive podle meritka!!! # musi byt mensi nez promenna buff_size_LE (staci aby to bylo vetsi nez sirka kontury
                                # u jineho nastaveni promenne buff_size_LE by mozna nemuselo byt
buff_size_LE_2_value = 0.6 + my_utils.calculate_real_size(map_scale, contours_size_3)
buff_size_LE_2 = '{} Meters'.format(buff_size_LE_2_value)
buff_LE_2 = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_LE_2', buff_size_LE_2, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
arcpy.Merge_management ([buff_LE_2, buff_V ], 'tmp_merge_V_LE_2')
erase_mask_2_buff = arcpy.Dissolve_management ('tmp_merge_V_LE_2', 'tmp_erase_mask_2_buff')
erase_mask_2_line = arcpy.PolygonToLine_management (erase_mask_2_buff, 'tmp_erase_mask_2_line')
erase_mask_2 = arcpy.Buffer_analysis(erase_mask_2_line , 'tmp_erase_mask_2', buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
basic_line_02 = arcpy.Erase_analysis (basic_line_01, erase_mask_2, 'tmp_basic_line_02')
'''
# slouceni pripadnych multipart 'basic_line'
    # 'basic_lines' jsou vytvoreny z bufferu/polygonu - nekdy tedy dochazi k tomu, ze je jedna linie tvorena vice prvky
    # je tedy potreba vrstvu rozdelit a opet spojit podle prislusneho id linie
# overit, jestli neni atribut id_basic line_uplne zbytecnej
arcpy.MultipartToSinglepart_management (basic_line_01, 'tmp_basic_line_01_singlepart')
arcpy.MakeFeatureLayer_management('tmp_basic_line_01_singlepart', 'singlepart_lyr')
# odstraneni 'basic_lines', ktere jsou mensi nez 1 metr - vznikly pravdepodobne geometrickymi neprestnostmi a dela to neplechu
arcpy.SelectLayerByAttribute_management ('singlepart_lyr', '', "Shape_Length > 1")
basic_line = arcpy.Dissolve_management ('singlepart_lyr', 'basic_line', 'ORIG_FID','','SINGLE_PART')

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
#basic_lines_list_select = basic_lines_list[1:4]


for id in basic_lines_list: #_select:# smazat
    print('id', id)
    whereID = '"OBJECTID" = {}'.format(id) #(basic_lines_list[id])
    one_bl = arcpy.MakeFeatureLayer_management(basic_line, 'one_bl_lyr', whereID)

    # nastavit pocatecni hodnoty gap/cheek
    gap_value = parameters.gap_value
    gap_value = my_utils.calculate_real_size(map_scale, gap_value)
    gap = '{} Meters'.format(gap_value)
    cheek_value = 0.2 + gap_value # parameters.
    cheek = '{} Meters'.format(cheek_value)
    count_cl = int(maximal_width_of_wall / gap_value)

    id_order = 1
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
            arcpy.CalculateField_management(tc, 'id_order', id_order)
            arcpy.Append_management(tc, tvar_cary)

            gap_value = (gap_value + addition_value) * multiple
            gap = "{} Meters".format(gap_value)
            cheek_value = (cheek_value + addition_value) * multiple
            cheek = "{} Meters".format(cheek_value)

            id_order = id_order + 1

    except Exception as inst:
        print('chyba',id)

    arcpy.Delete_management(one_bl)




## VYPOCET TLOUSTKY TVAROVYCH CAR
# list "poctu/poradi" tvarovych car
order_list = []
for i in range(1, count_cl +1):
    order_list.append(i)

# list hodnot tloustek jednotlivych linii
add = (float(max_line_width) - float(min_line_width)) / float(count_cl - 1)
size_list = []
size_list.append(min_line_width)
s = 1
for j in range(1, (count_cl - 1)):
    value = min_line_width + s * add
    size_list.append(value)
    s = s + 1
size_list.append(max_line_width)
# seradi hodnooty v listu obracene (od nejvetsiho k nejmensimu)
size_list = size_list[::-1]

# list listu [[poradi, tloustka], [], ...]
complet_list = []
for i in range(0, count_cl):
    item = []
    item.append(order_list[i])
    item.append(size_list[i])
    complet_list.append(item)
print('complet_list',complet_list)

# prirazeni tloustky linie tvarove cary
arcpy.AddField_management(tvar_cary, 'cl_size', 'DOUBLE')
u_cur = arcpy.da.UpdateCursor(tvar_cary, ['id_order', 'cl_size'])
for row in u_cur:
    order = row[0]
    print('order',order)
    row[1] = complet_list[order - 1][1]
    u_cur.updateRow(row)
del u_cur

# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)


end = time.time()
print 'time', end-start
