import arcpy
#import parameters
import my_utils
#import utils
import sys

start = time.time()

#Check the Spatial extension
arcpy.CheckOutExtension('Spatial')

arcpy.env.overwriteOutput = 1
arcpy.env.workspace = '.\\utery.gdb'
workspace = arcpy.env.workspace

# OPRAVA/SLOUCENI BASIC LINE

# inputs
lower_edges = 'superelevation_lower_edges'
contours_V = 'contours_V'
rocks_contours = 'rocks_contours_500'
left_buffer = 'left_buff'


## vytvoreni zakladni linie, podle ktere se budou kreslit tvarove cary
buff_size_LE = '3,4 Meters' # promenlive podle meritka!!!
buff_LE = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_LE', buff_size_LE, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
buff_size_V = '0,5 Meters' # promenlive podle meritka!!!
buff_V_01 = arcpy.Buffer_analysis(contours_V, 'tmp_buff_V_01', buff_size_V, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
buff_V = arcpy.Erase_analysis (buff_V_01, left_buffer, 'tmp_buff_V')

buff_LE_V_merge = arcpy.Merge_management ([buff_LE, buff_V], 'tmp_buff_LE_V_merge')
buff_LE_V_merge_diss = arcpy.Dissolve_management (buff_LE_V_merge, 'tmp_buff_LE_V_merge_diss')
buff_LE_V_merge_diss_lyr = arcpy.MakeFeatureLayer_management (buff_LE_V_merge_diss, 'tmp_buff_LE_V_merge_diss_lyr')
buff_LE_V_merge_diss_line = arcpy.PolygonToLine_management (buff_LE_V_merge_diss_lyr, 'tmp_buff_LE_V_merge_diss_line')

buff_size_cca = '0,1 Meters' # kdyz zmenim hodnotu, tak error a skript spadne
erase_mask = arcpy.Buffer_analysis(buff_LE_V_merge_diss_line, 'tmp_erase_mask', buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
rocks_contours_lyr = arcpy.MakeFeatureLayer_management (rocks_contours, 'tmp_rocks_contours_lyr')
rocks_contours_line = arcpy.PolygonToLine_management (rocks_contours_lyr, 'tmp_rocks_contours_line')
# prvotni zakldni linie
basic_line_01 = arcpy.Erase_analysis(rocks_contours_line, erase_mask, 'tmp_basic_line_01')

# odmazani problematickych zakonceni
# nutne kvuli pripadum dolnich hran v okoli puklin, kdy se vytvorena maska kolem puklin nedotyka dolnich hran na jejich
    # uplnem konci, ale kousek od neho a potom tedy nejsou odmazany bocni steny bufferu zakladni kontury
buff_size_LE_2 = '0,9 Meters' # promenlive podle meritka!!! # musi byt mensi nez promenna buff_size_LE (staci aby to bylo vetsi nez sirka kontury
                                # u jineho nastaveni promenne buff_size_LE by mozna nemuselo byt
buff_LE_2 = arcpy.Buffer_analysis(lower_edges, 'tmp_buff_LE_2', buff_size_LE_2, 'RIGHT', 'FLAT', 'ALL', '', 'PLANAR')
arcpy.Merge_management ([buff_LE_2, buff_V ], 'tmp_merge_V_LE_2')
erase_mask_2_buff = arcpy.Dissolve_management ('tmp_merge_V_LE_2', 'tmp_erase_mask_2_buff')
erase_mask_2_line = arcpy.PolygonToLine_management (erase_mask_2_buff, 'tmp_erase_mask_2_line')
erase_mask_2 = arcpy.Buffer_analysis(erase_mask_2_line , 'tmp_erase_mask_2', buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
basic_line_02 = arcpy.Erase_analysis (basic_line_01, erase_mask_2, 'tmp_basic_line_02')

# slouceni pripadnych multipart 'basic_line'
    # 'basic_lines' jsou vytvoreny z bufferu/polygonu - nekdy tedy dochazi k tomu, ze je jedna linie tvorena vice prvky
    # je tedy potreba vrstvu rozdelit a opet spojit podle prislusneho id linie
arcpy.AddField_management (basic_line_02, 'id_bl', "SHORT")
u_cursor = arcpy.da.UpdateCursor(basic_line_02, ['OBJECTID','id_bl'])
for row in u_cursor:
    id = row[0]
    row[1]= id
    u_cursor.updateRow(row)
del u_cursor
arcpy.MultipartToSinglepart_management (basic_line_02, 'tmp_basic_line_02_singlepart')
arcpy.MakeFeatureLayer_management('tmp_basic_line_02_singlepart', 'singlepart_lyr')
# odstraneni 'basic_lines', ktere jsou mensi nez 1 metr - vznikly pravdepodobne geometrickymi neprestnostmi a dela to neplechu
arcpy.SelectLayerByAttribute_management ('singlepart_lyr', '', "Shape_Length > 1")
basic_line = arcpy.Dissolve_management ('singlepart_lyr', 'basic_line_3', 'id_bl')


## VYTVORENI VZOROVYCH VRSTEV tvaroveych car a bufferuu
gap_value = 0.5 # v metrech
gap = "{} Meters".format(gap_value)
cheek_value = 0.7 # v metrech
cheek = "{} Meters".format(cheek_value)
maximal_width_of_wall = 4 # v metrech - duplicitne jeste jendou niz
count_tc = int(maximal_width_of_wall / gap_value)

addition_value = 0.5 #gap_value
nasobek = 1.2 # prejmenovat to ang

# vytvoreni vrstvy, do ktere se budou vkladat jednotlive tc/buffery (buffers, tvar_cary)
arcpy.MakeFeatureLayer_management(basic_line, 'model_bl_lyr', '"OBJECTID" = 1')
buffers = arcpy.Buffer_analysis('model_bl_lyr', 'buffers_5m', gap, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
arcpy.PolygonToLine_management(buffers, 'tmp_buffers_line')
arcpy.Buffer_analysis('model_bl_lyr', 'tmp_buffers_to_erase', cheek, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
arcpy.PolygonToLine_management('tmp_buffers_to_erase', 'tmp_buffers_to_erase_line')
tvar_cary = arcpy.Erase_analysis('tmp_buffers_line', 'tmp_buffers_to_erase_line', 'cary_mary_5m')
arcpy.DeleteFeatures_management (buffers)
arcpy.DeleteFeatures_management (tvar_cary)
arcpy.AddField_management(buffers, 'id_tc', 'SHORT')
arcpy.AddField_management(tvar_cary, 'id_tc', 'SHORT')

## VYTVORENI TC A BUFFERU
basic_lines_list = my_utils.create_list_of_values(basic_line, 'OBJECTID')
# print(basic_lines_list)
#basic_lines_list_select = basic_lines_list[16:21]

# id = 1
for bl in basic_lines_list: #_select:
    #print('id',basic_lines_list[id])
    print('bl', bl)
    whereID = '"OBJECTID" = {}'.format(bl) #(basic_lines_list[id])
    one_bl = arcpy.MakeFeatureLayer_management(basic_line, 'one_bl_lyr', whereID)
    # arcpy.CopyFeatures_management('one_bl_lyr', 'tmp_one_bl')

    # nstavit pocatecni hodnoty gap/cheek
    gap_value = 0.5  # v metrech
    gap = "{} Meters".format(gap_value)
    cheek_value = 0.7  # v metrech
    cheek = "{} Meters".format(cheek_value)
    maximal_width_of_wall = 4  # v metrech  - duplicitne jeste jendou vys
    count_tc = int(maximal_width_of_wall / gap_value)

    try:
        for i in range(1, (count_tc + 1)):
            # print('i', i)
            # buffer pro tvorbu TC
            one_buff = arcpy.Buffer_analysis(one_bl, 'tmp_buff', gap, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')
            buff_line = arcpy.PolygonToLine_management('tmp_buff', 'tmp_buff_line')
            # buffer na odmazani bocnic
            chyba = arcpy.Buffer_analysis(one_bl, 'tmp_buff_to_erase', cheek, 'LEFT', 'FLAT', 'ALL', '', 'PLANAR')

            buff_to_erase_line = arcpy.PolygonToLine_management('tmp_buff_to_erase', 'tmp_buff_to_erase_line')
            buff_to_erase_line_mask = arcpy.Buffer_analysis(buff_to_erase_line, 'tmp_buff_to_erase_line_mask',
                                                            buff_size_cca, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')
            # odmazani
            tc = arcpy.Erase_analysis(buff_line, buff_to_erase_line_mask, 'tmp_tc')
            arcpy.AddField_management(tc, 'id_tc', 'SHORT')
            arcpy.CalculateField_management(tc, 'id_tc', bl)
            arcpy.Append_management(tc, tvar_cary)
            # sem to i u 17 probehne bez problemu

            gap_value = (gap_value + addition_value) * nasobek
            gap = "{} Meters".format(gap_value)
            cheek_value = (cheek_value + addition_value) * nasobek
            cheek = "{} Meters".format(cheek_value)

            if i == count_tc:
                arcpy.AddField_management(one_buff, 'id_tc', 'SHORT')
                arcpy.CalculateField_management(one_buff, 'id_tc', bl)
                arcpy.Append_management(one_buff, buffers)
    except Exception as inst:
        print('chyba',inst)
        print(type(inst))

    arcpy.Delete_management(one_bl)


# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)


end = time.time()
print 'time', end-start
