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

# vstupni parametry
map_scale = parameters.map_scale
point_buffer_size = parameters.point_buffer_size
segmentation_size_valley = parameters.segmentation_size_valley
segmentation_size_valley = my_utils.calculate_real_size(map_scale, segmentation_size_valley)
minimum_wall_height = parameters.minimum_wall_height

# vystupni vrstvy
output_V = parameters.output_V
if arcpy.Exists (output_V):
	arcpy.Delete_management (output_V)

# prvni body udolnic - pruseciky udolnice a dolni hrany
first_points = my_utils.create_first_point_on_line(valley)

# vypocet maximalni hodnoty prevyseni pro udolnici (v miste dotyku dolni hrany)
arcpy.AddField_management (first_points, 'max_superelev', 'DOUBLE')
u_cursor = arcpy.da.UpdateCursor(first_points, ['max_superelev'])
i = 1
for row in u_cursor:
    whereID = '"OBJECTID" = {}'.format(i)
    arcpy.MakeFeatureLayer_management(first_points, 'tmp_point_lyr', whereID)
    arcpy.Buffer_analysis('tmp_point_lyr', 'tmp_point_lyr_buff', point_buffer_size, 'FULL', 'ROUND','ALL', '', 'PLANAR')
    zone = arcpy.Clip_analysis('superelevation_lower_edges','tmp_point_lyr_buff','tmp_superelevation_lower_edges_clip','')

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
arcpy.CreateFeatureclass_management(workspace, output_V, 'POLYLINE', '', '', '', sr)
arcpy.AddField_management (output_V, 'superelevation', 'DOUBLE')
arcpy.AddField_management (output_V, 'id_line', 'SHORT')

## pro kazdou udolnici se provede segmentace a nasledne se urci/interpoluje hodnota prevyseni pro jednotlive segmenty
# tyto udaje/hodnty se importuju do (vyse) vytvorene vystupni fc
idv = 1 # index pro nacitani jednotlivych prvku dle id (idv = id_valley)
vms = 0 # index pro hledani v listech (vms = valley_max_superelev)
s_cursor = arcpy.da.SearchCursor(valley, ['Shape@', 'OBJECTID'])
for row in s_cursor:
    shape = row[0]
    id_line = row[1]
    array_points = shape.getPart()
    line = arcpy.Polyline(array_points)

    # urceni poctu segmentu (segments_count)
    whereID = '"OBJECTID" = {}'.format(idv)
    arcpy.MakeFeatureLayer_management(valley, 'tmp_one_valley', whereID)
    s_cur = arcpy.da.SearchCursor('tmp_one_valley',['Shape_Length'])
    for i in s_cur:
        lenght = i[0]
        try:
            segments_count = int(round(lenght / segmentation_size_valley))
        except ZeroDivisionError:
            segments_count = int(lenght)
    del s_cur

    ## vypocet prevyseni - tvorba listu pro jednotlive segmenty
    # nasledne jsou konkretni hodnoty prirazeny prostrednictvim indexu
    maximum = valley_max_superelev[vms]
    minimum = minimum_wall_height
    addition = (maximum - minimum) / (segments_count - 1)
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
    i_cur = arcpy.da.InsertCursor(output_V, ['Shape@', 'OBJECTID', 'id_line', 'superelevation'])
    al = 0 # indexovani v additon_list
    for k in range(0,segments_count):
        segment = line.segmentAlongLine(k/float(segments_count), ((k+1)/float(segments_count)), True)
        i_cur.insertRow([segment, idv, id_line, addition_list[al]])
        al = al + 1
    del i_cur

    idv = idv + 1
    vms = vms + 1
del s_cursor

'''
# "zaverecny uklid"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)
'''
end = time.time()

print 'time', end-start