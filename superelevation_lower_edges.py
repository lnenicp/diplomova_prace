import arcpy
import parameters
import my_utils
import utils

#Check the Spatial extension
arcpy.CheckOutExtension('Spatial')

arcpy.env.overwriteOutput = 1
arcpy.env.workspace = '.\\lnenickova.gdb'
workspace = arcpy.env.workspace


# inputs
in_edges = parameters.in_edges
lower_edge_description = parameters.lower_edge_description
in_wall = parameters.in_wall
in_dmr = parameters.in_dmr
output = parameters.output
if arcpy.Exists (output):
	arcpy.Delete_management (output)
segmentation_size = parameters.segmentation_size
buffer_zone = parameters.buffer_zone
distance_polygons = parameters.distance_polygons

# create fc of lower edges
arcpy.MakeFeatureLayer_management (in_edges, 'in_edges_lyr')
arcpy.SelectLayerByAttribute_management('in_edges_lyr', 'NEW_SELECTION', lower_edge_description)
arcpy.CopyFeatures_management('in_edges_lyr', 'tmp_lower_edges')

# calculate the length of the lower edge segment
my_utils.calculate_sampling('tmp_lower_edges', segmentation_size)

# lower edge segmentation
# nejdrive se vygeneruji body v danych vzdalenostech, podle nich se linie deli
sampling_points = my_utils.create_points_along_line('tmp_lower_edges', 'sampling')
arcpy.SplitLineAtPoint_management('tmp_lower_edges', sampling_points, output, '1 Meters')

# creating a buffer around the bottom edge segment
arcpy.Buffer_analysis(output, 'tmp_lower_edges_seg_buff', buffer_zone, 'RIGHT', 'FLAT', 'NONE','#')

# cropping, selecting the relevant polygon
# provede se prunik bufferu kolem dolni hrany a plochou steny
# nasledne se vyberou jen ty polygony, jejichz ID je shodne s ID segmentu, ktereho se dotykaji (shodna hrana)
arcpy.Clip_analysis('tmp_lower_edges_seg_buff',in_wall,'tmp_clip','')
arcpy.MultipartToSinglepart_management('tmp_clip', 'tmp_clip_expl')
arcpy.SpatialJoin_analysis ('tmp_clip_expl', output, 'tmp_clip_expl_join', 'JOIN_ONE_TO_MANY', '', '',
                            'INTERSECT', '', '')
arcpy.MakeFeatureLayer_management ('tmp_clip_expl_join', 'tmp_clip_expl_join_lyr')
arcpy.SelectLayerByAttribute_management('tmp_clip_expl_join_lyr','NEW_SELECTION', 'JOIN_FID=ORIG_FID')
arcpy.CopyFeatures_management('tmp_clip_expl_join_lyr', 'tmp_relevant_polygons')

# calculating superelevation
# jednotlive polygony rozdeleny do skupin tak, aby se polygony v jedne skupine nedotykaly
# prevyseni v jednotlivych polygonech je urceno pomoci zonalni statisitky (as table)
# tabulka s prevysenim je najoinovana zpet k polygonove vrstve
# u prvni skupiny se vytvori nova polygonova vrstva
# po vypoctu prevyseni u dalsich skupin polygonu jsou prvky nacitany do polygonove vrstvy, ktera byla vytvorena v prvnim behu
# na zaver prejmenovani atributu s hodnotami prevyseni
groups_list = utils.groupFacets('tmp_relevant_polygons', 'OBJECTID', distance_polygons)
groups = my_utils.create_sql_query(groups_list)
i = 0
for j in groups:
    if i == 0:
        whereID = groups[i]
        arcpy.MakeFeatureLayer_management('tmp_relevant_polygons', 'tmp_relevant_polygons_lyr', whereID)
        arcpy.gp.ZonalStatisticsAsTable_sa('tmp_relevant_polygons_lyr', 'ORIG_FID', 'dmr','tmp_zonal_stat_table', 'DATA', 'RANGE')
        arcpy.MakeTableView_management('tmp_zonal_stat_table', 'tmp_zonal_stat_table_view')
        join_fc = arcpy.AddJoin_management('tmp_relevant_polygons_lyr', 'OBJECTID', 'tmp_zonal_stat_table_view',
                                           'ORIG_FID', 'KEEP_COMMON')
        arcpy.CopyFeatures_management(join_fc, 'tmp_superelevation')
    else:
        whereID = groups[i]
        arcpy.MakeFeatureLayer_management('tmp_relevant_polygons', 'tmp_relevant_polygons_lyr', whereID)
        arcpy.gp.ZonalStatisticsAsTable_sa('tmp_relevant_polygons_lyr', 'ORIG_FID', 'dmr', 'tmp_zonal_stat_table', 'DATA', 'RANGE')
        arcpy.MakeTableView_management('tmp_zonal_stat_table', 'tmp_zonal_stat_table_view')
        join_fc = arcpy.AddJoin_management('tmp_relevant_polygons_lyr', 'OBJECTID', 'tmp_zonal_stat_table_view',
                                           'ORIG_FID', 'KEEP_COMMON')
        arcpy.CopyFeatures_management(join_fc, 'tmp_join_fc')
        arcpy.Append_management ('tmp_join_fc', 'tmp_superelevation')
    i = i + 1

arcpy.JoinField_management (output, 'OBJECTID', 'tmp_superelevation', 'tmp_relevant_polygons_ORIG_FID',
                            'tmp_zonal_stat_table_RANGE')
arcpy.AlterField_management (output, 'tmp_zonal_stat_table_RANGE', 'superelevation','superelevation' )


# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)

fileds = [f.name for f in arcpy.ListFields(output)]
fileds.remove('superelevation')
fileds.remove('OBJECTID')
fileds.remove('Shape_Length')
fileds.remove('Shape')
arcpy.DeleteField_management (output, fileds)

arcpy.Delete_management('tmp_zonal_stat_table')

