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
valley = parameters.valley
size_percent = 5
minimum_wall_height = 0.2
maximum_wall_height = 5 # muze byt fixni??? -- pozor, tenhle nazev uz tam mam
left_buffer = parameters.left_LE_buffer_to_erase
in_wall = parameters.in_wall
contour_line = parameters.output_CL
rock_contours = parameters.output_RC

# outputs
mask_2 = 'mask'
tc_final = 'tmp_tvarove_cary_orez_rc'




### ODMASKOVANI PUKLIN/UDOLNIC
# priprava/vytvoreni vystupni vrstvy
sr = arcpy.Describe(valley).spatialReference
mask_segments = arcpy.CreateFeatureclass_management(workspace, 'tmp_mask_segments', 'POLYLINE', '', '', '', sr)
arcpy.AddField_management (mask_segments, 'size_buff', 'DOUBLE')
arcpy.AddField_management (mask_segments, 'id_line', 'SHORT')

## pro kazdou udolnici se provede segmentace a nasledne se urci/interpoluje hodnota bufferu pro jednotlive segmenty
# tyto udaje/hodnty se importuju do (vyse) vytvorene vystupni fc
s_cursor = arcpy.da.SearchCursor(valley, ['Shape@', 'OBJECTID'])
for row in s_cursor:
    shape = row[0]
    id_line = row[1]
    array_points = shape.getPart()
    line = arcpy.Polyline(array_points)

    # urceni poctu segmentu (segments_count)
    segments_count = 100 / size_percent

    ## vypocet sirky/tloustky bufferu - tvorba listu pro jednotlive segmenty
    # nasledne jsou konkretni hodnoty prirazeny prostrednictvim indexu
    maximum = maximum_wall_height
    minimum = minimum_wall_height
    addition = float((maximum - minimum) / (segments_count - 1))#musim pracovat s desetinnym cislem
    #addition = round(addition, 6) #(nevim, kolik des.mist ma "double")
    s = 1 # indexovani poradi segmentu
    addition_list = []
    addition_list.append(maximum)  # nacte maximum "k prvnimu prvku"
    # for cyklus prirazuje hodnoty od druheho po predposledni prvek,
    # protoze okrajovym prvkum je prirazeno minimum a maximum
    for i in range(1, (segments_count - 1)):
        value = maximum - s * addition
        addition_list.append(value)
        s = s + 1
    addition_list.append(minimum)  # nacte minimum "k poslednimu prvku"

    # naplneni vystupni vrstvy daty - vlozeni geometrie, id objektu a veliksoti bufferu
    i_cur = arcpy.da.InsertCursor(mask_segments, ['Shape@', 'id_line', 'size_buff'])
    al = 0 # indexovani v additon_list
    for k in range(0,segments_count):
        segment = line.segmentAlongLine(k/float(segments_count), ((k+1)/float(segments_count)), True)
        i_cur.insertRow([segment, id_line, addition_list[al]])
        al = al + 1
    del i_cur
del s_cursor


## vytvoreni bufferu/kuzelu
arcpy.GraphicBuffer_analysis(mask_segments, 'tmp_GB_butt_mitter','size_buff', 'BUTT', 'MITER', '10','')

diss = arcpy.Dissolve_management('tmp_GB_butt_mitter', 'tmp_diss', 'id_line')

## potreba udelat "bevel buffer", abychom u nejtenciho konce dostali jeden bod a pozdeji tak mohl vzniknout tvar "kuzele"
# kladny buffer pro shlazeni (positive)
arcpy.GraphicBuffer_analysis(diss, 'tmp_diss_GB_bevel_p','2 Meters', 'SQUARE', 'BEVEL', '10','')
# zaporny buffer pro shlazeni (negative)
arcpy.GraphicBuffer_analysis('tmp_diss_GB_bevel_p', 'tmp_diss_GB_bevel_n','-1,5 Meters', 'SQUARE', 'BEVEL', '10','')
# zjednoduseni tvaru
simplify = arcpy.SimplifyPolygon_cartography('tmp_diss_GB_bevel_n', 'tmp_simplify', 'POINT_REMOVE', '0,5 Meters', '', '', 'NO_KEEP', '')

# odmazani kuzelu presahujicih pres dolni hranu
arcpy.Erase_analysis (simplify, left_buffer, 'tmp_simplify_erase')
arcpy.MultipartToSinglepart_management ('tmp_simplify_erase', 'tmp_multipart')
arcpy.MakeFeatureLayer_management('tmp_multipart', 'multipart_lyr')
arcpy.SelectLayerByAttribute_management('multipart_lyr', 'NEW_SELECTION', ' "Shape_Area" > 50 ')
mask_valley = arcpy.CopyFeatures_management('multipart_lyr', 'tmp_mask_valley')

### MASKA CELEK
arcpy.Merge_management ([in_wall, mask_valley], 'tmp_merge')
# vrstva pro odmaskovani kresby skal
mask_to_erase = arcpy.Dissolve_management ('tmp_merge', 'tmp_mask_to_erase')
# vrstva pro odmaskovani okolni kresby
mask_gap_value = 1.5
mask_gap = '{} Meters'.format(mask_gap_value)
arcpy.Buffer_analysis(mask_to_erase, mask_2, mask_gap, 'FULL', 'ROUND', 'ALL', '', 'PLANAR')

### ODMASKOVANI CELEK
arcpy.Intersect_analysis ([contour_line, mask_to_erase], tc_final)
arcpy.Erase_analysis(tc_final, rock_contours, 'finito')

'''
# zaverecny uklid
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)
'''
end = time.time()

print 'time', end-start