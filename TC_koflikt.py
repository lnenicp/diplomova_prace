import arcpy
import parameters
import my_utils
#import utils

# import decimal
start = time.time()
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = 1

# nastaveni pracovni databaze
work_dtb = parameters.work_dtb
arcpy.env.workspace = '.\\{}.gdb'.format(work_dtb)
workspace = arcpy.env.workspace

# inputs
cont_line = parameters.cl_output_01
basic_line = parameters.basic_line_name

# parameters
map_scale = parameters.map_scale
erase_size_value = parameters.erase_size_value
erase_size = my_utils.calculate_real_size(map_scale, erase_size_value)

# output
cl_output = parameters.cl_output


# priprava pruseciku tvarovych car
points_int = arcpy.Intersect_analysis(cont_line, 'tmp_intersect', 'ALL', '', 'POINT')
points_single = arcpy.MultipartToSinglepart_management (points_int, 'tmp_points_single')

near = arcpy.GenerateNearTable_analysis(points_single, basic_line, 'tmp_near_table')

arcpy.JoinField_management (points_single, 'OBJECTID', near, 'IN_FID')
arcpy.JoinField_management (points_single, 'NEAR_FID', basic_line, 'OBJECTID')
points = arcpy.CopyFeatures_management (points_single, 'tmp_points')

# predpriprava linii - vrsva cont_line/finito se sklada z "miniusecek"
cont_line_single = arcpy.Dissolve_management(cont_line, 'tmp_cont_line_single', 'id_tc','', 'SINGLE_PART', 'DISSOLVE_LINES')
cont_line_ok = arcpy.SpatialJoin_analysis(cont_line_single, cont_line, 'tmp_cont_line_ok', 'JOIN_ONE_TO_ONE', '', '',
                           'SHARE_A_LINE_SEGMENT_WITH', '', '')
arcpy.MakeFeatureLayer_management (cont_line_ok, 'cont_line_lyr')
arcpy.SelectLayerByLocation_management ('cont_line_lyr', 'INTERSECT', points)
cont_line_int = arcpy.CopyFeatures_management('cont_line_lyr', 'tmp_cont_line_int')


# budu pouzivat pro vyber v s_cur
points_lyr = arcpy.MakeFeatureLayer_management (points, 'points_lyr')

# priprava vystupni vrstvy
sr = arcpy.Describe(cont_line).spatialReference
cl_conflict = arcpy.CreateFeatureclass_management(workspace, 'cl_conflict', 'POLYLINE', '', '', '', sr)
arcpy.AddField_management(cl_conflict, 'id_tc', 'SHORT')
arcpy.AddField_management(cl_conflict, 'cl_size', 'DOUBLE')


