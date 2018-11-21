import arcpy
import os
import numpy

#Check the Spatial extension
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = 1
arcpy.env.workspace = ".\\lnenickova.gdb"
workspace = arcpy.env.workspace

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


# vytvoreni SQL dotazu
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
