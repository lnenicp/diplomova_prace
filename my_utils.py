import arcpy
import os
import numpy

import parameters


arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = 1

work_dtb = parameters.work_dtb
arcpy.env.workspace = '.\\{}.gdb'.format(work_dtb)
workspace = arcpy.env.workspace

# tato funkce by mela nahradit funkci "calculate_contour_size"
def calculate_real_size (map_scale, size_in_map):
    '''
    Prepocita pozadovana velikost z mm v mape na m ve skutecnoti.
    :param map_scale: meritkove cislo mapy
    :param size_in_map: pozadovana velikost v mape (mm)
    :return: velikost/rozmer prvku ve skutecnosti
    '''
    size_in_real = size_in_map  * map_scale/1000
    return size_in_real


def create_segments(line_fc, segmentation_size):
    '''
    Rozdeli linie na segmenty o optimalni velikosti. Nebo-li vypocita delku segmentu tak,
    aby se co nejvice blizila zadane hodnote a zaroven byla linie rozdelena na stejne dlouhe segmenty.
    :param line_fc: vstupni liniova vrstva
    :param segmentation_size: pozadovana velikost segmentu
    :return: line_fc jednotlivych segmentu
    '''
    # priprava vystupni fc
    sr = arcpy.Describe(line_fc).spatialReference
    output_fc = arcpy.CreateFeatureclass_management(workspace, 'tmp_segments' , 'POLYLINE', '', '', '', sr)
    arcpy.AddField_management(output_fc, 'id_line', 'SHORT')

    s_cursor = arcpy.da.SearchCursor(line_fc, ['Shape@', 'Shape_Length', 'OBJECTID'])
    for row in s_cursor:
        shape = row[0]
        lenght = row[1]
        id_line = row[2]
        array_points = shape.getPart()
        line = arcpy.Polyline(array_points)

        # vypocet mnozstvi segmentu pro segmentacii linie
        segments_count = int(round(lenght / segmentation_size))

        i_cur = arcpy.da.InsertCursor(output_fc, ['Shape@', 'id_line'])
        if segments_count > 0:
            for k in range(0, segments_count):
                segment = line.segmentAlongLine(k / float(segments_count), ((k + 1) / float(segments_count)), True)
                i_cur.insertRow([segment, id_line])
        # pokud je linie kratsi nez pozadovana delka segmentu -- nacte se primo linie
        if segments_count == 0:
            i_cur.insertRow([shape, id_line])
        del i_cur
    del s_cursor
    return output_fc


def create_sql_query(list_of_lists):
    '''
    Z listu jednotlivych ID predpripravi SQL dotazy, ktere vyberou vsechny ID z daneho seznamu.
    Funguje i pro list listu - tedy vytvori list SQL dotazu.
    :param groups: list of lists/ pole poli
    :return: list/pole SQL dotazu
    '''
    sql_list = []
    for list in list_of_lists:
        sql_i = []
        for j in list:
            j_str = str(j)
            if len(sql_i)==0:
                sql_i = '"OBJECTID" = {}'.format(j_str)
            else:
                i = str(sql_i)
                sql_i = i + ' OR "OBJECTID" = {}'.format(j_str)
        sql_list.append(sql_i)
        sql_i = []
    return sql_list


