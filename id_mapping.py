# soure: https://www.kaggle.com/code/alexandervc/id-mapping-mygene

from utils import id_mapping

genes = genes = [
    "7319",
    "BCDK", "VTA",
    "UBE1", "UBE2A",
    "STAG2", "NCAPG", "SMC2", "STAG1", "STAG2", "SMC3",
    "CYP11A1", "HSD3B2", "CYP21A2",
    "NOD2",
    "TYR", "SLC24A4",
    "TLR4", "IRAK1", "NFKB1",
    "ERBB4", "PI3K", "AKT", "BAD",
    "PDGFR",
    "FGFR2", "MSX1", "TP63",
    "FABP4", "LPL", "PPAR",
    "VEGFA", "TIE2",
    "B2M", "TAP1", "TAP2", "LMP2A", "LMP2B",
    "DMP1", "DSPP", "BSP"
]

entrez, _, _ = id_mapping(genes)
print(entrez)