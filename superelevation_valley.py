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
output_LE = parameters.output_LE

# vstupni parametry
map_scale = parameters.map_scale
point_buffer_size = parameters.point_buffer_size
segmentation_size_valley = parameters.segmentation_size_valley
print("size_map", segmentation_size_valley)
segmentation_size_valley = my_utils.calculate_real_size(map_scale, segmentation_size_valley)
print("size_real", segmentation_size_valley)
minimum_wall_height = parameters.minimum_wall_height


# vystupni vrstvy
output_V = parameters.output_V
if arcpy.Exists (output_V):
	arcpy.Delete_management (output_V)


"UDOLNICE SE DOTYKAJI DOLNI HRANY"
"---------------PRIDANO-----------------"
valley_lyr = arcpy.MakeFeatureLayer_management (valley, 'valley_lyr')
arcpy.SelectLayerByLocation_management (valley_lyr, 'BOUNDARY_TOUCHES',output_LE)
valley_boundary_touches = arcpy.CopyFeatures_management(valley_lyr, 'tmp_valley_boundary_touches')
"---"

# prvni body udolnic - pruseciky udolnice a dolni hrany
first_points = my_utils.create_first_point_on_line(valley_boundary_touches)

# vypocet maximalni hodnoty prevyseni pro udolnici (v miste dotyku dolni hrany)
arcpy.AddField_management (first_points, 'max_superelev', 'DOUBLE')
u_cursor = arcpy.da.UpdateCursor(first_points, ['max_superelev'])
i = 1
for row in u_cursor:
    whereID = '"OBJECTID" = {}'.format(i)
    arcpy.MakeFeatureLayer_management(first_points, 'tmp_point_lyr', whereID)
    arcpy.Buffer_analysis('tmp_point_lyr', 'tmp_point_lyr_buff', point_buffer_size, 'FULL', 'ROUND','ALL', '', 'PLANAR')
    zone = arcpy.Clip_analysis(output_LE,'tmp_point_lyr_buff','tmp_superelevation_lower_edges_clip','')

    # vytvoreni/naplneni listu hodnot prevyseni a delek
    superelevation = my_utils.create_list_of_values(zone, 'superelevation')
    length = my_utils.create_list_of_values(zone, 'Shape_Length')

    # vazeny prumer (hodnota prevyseni vzhledem k delce linie v urcenem okoli bodu)
    max_c = [length[j] * superelevation[j] for j in range(0,len(superelevation))]
    try:
        maximum = sum(max_c) / sum(length)
    except ZeroDivisionError:
        maximum = 0
    row[0] = maximum
    u_cursor.updateRow(row)
    i = i + 1
del u_cursor

# seznam maximalnich hodnot prevyseni pro jednotlive linie udolnic
valley_max_superelev = my_utils.create_list_of_values(first_points, 'max_superelev')

# priprava/vytvoreni vystupni vrstvy
sr = arcpy.Describe(valley).spatialReference
output_1 = arcpy.CreateFeatureclass_management(workspace,'tmp_output_1', 'POLYLINE', '', '', '', sr)
arcpy.AddField_management (output_1, 'superelevation', 'DOUBLE')
arcpy.AddField_management (output_1, 'id_line', 'SHORT')

## pro kazdou udolnici se provede segmentace a nasledne se urci/interpoluje hodnota prevyseni pro jednotlive segmenty
# tyto udaje/hodnty se importuju do (vyse) vytvorene vystupni fc
id_list = my_utils.create_list_of_values(valley_boundary_touches, 'OBJECTID' )
# asi si nakonec vystacim s jednim indexem
idv = 0 # index pro nacitani jednotlivych prvku dle id (idv = id_valley)
vms = 0 # index pro hledani v listech (vms = valley_max_superelev)
s_cursor = arcpy.da.SearchCursor(valley_boundary_touches, ['Shape@', 'OBJECTID'])
for row in s_cursor:
    shape = row[0]
    id_line = row[1]
    array_points = shape.getPart()
    line = arcpy.Polyline(array_points)

    # urceni poctu segmentu (segments_count)
    whereID = '"OBJECTID" = {}'.format(id_list[idv])
    arcpy.MakeFeatureLayer_management(valley_boundary_touches, 'tmp_one_valley', whereID)
    s_cur = arcpy.da.SearchCursor('tmp_one_valley',['Shape_Length'])
    for i in s_cur:
        lenght = i[0]
        print("lenght", lenght)
        # je to ok?
        segments_count = int(round(lenght / segmentation_size_valley))
        print("round", round(lenght / segmentation_size_valley))
        print("int",segments_count)
    del s_cur

    ## vypocet prevyseni - tvorba listu pro jednotlive segmenty
    # nasledne jsou konkretni hodnoty prirazeny prostrednictvim indexu
    if segments_count == 0 or segments_count == 1 :
        addition_list = [valley_max_superelev[vms]]
    else:
        maximum = valley_max_superelev[vms]
        minimum = minimum_wall_height
        addition = float((maximum - minimum) / (segments_count - 1))
        s = 1 # indexovani poradi segmentu
        addition_list = []
        addition_list.append(maximum)  # nacte maximum "k prvnimu prvku"
        # for cyklus prirazuje hodnoty od druheho po predposledni prvek,
        # protoze okrajovym prvkum je prirazeno minimum a maximum
        for j in range(1, (segments_count - 1)):
            value = maximum - s * addition
            addition_list.append(value)
            s = s + 1
        addition_list.append(minimum)  # nacte minimum "k poslednimu prvku"

    # naplneni vystupni vrstvy daty - vlozeni geometrie, id objektu a prevyseni
    i_cur = arcpy.da.InsertCursor(output_1, ['Shape@', 'OBJECTID', 'id_line', 'superelevation'])
    al = 0 # indexovani v additon_list
    for k in range(0,segments_count):
        segment = line.segmentAlongLine(k/float(segments_count), ((k+1)/float(segments_count)), True)
        i_cur.insertRow([segment, idv, id_line, addition_list[al]])
        al = al + 1
    del i_cur

    idv = idv + 1
    vms = vms + 1