def create_first_point_on_line(in_feature_class):
    '''
    Na jednolivych prvcich liniove vrstvy vytvori body na jejich pocatku.
    :param in_feature_class: liniova vrstva
    :return: Bodovou vrstvu, kde jsou body umiteny na pocatku linii vstupni vrstvy
    '''
    array = arcpy.Array() # pripraveni "listu pro nacteni geometrie"
    points_list = list() # list pro zapisovani souradnic jednotlivych bodu
    output = 'tmp_first_points'
    output_path = os.path.join(workspace, 'tmp_fc') # muze vzniknout problem s cestou!!!
    # zkouska, jestli to pomuze
    if arcpy.Exists('tmp_fc'):
        arcpy.Delete_management('tmp_fc')
    s_cursor = arcpy.da.SearchCursor(in_feature_class, ['Shape@', 'OBJECTID'])
    for row in s_cursor:
        shape = row[0]
        id = row[1]
        array_points = shape.getPart()
        line = arcpy.Polyline(array_points) # (+radek vys) "rozdeli linii na jednotlive body"
        point = line.positionAlongLine(0) # zjisi souradnice pocatecniho bodu
        points_list.append((id, (point.getPart().X, point.getPart().Y))) # zapise souradnice bodu do points_list
        # prevede list se souradnicemi na geometrii
        array = numpy.array([points_list], numpy.dtype([('id_line',numpy.int32),('XY', '<f8', 2)]))
    sr = arcpy.Describe(in_feature_class).spatialReference
    arcpy.da.NumPyArrayToFeatureClass(array, output_path, ['XY'], sr) # vytvoreni nove fc ze vzniklych bodu
    # fce NumPyArrayToFeatureClass neumoznuje prepis jiz existujicich souboru, proto je tu klicka s kopirovanim a mazanim
    arcpy.CopyFeatures_management('tmp_fc', output)
    arcpy.Delete_management('tmp_fc')
    del s_cursor
    return output


def create_list_of_values(in_feature_class, attribute):
    '''
    Pro zvolenou vtupni fc vypise hodnoty pozadovaneho atributu
    :param in_feature_class: fc libovolne geomtrie
    :param attribute: pozadovany atribut
    :return: list hodnot zadaneho atributu
    '''
    list = []
    s_cursor = arcpy.da.SearchCursor(in_feature_class, [attribute])
    for row in s_cursor:
        list.append(row[0])
    del s_cursor
    return list


def classify_contour_size(line_superelev, map_scale, contour_size_1, contour_size_2, contour_size_3, buffer_type):
    '''
    Priradi tloustku kontury ke kazdemu segmentu dle hodnoty prevyseni a pozadovanemu typu bufferu.
    #:param line_superelev: line fc se segmenty s urcenym prevysenim
    #:param map_scale: meritkove cislo mapy
    #:param buffer_type: zadat honotu 'ROUND' pro segmenty udolnic a 'RIGHT' pro segmenty dolnich hran
    #:return: novy atribut ve svtupni vrstve
    '''
    if buffer_type == 'FULL':
        bt = 2
    if buffer_type == 'RIGHT':
        bt = 1
    arcpy.AddField_management (line_superelev, 'contour_size', 'DOUBLE')
    u_cur = arcpy.da.UpdateCursor(line_superelev, ['superelevation','contour_size'])
    for row in u_cur:
        superelevation = row[0]
        if superelevation <= 10:
            value = float(calculate_real_size(map_scale, contour_size_1))/ bt
        if 10 < superelevation <= 25:
            value = float(calculate_real_size(map_scale, contour_size_2)) / bt
        if superelevation > 25:
            value = float(calculate_real_size(map_scale, contour_size_3)) / bt
        row[1] = value
        u_cur.updateRow(row)
    del u_cur
    return line_superelev


def select_extreme_segments(line_superelev, output_fc):
    '''
    Vybere pocatecni a koncovy segment linie
    :param line_superelev: liniova vstupni vrstva (skladajici se ze segmentu)
    :param output_fc: nazev vystupni vrstvy
    :return: output_fc
    '''
    # vytvoreni prazdne fc (odpovidajicich atributu)
    arcpy.CopyFeatures_management(line_superelev, output_fc)
    arcpy.DeleteRows_management (output_fc)

    # vytvoreni vrstvy krajnich segmentu linii - udolnic
    line_id_list = create_list_of_values(line_superelev, 'id_line')
    i = 0 # indexovani v list_id_line
    for row in  line_id_list:
        whereID = '"id_line" = {}'.format(line_id_list[i])
        arcpy.MakeFeatureLayer_management(line_superelev, 'tmp_one_line', whereID)
        segment_id_list = create_list_of_values('tmp_one_line', 'OBJECTID')
        min_id = min(segment_id_list)
        max_id = max(segment_id_list)

        whereID_seg = '"OBJECTID" = {} OR "OBJECTID" = {}'.format(min_id, max_id)
        arcpy.MakeFeatureLayer_management(line_superelev, 'tmp_segments_lyr', whereID_seg)
        seg = arcpy.CopyFeatures_management('tmp_segments_lyr', 'tmp_segments')
        arcpy.Append_management(seg, output_fc)
        i = i + 1
    return output_fc


