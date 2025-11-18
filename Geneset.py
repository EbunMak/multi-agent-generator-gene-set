class Geneset(object):
    """Work with genesets of various format.
    """
    def __init__(self):
        self.__genesets = {}
        self.gene_set_names = []

########################################################################################
    def read_table(self, file_address, column_sep="\t"):
        """Reads a gene set database from a tabular file and set self.genesets.

        Args:
            file_address (str): Address of a tabulare file with the gene set name as \
                the first element. Gene names start froma the second element. There is \
                no limitation on the number of genes in each gene set.

            column_sep (str): seperates gene set names from the list of gene names. \
                column_sep should not be equalt to gene_sep.

            gene_sep (str): seperates genes in the list of gene names included in each \
                dataset. gene_sep should not be equal to column_sep.

        """
        gene_set_names = []
        gene_set = {}
        # Reading gene sets from file
        with open(file_address, "r") as input:
            line_number = 0
            for line in input:
                line_number += 1
                line = line.strip()
                words = line.split(column_sep)
                gene_set_names.append(words[0])
                gene_set[words[0]] = words[2:]
        self.gene_set_names = gene_set_names
        self.geneset = gene_set

########################################################################################
    def __str__(self):
        """Creates a String representation of gene set database.

        Retruns:
            str: a representation of gene set database where each line represents \
                one gene set. gene set name is the first element in each line, and \
                the genes will be listed after the gene set name. All elements are \
                seperated using tab.
        """
        geneset_string = ""
        geneset_names = self.genesets.keys()
        geneset_names = sorted(geneset_names)
        for name in geneset_names:
            geneset_string += name + "\t" + ",".join(self.genesets[name]) + "\n"
        return geneset_string

    ########################################################################################

def get_gene_set_description(geneset_name, join_char=' '):
    split_name = geneset_name.split('_')[1:]
    return join_char.join(split_name).lower()


def main():
    gs = Geneset()
    gs.read_table("geneset data/c5.hpo.v2024.1.Hs.entrez.gmt")
    for name in gs.gene_set_names[:5]:
        print(get_gene_set_description(name))
    print(gs.gene_set_names[:5])

if __name__ == '__main__':
    main()