del s_cursor
print("first_part_done")

"UDOLNICE NAVAZUJE NA UDOLNICI"
valley_lyr = arcpy.MakeFeatureLayer_management (valley, 'valley_lyr')
arcpy.SelectLayerByLocation_management (valley_lyr, 'CROSSED_BY_THE_OUTLINE_OF', output_1)#valley_boundary_touches)
valley_cross_valley = arcpy.CopyFeatures_management(valley_lyr, 'tmp_valley_cross_valley')
print("done")

# zkouska, jesti vrstva obsahuje nejake prevky
test_list = []
s_cur = arcpy.da.SearchCursor(valley_cross_valley, ["OBJECTID"])
for row in s_cur:
    test_list.append(row[0])
print(len(test_list))

if len(test_list) > 0:
    arcpy.AddField_management (valley_cross_valley, 'id_line', 'SHORT')
    u_cur = arcpy.da.UpdateCursor(valley_cross_valley, ['OBJECTID','id_line'])
    for row in u_cur:
        value = 9000 + row[0]
        row[1] = value
        u_cur.updateRow(row)
    del u_cur

    valley_intersection = arcpy.Intersect_analysis ([valley_boundary_touches, valley_cross_valley], 'tmp_valley_intersection', '', '', 'POINT')

    output_2 = arcpy.SplitLineAtPoint_management (valley_cross_valley, valley_intersection, 'tmp_valley_cross_valley_splited')
    arcpy.AddField_management (output_2, 'superelevation', 'DOUBLE')

    first_points_2 = my_utils.create_first_point_on_line(output_2)
    arcpy.CopyFeatures_management(first_points_2, 'tmp_first_points_2')

    # vyberu segmenty jiz vypocitanych udolnic, ktere protinaji dalsi udolnice
    lyr = arcpy.MakeFeatureLayer_management (output_1, 'valley_superelev_segment_lyr')
    arcpy.SelectLayerByLocation_management (lyr, 'CROSSED_BY_THE_OUTLINE_OF', valley_cross_valley)#valley_boundary_touches)
    valley_superelev_segment_selected = arcpy.CopyFeatures_management(lyr, 'tmp_valley_superelev_segment_selected')

    # vytvorim seznam ID prvku z predesleho kroku
    #id_superelev_segment = my_utils.create_list_of_values(valley_superelev_segment_selected,'OBJECTID')

    #my_utils.create_list_of_values(valley_superelev_segment_selected,'OBJECTID')



    u_cursor = arcpy.da.UpdateCursor(output_2, ['OBJECTID','superelevation'])
    for row in u_cursor:
        id = row[0]

        # vytvorim vrstvu jednoho prvku, kteremu chci priradit prevyseni
        whereID = '"OBJECTID" = {}'.format(id)
        one = arcpy.MakeFeatureLayer_management(output_2, 'one_valley_cross_valley_splited', whereID)
        valley_superelev_segment_selected_lyr = arcpy.MakeFeatureLayer_management(valley_superelev_segment_selected, 'valley_superelev_segment_selected_lyr')

        # vyberu prvek, ktery protina prvek, kteremu chci priradit prevyseni
        arcpy.SelectLayerByLocation_management(valley_superelev_segment_selected_lyr, 'BOUNDARY_TOUCHES', one)
        one_segment = arcpy.CopyFeatures_management(valley_superelev_segment_selected_lyr, 'tmp_one_valley_superelev_segment_selected')

        s_cur = arcpy.da.SearchCursor(one_segment, ['superelevation'])
        superelev_list = []
        for ite in s_cur:
            superelev_list.append(ite[0])
        # ziskam prumernou hodnotu
        try:
            superelev_value = sum(superelev_list)/len(superelev_list)
        except ZeroDivisionError:
            superelev_value = 0

        row[1] = superelev_value
        u_cursor.updateRow(row)
    del u_cursor


    arcpy.Merge_management ([output_1,output_2], output_V)

else:
    arcpy.Copy_management(output_1, output_V)






# "zaverecny uklid"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)

end = time.time()

print 'time', end-start