def select_end_segments(line_superelev, output_fc):
    '''
    Vybere pocatecni a koncovy segment linie
    :param line_superelev: liniova vstupni vrstva (skladajici se ze segmentu)
    :param output_fc: nazev vystupni vrstvy
    :return: output_fc
    '''
    # vytvoreni prazdne fc (odpovidajicich atributu)
    arcpy.CopyFeatures_management(line_superelev, output_fc)
    arcpy.DeleteRows_management (output_fc)

    # vytvoreni vrstvy krajnich segmentu linii - udolnic
    line_id_list = create_list_of_values(line_superelev, 'id_line')
    i = 0 # indexovani v list_id_line
    for row in  line_id_list:
        whereID = '"id_line" = {}'.format(line_id_list[i])
        arcpy.MakeFeatureLayer_management(line_superelev, 'tmp_one_line', whereID)
        segment_id_list = create_list_of_values('tmp_one_line', 'OBJECTID')
        #min_id = min(segment_id_list)
        max_id = max(segment_id_list)

        whereID_seg = '"OBJECTID" = {}'.format(max_id) # OR "OBJECTID" = {} min_id,
        arcpy.MakeFeatureLayer_management(line_superelev, 'tmp_segments_lyr', whereID_seg)
        seg = arcpy.CopyFeatures_management('tmp_segments_lyr', 'tmp_segments')
        arcpy.Append_management(seg, output_fc)
        i = i + 1
    return output_fc


def calculate_contour_line_size(countour_line_fc, id_order_attribute, count_of_contour_line, min_line_width,
                                max_line_width):
    '''
    Priradi tloustku linii (tvarovym caram) na zaklade toho, v jakem poradi byla vytvorena. Tloustka prislusne linie je
    vypocitana linearni interpolaci mezi zadanou minimalni a maximalni hodnotou tloustky linie.
    :param countour_line_fc: liniova vrstva tvarovych car
    :param id_order_attribute: nazev atributu, ktery nese indormaci o poradi, v kterem byla tvarova cara vytvorena
    :param count_of_contour_line: pocet tvarovych car (od jedne kontury/zakladni linie)
    :param min_line_width: maximalni pozadovana tloustka linie kontury
    :param max_line_width: minimalni pozadovana tloustka linie kontury
    :return: vstupni vrstvu tvarovych car s novymm atributem "cl_size"
    '''
    # list "poctu/poradi" tvarovych car
    order_list = []
    for i in range(1, count_of_contour_line + 1):
        order_list.append(i)

    # list hodnot tloustek jednotlivych linii
    add = (float(max_line_width) - float(min_line_width)) / float(count_of_contour_line - 1)
    size_list = []
    size_list.append(min_line_width)
    s = 1
    for j in range(1, (count_of_contour_line - 1)):
        value = min_line_width + s * add
        size_list.append(value)
        s = s + 1
    size_list.append(max_line_width)
    # seradi hodnooty v listu obracene (od nejvetsiho k nejmensimu)
    size_list = size_list[::-1]

    # list listu [[poradi, tloustka], [], ...]
    complet_list = []
    for i in range(0, count_of_contour_line):
        item = []
        item.append(order_list[i])
        item.append(size_list[i])
        complet_list.append(item)

    # prirazeni tloustky linie tvarove cary
    arcpy.AddField_management(countour_line_fc, 'cl_size', 'DOUBLE')
    u_cur = arcpy.da.UpdateCursor(countour_line_fc,
                                  [id_order_attribute, 'cl_size'])  # '"{}"'.format(id_order_attribute)
    for row in u_cur:
        order = row[0]
        row[1] = complet_list[order - 1][1]
        u_cur.updateRow(row)
    del u_cur

    return countour_line_fc

