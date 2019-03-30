import arcpy
import parameters
import my_utils
import utils

start = time.time()
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = 1

# nastaveni pracovni databaze
work_dtb = parameters.work_dtb
arcpy.env.workspace = '.\\{}.gdb'.format(work_dtb)
workspace = arcpy.env.workspace

## NASTAVENI
# vstupni vrstvy
in_edges = parameters.in_edges
in_wall = parameters.in_wall
in_dmr = parameters.in_dmr

# vstupni parametry
lower_edge_description = parameters.lower_edge_description
map_scale = parameters.map_scale
segmentation_size = parameters.segmentation_size
segmentation_size = my_utils.calculate_real_size(map_scale, segmentation_size)
buffer_zone = parameters.buffer_zone
distance_polygons = parameters.distance_polygons

# vystupni vrstvy
output_LE = parameters.output_LE
if arcpy.Exists (output_LE):
	arcpy.Delete_management (output_LE)

## VYPOCET
# vytvoreni vrstvy dolnich hran
arcpy.MakeFeatureLayer_management (in_edges, 'in_edges_lyr')
arcpy.SelectLayerByAttribute_management('in_edges_lyr', 'NEW_SELECTION', lower_edge_description)
lower_edges = arcpy.CopyFeatures_management('in_edges_lyr', 'lower_edges')

# segmentace dolnich hran
segments = my_utils.create_segments(lower_edges, segmentation_size)
output = arcpy.CopyFeatures_management(segments, output_LE)
arcpy.AddField_management (output, 'id_segment', 'SHORT')
arcpy.CalculateField_management(output, 'id_segment', '[OBJECTID]', 'VB','')

# vytvoreni bufferu okolo dolnich hran
segments_buffer = arcpy.Buffer_analysis(output, 'tmp_lower_edges_seg_buff', buffer_zone, 'RIGHT', 'FLAT', 'NONE','#')


# orez a vyber relevantnich polygonu
    # provede se prunik bufferu kolem dolni hrany a plochou steny
    # nasledne se vyberou jen ty polygony, jejichz ID je shodne s ID segmentu, ktereho se dotykaji (shodna hrana)
arcpy.Clip_analysis(segments_buffer, in_wall,'tmp_clip','')
clip_explode = arcpy.MultipartToSinglepart_management('tmp_clip', 'tmp_clip_expl')
arcpy.SpatialJoin_analysis (clip_explode, output, 'tmp_clip_expl_join', 'JOIN_ONE_TO_MANY', '', '',
                            'INTERSECT', '', '')
arcpy.MakeFeatureLayer_management ('tmp_clip_expl_join', 'tmp_clip_expl_join_lyr')
arcpy.SelectLayerByAttribute_management('tmp_clip_expl_join_lyr','NEW_SELECTION', 'JOIN_FID = id_segment')
arcpy.CopyFeatures_management('tmp_clip_expl_join_lyr', 'tmp_relevant_polygons')


# vypocet prevyseni
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
        stat = arcpy.gp.ZonalStatisticsAsTable_sa(sel_lyr, 'id_segment', in_dmr,'tmp_zonal_stat_table', 'DATA', 'RANGE')
        stat_view = arcpy.MakeTableView_management(stat, 'tmp_zonal_stat_table_view')
        join_fc = arcpy.AddJoin_management(sel_lyr, 'id_segment', stat_view, 'id_segment', 'KEEP_COMMON')
        arcpy.CopyFeatures_management(join_fc, 'tmp_superelevation')
    else:
        whereID = groups[i]
        sel_lyr = arcpy.MakeFeatureLayer_management('tmp_relevant_polygons', 'tmp_relevant_polygons_lyr', whereID)
        stat = arcpy.gp.ZonalStatisticsAsTable_sa(sel_lyr, 'id_segment', in_dmr, 'tmp_zonal_stat_table', 'DATA', 'RANGE')
        stat_view = arcpy.MakeTableView_management(stat, 'tmp_zonal_stat_table_view')
        join_fc = arcpy.AddJoin_management(sel_lyr, 'id_segment', stat_view, 'id_segment', 'KEEP_COMMON')
        join_copy = arcpy.CopyFeatures_management(join_fc, 'tmp_join_fc')
        arcpy.Append_management (join_copy, 'tmp_superelevation')
    i = i + 1

arcpy.JoinField_management (output, 'OBJECTID', 'tmp_superelevation', 'tmp_relevant_polygons_JOIN_FID',
                            'tmp_zonal_stat_table_RANGE')
arcpy.AlterField_management (output, 'tmp_zonal_stat_table_RANGE', 'superelevation','superelevation' )


# "zaverecny uklid"
list = arcpy.ListFeatureClasses('tmp_*')
for item in list:
    arcpy.Delete_management(item)

arcpy.Delete_management('tmp_zonal_stat_table')

end = time.time()
print 'time', end-start