# nastaveni pracovni databaze
work_dtb = '_testicek'



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
map_scale = 1000


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
contour_size_1 = 1      #0.25
contour_size_2 = 1.5    #0.4
contour_size_3 = 2      #0.6

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
# gap_value = 0.5 # v metrech
gap_value = 1.2#0.1 # v mm -- musi byt vetsi nez 0.1 nebo musim upravit parametry bufferu uvnitr scriptu

# cheek_value = 0.7 # v metrech ...lepsi vypocitat jako pridavek k gap_value ... min o 0,2 vetsi, (pak se dela buffer +- 0,1 - tak aby se to neodmazalo)
# addition_value = 0.5 #gap_value ... taky dat jenom jako vypocet ... jako prideavek = parameters.gap_value

# hodnota pro nasobeni mezer - vznikne postupne vzdalovani tvarovych car
multiple = 1.2

# maximalni vyska/sirka steny
# (velikost v [m] ve skutecnosti)
maximal_width_of_wall = 8 # v metrech - duplicitne jeste jendou niz

# minimalni a maximalni tloustka linie tvarovych car
# (velikost v [mm] v mape)
min_line_width = 0.12
max_line_width = 0.5

# velikost bufferu okolo kontur udolnic (pro vytvoreni zakladni linie)
# (velikost v [m] ve skutecnosti)
buff_size_V_value = 0.3

# velikost bufferu, ktery se vytvari pro odmazani lini vzniklych "nepresnostmi"
    # slouzi pro odmazavani dvou bufferu prevedenych na linie,
    # kolem linie, kterou je odmazavno, je vytvoren tento buffer
# (velikost v [m] ve skutecnosti)
buff_size_cca_value = 0.1 #'0.1 Meters'

## VYSTUPNI VRSTVY
output_CL = 'contour_line_{}'.format(map_scale)

# nazev pomocne vystupni vrstvy zakladnich linii
basic_line_name = 'basic_line'

'''
Dalsi parametry pro skript: odmaskovani.py
Vystupem je liniova vrstva "oriznutych" tvarovych car.
'''
# velikost (v %), na kterou se maji rozdelit udolnice pri tvorbe umele steny (pro odmaskovani)
size_percent = 5

# minimalni a maximalni vyska umele steny udolnice
# (velikost v [m] ve skutecnosti)
minimum_valley_wall_height = 0.2
maximum_valley_wall_height = 5

# nazev vystupni vrstvy masky pro odmaskovani okolni mapove kresby
mask = 'mask'

# nazev vystupni vrstvy oriznutych tvarovych car
cl_output_01 = 'contour_line_relevant'


'''
Dalsi parametry pro skript: tc_konflikt.py
Vystupem je liniova vrstva "oriznutych" tvarovych car bez prekryvu/pruseciku.
'''

# velikost, o kterou bude zkracen "sporny segment"
# (velikost v [mm] v mape)
    # pozor, aby hodnota nebyla vetsi, nez sama velikost/delka segmentu
erase_size_value = 0.04 #ted odpovida 0,2 [m]

# nazev vystupni vrstvy tvarovych car (konecna podoba linii)
cl_output = 'contour_lines_line'

'''
Dalsi parametry pro skript: tc_output_buffer.py
Vystupem je liniova vrstva "oriznutych" tvarovych car bez prekryvu/pruseciku.
'''
# nazev vystupni vrstvy
    # linie tvarovych car prevedene na polygony dle prirazene tloustky
cl_polygon = 'contour_lines_polygon'