# ------------------------------------------------------------------

"""
def create_points_along_line(in_feature_class, sampling):
    '''
    Na jednolivych prvcich liniove vrstvy vytvori body v pozadovane vzdalenosti(na zaklade daneho atributu).
    :param in_feature_class: liniova vrstva
    :param sampling: nazev atributu, ktery obsahuje hodnoty vzorkovani (pozadovane vzdalenosti mezi body)
    :param out_feature_class: bodova vrstva
    :return: Bodovou vrstvu, kde se body nachazi na linii v pozadovane vzdalenosti.
    '''
    array = arcpy.Array() # pripraveni "listu pro nacteni geometrie"
    points_list = list() # list pro zapisovani souradnic jednotlivych bodu
    output = 'tmp_points_along_line'
    output_path = os.path.join(workspace, 'tmp_fc' ) # muze vzniknout problem s cestou!!!
    s_cursor = arcpy.da.SearchCursor(in_feature_class, ['Shape@', 'Shape_Length', sampling, 'OBJECTID'])
    for row in s_cursor:
        shape = row[0]
        lenght = row[1]
        sampling = row[2]
        sampling_add = row[2]
        id = row[3]
        array_points = shape.getPart()
        line = arcpy.Polyline(array_points) # (+radek vys) "rozdeli linii na jednotlive body"
        while sampling < lenght:
            point = line.positionAlongLine(sampling) # zjisi souradnice bodu na prislusnem miste
            points_list.append((id, (point.getPart().X, point.getPart().Y))) # zapise souradnice bodu do points_list
            sampling += sampling_add
        # prevede list se souradnicemi na geometrii
        array = numpy.array([points_list], numpy.dtype([('id_line',numpy.int32),('XY', '<f8', 2)]))
    sr = arcpy.Describe(in_feature_class).spatialReference
    arcpy.da.NumPyArrayToFeatureClass(array, output_path, ['XY'], sr) # vytvoreni nove fc ze vzniklych bodu
    # fce NumPyArrayToFeatureClass neumoznuje prepis jiz existujicich souboru, proto je tu klicka s kopirovanim a mazanim
    arcpy.CopyFeatures_management('tmp_fc', output)
    arcpy.Delete_management('tmp_fc')
    del s_cursor
    return output
"""

"""
# calculate the length of the lower edge segment
def calculate_sampling(feature_class, segmentation_size):
    '''
    Prepocita zadanou hodnotu velikosti segmentu na optimalni velikost segmentu. Nebo-li vypocita delku segmentu tak,
    aby se co nejvice blizila zadane hodnote a zaroven byla linie rozdelena na stejne dlouhe segmenty.
    :param feature_class: liniova vrstva
    :param segmentation_size: pozadovana velikost segmentu (v metrech)???
    :return: vtupni liniovou vrstvu s novym atributem 'sampling'
    '''
    arcpy.AddField_management (feature_class, 'sampling', "DOUBLE")
    u_cursor = arcpy.da.UpdateCursor(feature_class, ['Shape_Length','sampling'])
    for row in u_cursor:
        lenght = row[0]
        segment_count = round(lenght / segmentation_size) # musim zaokrouhlit, abych mohla "rozpocitat" skutecnou velikost
        try:
            segment = lenght / segment_count
        # pokud je linie kratsi nez pozadovany segment (nebude se delit)
        except ZeroDivisionError:
            segment = lenght
        row[1]= segment
        u_cursor.updateRow(row)
    del u_cursor
    return feature_class
"""


'''
# nahradit fci viz vyse
def calculate_contour_size (map_scale, contour_size_map):
    
    Prepocita pozadovana sirku kontury z mm v mape na m ve skutecnoti.
    :param map_scale: meritkove cislo mapy
    :param contour_size_map: pozadovana tloustka kontury v mape (mm)
    :return: hodnotu pro vytvoreni jednostranneho bufferu
    
    contour_size_real = contour_size_map  * map_scale/1000
    return contour_size_real
'''