s_cursor = arcpy.da.SearchCursor(cont_line_int, ['Shape@','OBJECTID', 'id_tc', 'cl_size'])
for row in s_cursor:
    shapeline = row[0]
    id = row[1]
    print('id', id)
    id_tc = row[2]
    cl_size = row[3]

    # vyberu jednu linii (podle id)
    whereID = '"OBJECTID" = {}'.format(id)
    cont_line_one = arcpy.MakeFeatureLayer_management(cont_line_int, 'cont_line_one_lyr', whereID)

        ##arcpy.CopyFeatures_management(cont_line_one, 'tmp_cont_line_one')

    # vyberu body, ktere protinaji konkretni linii
    arcpy.SelectLayerByLocation_management(points_lyr, 'INTERSECT', cont_line_one)
    points_intersect = arcpy.CopyFeatures_management(points_lyr, 'tmp_points_intersect')

    # z vyse vybranych bodu vyberu pouze ty, jejich 'id_tc' je shodne s 'id_tc' linie
    points_intersect_lyr = arcpy.MakeFeatureLayer_management(points_intersect, 'points_intersect_lyr')
    arcpy.SelectLayerByAttribute_management(points_intersect_lyr, '','"id_tc" = {}'.format(id_tc))
    relevant_points = arcpy.CopyFeatures_management(points_intersect_lyr, 'tmp_relevant_points')
                        # arcpy.AddField_management(relevant_points, 'measure', 'DOUBLE')


    points_shape_list = []
    points_idbl_list = []
    id_point_list = []
    s_cur = arcpy.da.SearchCursor(relevant_points, ['Shape@', 'id_basic_line', 'OBJECTID']) # prepsat "id_jistota" smazat objectid
    for p in s_cur:
        points_shape_list.append(p[0])
        points_idbl_list.append(p[1])
        id_point_list.append(p[2])
    del s_cur
    print(points_shape_list)
    print(points_idbl_list)
    print(id_point_list)

    measure_list = []
    # vytvoreni koncoveho bodu pro nsazsi 'segmentAlongLine'
    endpoint_measure = []
    measure_cursor = arcpy.da.SearchCursor(cont_line_one, ['Shape@', 'Shape_Length'])
    for clo in measure_cursor:
        polyline = clo[0]
        length = clo[1]
        endpoint_measure.append(length)
        mi = 0
        for psl in points_shape_list:
            #print('prvek',id_point_list[mi])
            m = polyline.measureOnLine(points_shape_list[mi])
            #print('m', m)
            measure_list.append(m)
            mi = mi + 1
    del measure_cursor

    complet_list = []
    c = 0
    for i in range(len(points_idbl_list)):
        item = [points_idbl_list[c], measure_list[c], id_point_list[c]]
        complet_list.append(item)
        c = c + 1

    complet_list_sorted = sorted(complet_list, key=lambda x: x[1])

    # pridam nulu, aby se mi snadneji tvorili 'segmentAlongLine'
    complet_list_sorted.insert(0, [0, 0, 0])
    # umele vytvoreni posledniho bodu, na posledni misto v listu
    endpoint_measure_value = endpoint_measure[0]
    endpoint = [0, endpoint_measure_value, 0]
    complet_list_sorted.insert(len(complet_list_sorted), endpoint)
    print('complet_list_sorted', complet_list_sorted)

    # index = len(complet_list_sorted)- 2

    i_cursor = arcpy.da.InsertCursor(cl_conflict, ['Shape@', 'id_tc', 'cl_size'])
    i = 0 # indexovani mista s hodnotou "measure"/ indexovani v listech
    # pos = 1 # indexovani pozice bodu (jak jdou za sebou) - jdu az od 1, protoze na prvnim/nultem miste je umele dosazena nula
    for item in complet_list_sorted:
        aktual = i + 1
        previous = i
        next = i + 2
        penultimate = len(complet_list_sorted)- 2
        # pokud je id_bl shodne
        # pokud index dosahne hodnoty predposledniho prvku (posledni skutecny bod), a id_tc budou shodne, vznikne segment od posldniho skutecneho bodu ke konci linie
        if (i == penultimate and complet_list_sorted[penultimate][0] == id_tc):
            start = complet_list_sorted[previous][1]
            end = complet_list_sorted[aktual][1]
            line = shapeline.segmentAlongLine(start, end)
            i_cursor.insertRow([line, id_tc, cl_size])

        # pokud se prvni skutecny bod id_tc rovna (druhy prvek v listu)
        if (i == 0 and complet_list_sorted[aktual][0] == id_tc): # mozna dat do zavroky misto "i" - "jednicku"
            line = shapeline.segmentAlongLine(complet_list_sorted[previous][1], complet_list_sorted[aktual][1])
            i_cursor.insertRow([line, id_tc, cl_size])

        # pokud jsou shodne aktualni a i predesle id_tc s linii
        if ((i > 0 and i < penultimate)
                and (complet_list_sorted[aktual][0] == id_tc and complet_list_sorted[previous][0] == id_tc) ):
            line = shapeline.segmentAlongLine(complet_list_sorted[previous][1], complet_list_sorted[aktual][1])
            i_cursor.insertRow([line, id_tc, cl_size])

        ## sporne body na prechodech - "C"
        if ((i > 0 and i < penultimate)
                and (complet_list_sorted[aktual][0] <> id_tc and complet_list_sorted[previous][0] == id_tc) ):
            start = complet_list_sorted[previous][1]
            end = complet_list_sorted[aktual][1] - erase_size
            line = shapeline.segmentAlongLine(start, end)
            i_cursor.insertRow([line, id_tc, cl_size])

            ## sporne body na prechodech - "E"
        if ((i > 0 and i < penultimate)
                and (complet_list_sorted[aktual][0] == id_tc and complet_list_sorted[previous][0] <> id_tc)):
            start = complet_list_sorted[previous][1] + erase_size
            end = complet_list_sorted[aktual][1]
            line = shapeline.segmentAlongLine(start, end)
            i_cursor.insertRow([line, id_tc, cl_size])

        i = i + 1

    del i_cursor
del s_cursor


# nahrazeni problematickych casti a vytvoreni konecneho vystupu
cont_line_lyr = arcpy.MakeFeatureLayer_management (cont_line_ok, 'cont_line_lyr')
cont_line_all = arcpy.SelectLayerByAttribute_management (cont_line_lyr,'', '"OBJECTID" >= 1')
cont_line_selected = arcpy.SelectLayerByLocation_management (cont_line_all, 'INTERSECT', cont_line_int, '', 'REMOVE_FROM_SELECTION', '')
cl_no_conflict = arcpy.CopyFeatures_management (cont_line_selected, "tmp_cl_no_conflict")

cont_line_merge = arcpy.Merge_management ([cl_no_conflict, cl_conflict], "tmp_cont_line_merge")


cont_line_diss = arcpy.Dissolve_management(cont_line_merge, 'tmp_cont_line_diss', 'id_tc','', 'SINGLE_PART', 'DISSOLVE_LINES')
final_line = arcpy.SpatialJoin_analysis(cont_line_diss, cont_line_ok, cl_output, 'JOIN_ONE_TO_ONE','', '','SHARE_A_LINE_SEGMENT_WITH', '', '')

# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)


end = time.time()
print 'time', end-start