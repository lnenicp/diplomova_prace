# nastaveni pracovni databaze
work_dtb = 'ctvrtek'

'''
Parametry skriptu: superelevation_lower_edges.py
Vystupem je segmentovana dolni hrana, kdy je kazdemu segmentu v atributu "superelevation" urceno prevyseni.
'''
## VSTUPNI VRSTVY
# liniova vrstva (feature class) skalnich hran
in_edges = 'hrana'

# polygonova vrstva (feature class) skalnich utvaru
in_wall = 'stena'

# digitalni model reliefu
in_dmr = 'dmt'

## VSTUPNI PARAMETRY
# nazev a hodnota atributu vrstvy "in_edges", ktery vymezuje dolni hrany
lower_edge_description = "typ_hrana='D'"

# meritko mapy
map_scale = 5000


# velikost segmentu, na ktere bude rozdelena vrstva "in_edges"
# (velikost v [mm] v mape)
segmentation_size = 3 #[mm]

# maximalni velikost/vyska steny (okoli dolni hrany pro vypocet prevyseni steny)
# (velikost v [m] ve skutecnosti)
buffer_zone = 20 #[m]

# minimalni vzdalenost mezi polygony pri vypoctu prevyseni
    # (pro vypocet prevyseni jsou jednotlive poylgony rozdeleny do skupin (tak aby se neprekryvaly,
    # na zaklade toho parametru), a vypocet nasledne probiha pro cele skupiny poylgonu)
# (velikost v [m] ve skutecnosti)
distance_polygons = 2 #[m]

## VYSTUPNI VRSTVY
# liniova vrstva (feature class), kazdy segment obsahuje v atributu "superelevation" hodnotu prevyseni
output_LE = 'superelevation_lower_edges'

'''
Dalsi parametry pro skript: parametrs of superelevation_valley.py.py
Vystupem jsou segmentovane udolnice/pukliny, kdy je kazdemu segmentu v atributu "superelevation" urceno prevyseni.
'''

## DALSI VSTUPNI VRSTVY
# liniova vrstva (feature class) udolnic/puklin
valley = 'puklina'

## DALSI VSTUPNI PARAMETRY
# velikost okoli pruseciku udolnice a dolni hrany, ktere bude pouzito pro vypocet prevyseni
# (velikost v [m] ve skutecnosti)
point_buffer_size = 5 #[m]

# velikost segmentu, na ktere bude rozdelena vrstva "in_edges"
# (velikost v [m] ve skutecnosti)
segmentation_size_valley = segmentation_size/4 #[m]

# minimalni hodnota prevyseni pro linie udolnic
# (velikost v [m] ve skutecnosti)
minimum_wall_height = 2 #[m]

## VYSTUPNI VRSTVY
# liniova vrstva (feature class), kazdy segment obsahuje v atributu "superelevation" hodnotu prevyseni
output_V = 'superelevation_valley'

'''
Dalsi parametry pro skript: output_buffer.py
Vystupem je polygonova vrstva zakladnich kontur.
'''

## DALSI VSTUPNI VRSTVY
# liniova vrstva segmentovanch dolnich hran s urcenym prevysenim
# lower_edges_superelev = output_LE

# liniova vrstva segmentovanch udolnic s urcenym prevysenim
# valley_superelev = output_V

## DALSI VSTUPNI PARAMETRY
# pozadovane sirky kontur
# (velikost v [mm] v mape)
contour_size_1 = 0.25
contour_size_2 = 0.4
contour_size_3 = 0.6

# hodnota pro shlazeni vystupniho polygonu
# (velikost v [m] ve skutecnosti)
    # cim mensi meritko, tim by mela byt mensi i tato hodnota
    # (pri velke hodnote dojde ke spojeni/splynuti blizkych kontur)
buffer_size_smooth_value = 0.1

## VYSTUPNI VRSTVY
# polygonova vrstva zakladnich kontur
output_RC = 'rocks_contours_{}'.format(map_scale)

# zakladni kontura dolnich hran
contours_LE = 'contours_LE_{}'.format(map_scale)

# zakladni kontura udolnic
contours_V = 'contours_V_{}'.format(map_scale)

# levostranny buffer od dalni hrany slouzici k odmazavani
left_LE_buffer_to_erase = 'left_LE_buffer_to_erase'

'''
Dalsi parametry pro skript: tvarove_cary.py
Vystupem je liniova vrstva tvarovych car.
'''
## DALSI VSTUPNI PARAMETRY
# zakladni interval mezi tvarovymi carami
gap_value = 0.5 # v metrech

# cheek_value = 0.7 # v metrech ...lepsi vypocitat jako pridavek k gap_value ... min o 0,2 vetsi, (pak se dela buffer +- 0,1 - tak aby se to neodmazalo)
# addition_value = 0.5 #gap_value ... taky dat jenom jako vypocet ... jako prideavek = parameters.gap_value

# hodnota pro nasobeni mezer - vznikne postupne vzdalovani tvarovych car
multiple = 1.2

# maximalni vyska/sirka steny
# (velikost v [m] ve skutecnosti)
maximal_width_of_wall = 4 # v metrech - duplicitne jeste jendou niz

## VYSTUPNI VRSTVY
output_CL = 'contour_line_{}'.format(map_scale)
buffers_CL = 'buffers_CL'