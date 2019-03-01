'''parametrs of superelevation_lower_edges.py'''
in_edges = 'hrana' # line fc of inputs edges
lower_edge_description = "typ_hrana='D'" # name and value of attribute with lower edges in in_edges
in_wall = 'stena' # polygon fc of wall
in_dmr = 'dmt'
output_name = 'superelevation_lower_edges' # line fc output
segmentation_size = 10 # [m]
buffer_zone = 20 # size of buffer for calculating superelevation [m]
distance_polygons = 2 # minimum distance between polygons by creating groups/calculating superelevation [m]

'''parametrs of superelevation_valley.py'''
valley = 'puklina' # line fc input
point_buffer_size = 5 # area radius for calculating value of maximal superelevation [m]
segmentation_size_valley = segmentation_size/4
minimum_wall_height = 2 # value of minimal wall height [m]
output2 = 'superelevation_valley' # line fc output

'''parametrs of output_buffer.py'''
valley_superelev = 'superelevation_valley' #output2
lower_edges_superelev = 'superelevation_lower_edges' # output
map_scale = 500
# in_wall - ze scriptu superelevation_lower_edges.py
output98 = 'rocks_contours_500'