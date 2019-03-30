
# parameters_2
# 1: 2 000
# nastaveni pracovni databaze
work_dtb = 'tiske_steny'

'''VSTUPNI VRSTVY...................................................................................................'''
# liniova vrstva (feature class) skalnich hran
in_edges = 'hrana'

# polygonova vrstva (feature class) skalnich utvaru
in_wall = 'stena'

# digitalni model reliefu
in_dmr = 'dmr'

# liniova vrstva (feature class) udolnic/puklin
valley = 'puklina'

'''VSTUPNI PARAMETRY................................................................................................'''
'''NUTNE NASTAVIT---------------------------------------------------------------------------------------------------'''
# meritko mapy
map_scale = 2000

# nazev a hodnota atributu vrstvy "in_edges", ktery vymezuje dolni hrany
lower_edge_description = "typ_hrana='D'"

# velikost segmentu, na ktere bude rozdelena vrstva "in_edges"
# (velikost v [mm] v mape)
segmentation_size = 5 #[mm]

# maximalni velikost/vyska/sirka steny (okoli dolni hrany pro vypocet prevyseni steny, pro zjisteni poctu tvarovych car)
# (velikost v [m] ve skutecnosti)
maximal_width_of_wall = 6

# pozadovane sirky kontur
# (velikost v [mm] v mape)
contour_size_1 = 0.4
contour_size_2 = 0.8
contour_size_3 = 1.2

# velikost pro odmaskovani okolni kresby (kolik mm od okraje kresby skal bude ostatni kresba)
# (velikost v [mm] v mape)
mask_gap_value = 1.5

# velikost levostranneho bufferu pro odmazavai nepresnosti pri tvorbe kontur
# (velikost v [m] ve skutecnosti)
#left_buffer_size_value = 4 # velikost nastevana primo ve scriptu tak, ze odpovida max sirce kontury

# hodnota pro shlazeni vystupniho polygonu
# (velikost v [m] ve skutecnosti)
    # cim mensi meritko, tim by mela byt mensi i tato hodnota
    # (pri velke hodnote dojde ke spojeni/splynuti blizkych kontur)
buffer_size_smooth_value = 1

'''pro tvarove cary-------------------------------------------------'''
# zakladni interval mezi tvarovymi carami
# gap_value = 0.5 # v metrech
gap_value = 0.35 #0.1 # v mm -- musi byt vetsi nez 0.1 nebo musim upravit parametry bufferu uvnitr scriptu

# hodnota pro nasobeni mezer - vznikne postupne vzdalovani tvarovych car
multiple = 1.2

# minimalni a maximalni tloustka linie tvarovych car
# (velikost v [mm] v mape)
min_line_width = 0.12
max_line_width = 0.25

# minimalni a maximalni vyska umele steny udolnice
# (velikost v [m] ve skutecnosti)
minimum_valley_wall_height = 0.2
maximum_valley_wall_height = 5

# velikost, o kterou bude zkracen "sporny segment"
# (velikost v [mm] v mape)
    # pozor, aby hodnota nebyla vetsi, nez sama velikost/delka segmentu
erase_size_value = 0.04 #ted odpovida 0,2 [m]


'''MUZE ZUSTAT JO DEFAULT-------------------------------------------------------------------------------------------'''


# minimalni vzdalenost mezi polygony pri vypoctu prevyseni
    # (pro vypocet prevyseni jsou jednotlive poylgony rozdeleny do skupin (tak aby se neprekryvaly,
    # na zaklade toho parametru), a vypocet nasledne probiha pro cele skupiny poylgonu)
# (velikost v [m] ve skutecnosti)
distance_polygons = 2 #[m]

# velikost okoli pruseciku udolnice a dolni hrany, ktere bude pouzito pro vypocet prevyseni
# (velikost v [m] ve skutecnosti)
point_buffer_size = 5 #[m]

# velikost segmentu, na ktere bude rozdelena vrstva "in_edges"
# (velikost v [mm] v mape)
segmentation_size_valley = float(segmentation_size)/float(3) #[mm]

# minimalni hodnota prevyseni pro linie udolnic
# (velikost v [m] ve skutecnosti)
minimum_wall_height = 2 #[m]

# velikost bufferu okolo kontur udolnic (pro vytvoreni zakladni linie)
# (velikost v [m] ve skutecnosti)
buff_size_V_value = 0.3

# velikost bufferu, ktery se vytvari pro odmazani lini vzniklych "nepresnostmi"
    # slouzi pro odmazavani dvou bufferu prevedenych na linie,
    # kolem linie, kterou je odmazavno, je vytvoren tento buffer
# (velikost v [m] ve skutecnosti)
buff_size_cca_value = 0.1 #'0.1 Meters'

# velikost (v %), na kterou se maji rozdelit udolnice pri tvorbe umele steny (pro odmaskovani)
size_percent = 5

'''VYSTUPNI VRSTVY..................................................................................................'''
# prevyseni dolnich hran
# liniova vrstva (feature class), kazdy segment obsahuje v atributu "superelevation" hodnotu prevyseni
output_LE = 'superelevation_lower_edges_{}'.format(map_scale)

# prevyseni udolnic
# liniova vrstva (feature class), kazdy segment obsahuje v atributu "superelevation" hodnotu prevyseni
output_V = 'superelevation_valley_{}'.format(map_scale)

# polygonova vrstva zakladnich kontur
output_RC = 'rocks_contours_{}'.format(map_scale)

# zakladni kontura udolnic
contours_V = 'contours_V_{}'.format(map_scale)

# levostranny buffer od dalni hrany slouzici k odmazavani
left_LE_buffer_to_erase = 'left_LE_buffer_to_erase_{}'.format(map_scale)

# doplnkove tvarove cary
output_CL = 'contour_line_all_{}'.format(map_scale)

# zakladnich linie
basic_line_name = 'basic_line_{}'.format(map_scale)

# nazev vystupni vrstvy masky pro odmaskovani okolni mapove kresby
mask = 'mask_{}'.format(map_scale)

# nazev vystupni vrstvy oriznutych tvarovych car
cl_output_01 = 'contour_line_clip_{}'.format(map_scale) # rename cl_output

# nazev vystupni vrstvy tvarovych car (konecna podoba linii)
cl_output = 'contour_lines_line_{}'.format(map_scale) # rename cl_output_line

# nazev vystupni vrstvy
    # linie tvarovych car prevedene na polygony dle prirazene tloustky
cl_polygon = 'contour_lines_polygon_{}'.format(map_scale) # rename cl_output_polygon