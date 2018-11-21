import arcpy

def groupFacets(facetfc, id, distance):
    """Rozdeli objekty z polygonove vrstvy do skupin tak, ze v kazde
    skupine jsou plochy, ktere jsou od sebe dale nez je
    zadana mez. Funkce se pri tom snazi minimalizovat pocet skupin.

    Args:
        facetfc (string): nazev shapefile s polygony k roztrideni
        id (string): nazev atributu polygonove vrstvy, ve kterem je
    jednoznacny identifikator
        distance (double): minimalni pozadovana vzdalenost

    Returns:
        list of lists: pole poli, v kazdem poli indexy plosek ve skupine
    """
    geomFieldFac = 'Shape'
    # nasypeme geometrii plosek do pameti:
    facetList = {}
    cur = arcpy.SearchCursor(facetfc)
    for row in cur:
        facetId = row.getValue(id)
        facetList[facetId] = arcpy.Polygon(row.getValue(geomFieldFac).getPart(0))
    del cur

    extents = {}
    # predpocitame si nove extenty
    for i in facetList:
        xmin = facetList[i].extent.XMin - distance
        ymin = facetList[i].extent.YMin - distance
        xmax = facetList[i].extent.XMax + distance
        ymax = facetList[i].extent.YMax + distance

        extents[i] = arcpy.Extent(xmin, ymin, xmax, ymax)

    result = [[]]
    for f in facetList:
        # najdeme skupinu, do ktere ho muzeme zaradit
        # to je takova skupina, ktera splnuje podminku, ze s zadnym jejim prvkem se neprotina
        found = False  # byla nalezena ?
        i = 0
        while not found and i < len(result):
            ok = True
            for item in result[i]:
        # otestujeme, zda item protina aktualne zpracovavanou plosku
                if not extents[f].disjoint(extents[item]):
                    ok = False
                    break
                    # jdeme na dalsi skupinu
            if ok:  # uspech, koncime s hledanim
                found = True
                result[i].append(f)
            i += 1

        if not found:
            # nenasli jsme, musime pridat
            result.append([f])
            # zalozime novou skupinu
    return result
    # vysledek vratime

