import arcpy
import parameters
import my_utils
import utils

start = time.time()

#Check the Spatial extension
arcpy.CheckOutExtension('Spatial')

arcpy.env.overwriteOutput = 1
arcpy.env.workspace = '.\\text.gdb'
workspace = arcpy.env.workspace

# inputs
in_edges = parameters.in_edges
lower_edge_description = parameters.lower_edge_description
in_wall = parameters.in_wall
in_dmr = parameters.in_dmr
output_name = parameters.output_name
if arcpy.Exists (output_name):
	arcpy.Delete_management (output_name)
segmentation_size = parameters.segmentation_size
buffer_zone = parameters.buffer_zone
distance_polygons = parameters.distance_polygons


# create fc of lower edges
arcpy.MakeFeatureLayer_management (in_edges, 'in_edges_lyr')
arcpy.SelectLayerByAttribute_management('in_edges_lyr', 'NEW_SELECTION', lower_edge_description)
lower_edges = arcpy.CopyFeatures_management('in_edges_lyr', 'tmp_lower_edges')




# lower edge segmentation, creating new field "seg_id"
segments = my_utils.create_segments(lower_edges, segmentation_size)
output = arcpy.CopyFeatures_management(segments, output_name)
arcpy.AddField_management (output, 'seg_id', 'SHORT')
arcpy.CalculateField_management(output, 'seg_id', '[OBJECTID]', 'VB','')


# creating a buffer around the bottom edge segment
segments_buffer = arcpy.Buffer_analysis(output, 'tmp_lower_edges_seg_buff', buffer_zone, 'RIGHT', 'FLAT', 'NONE','#')


# cropping, selecting the relevant polygon
# provede se prunik bufferu kolem dolni hrany a plochou steny
# nasledne se vyberou jen ty polygony, jejichz ID je shodne s ID segmentu, ktereho se dotykaji (shodna hrana)
arcpy.Clip_analysis(segments_buffer, in_wall,'tmp_clip','')
clip_explode = arcpy.MultipartToSinglepart_management('tmp_clip', 'tmp_clip_expl')
arcpy.SpatialJoin_analysis (clip_explode, output, 'tmp_clip_expl_join', 'JOIN_ONE_TO_MANY', '', '',
                            'INTERSECT', '', '')
arcpy.MakeFeatureLayer_management ('tmp_clip_expl_join', 'tmp_clip_expl_join_lyr')
arcpy.SelectLayerByAttribute_management('tmp_clip_expl_join_lyr','NEW_SELECTION', 'JOIN_FID=seg_id')
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
        sel_lyr = arcpy.MakeFeatureLayer_management('tmp_relevant_polygons', 'tmp_relevant_polygons_lyr', whereID)
        stat = arcpy.gp.ZonalStatisticsAsTable_sa(sel_lyr, 'seg_id', in_dmr,'tmp_zonal_stat_table', 'DATA', 'RANGE')
        stat_view = arcpy.MakeTableView_management(stat, 'tmp_zonal_stat_table_view')
        join_fc = arcpy.AddJoin_management(sel_lyr, 'seg_id', stat_view, 'seg_id', 'KEEP_COMMON')
        arcpy.CopyFeatures_management(join_fc, 'tmp_superelevation')
    else:
        whereID = groups[i]
        sel_lyr = arcpy.MakeFeatureLayer_management('tmp_relevant_polygons', 'tmp_relevant_polygons_lyr', whereID)
        stat = arcpy.gp.ZonalStatisticsAsTable_sa(sel_lyr, 'seg_id', in_dmr, 'tmp_zonal_stat_table', 'DATA', 'RANGE')
        stat_view = arcpy.MakeTableView_management(stat, 'tmp_zonal_stat_table_view')
        join_fc = arcpy.AddJoin_management(sel_lyr, 'seg_id', stat_view, 'seg_id', 'KEEP_COMMON')
        join_copy = arcpy.CopyFeatures_management(join_fc, 'tmp_join_fc')
        arcpy.Append_management (join_copy, 'tmp_superelevation')
    i = i + 1


arcpy.JoinField_management (output, 'OBJECTID', 'tmp_superelevation', 'tmp_relevant_polygons_JOIN_FID',
                            'tmp_zonal_stat_table_RANGE')
arcpy.AlterField_management (output, 'tmp_zonal_stat_table_RANGE', 'superelevation','superelevation' )

'''
# "final cleaning"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)

arcpy.Delete_management('tmp_zonal_stat_table')
'''
end = time.time()
print 'time', end-start