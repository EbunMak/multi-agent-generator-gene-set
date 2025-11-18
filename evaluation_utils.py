from collections import Counter
from collections import namedtuple
import copy
import numpy as np
import os
from Geneset import get_gene_set_description
import matplotlib.pyplot as plt
import seaborn as sns



def get_core_db(data_dir, dir):
    """
    Get the file names for the core gene set databases
    """
    files = os.listdir(data_dir + '/' +dir)
    core_db = {}
    for file in files:
        f_name = file.split('/')[-1]
        if f_name.startswith("c2.cp.biocarta"):
            core_db['BioCarta'] = f_name
        elif f_name.startswith("c2.cp.reactome"):
            core_db['Reactome'] = f_name
        elif f_name.startswith("GO_Star"):
            core_db['GO_Star'] = f_name
        elif f_name.startswith("c5.go"):
            core_db['GO'] = f_name
        # elif f_name.startswith("msigdb."):
        #     core_db['MSigDB'] = f_name
        elif f_name.startswith("KEGG_Star"):
            core_db['KEGG_Star'] = f_name
        elif f_name.startswith("c2.cp.kegg"):
            core_db['KEGG'] = f_name
    return core_db

def jaccard(G_i, G_j):
    set_a = set(G_i)
    set_b = set(G_j)
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))



def presence_score(gene, db):
    gs_db = GSDB(db)
    presence = 0
    for _, gs in gs_db.db.items():
        if str(gene) in gs:
           presence += 1
    print(gene, ": ", presence)
    return presence

def plot_presence(presence_dict, title="Presence Score for Genes Associated with JIA", 
                  save_path="gene_set_presence.pdf", show=True, vertical=True):
    sorted_sim = sorted(presence_dict.items(), key=lambda x: x[1])  # ascending
    genes, presence = zip(*sorted_sim)

    fig_width = max(10, 0.6 * len(genes))
    plt.figure(figsize=(fig_width, 6))
    
    sns.barplot(x=genes, y=presence, color="#2ecc71")  # Green bars
    plt.xticks(rotation=45, ha='right', fontsize=16)
    plt.xlabel("Genes Associated with JIA", fontsize=20, weight='bold')   
    plt.ylabel("Presence Score", fontsize=20, weight='bold')
    plt.title(title, fontsize=24, weight='bold')
    plt.ylim(0, max(presence) * 1.1)  # adjust based on actual values
    plt.tight_layout()


    plt.savefig(save_path, format="pdf")
    if show:
        plt.show()
    else:
        plt.close()



def coverage(G, L):
    set_G = set(G)
    set_L = set(L)
    return len(set_G.intersection(set_L)) / len(set_G)


def geneset2db_similarity(gs1, database):
    max_sim = 0
    max_name = None
    for name, gs in database.items():
        score = jaccard(gs1, gs)
        if score > max_sim:
            max_sim = score
            max_name = name
    return max_sim, max_name


def db2db_similarity(db1, db2):
    score1 = 0
    for _, gs in db1.items():
        score1 += geneset2db_similarity(gs, db2)[0]
    score2 = 0
    for _, gs in db2.items():
        score2 += geneset2db_similarity(gs, db1)[0]
    return score1 /(2 * len(db1)) + (score2 / (2 * len(db2)))

def geneset2db_ic_similarity(gs1, gsdb1, gsdb2):
    max_sim = 0
    max_name = None
    for name, gs in gsdb2.db.items():
        score = weighted_jaccard(gs1, gs, gsdb1, gsdb2)
        if score > max_sim:
            max_sim = score
            max_name = name
    return max_sim, max_name

def ic_db2db_similarity(db1, db2):
        score1 = 0
        gs_db1 = GSDB(db1)
        gs_db2 = GSDB(db2)
        for _, gs in gs_db1.db.items():
            score1 += geneset2db_ic_similarity(gs, gs_db1, gs_db2)[0]
        score2 = 0
        for _, gs in db2.items():
            score2 += geneset2db_ic_similarity(gs, gs_db2, gs_db1)[0]
        return score1 /(2 * len(db1)) + (score2 / (2 * len(db2)))

def get_similarity_matrix(db1, db2):
    gs_db1 = GSDB(db1)
    gs_db2 = GSDB(db2)
    index = []
    column = []
    similarities = {}
    for name1, gs1 in gs_db1.db.items():
        for name2, gs2 in gs_db2.db.items():
            # new_name = get_gene_set_description(name2, join_char='_').upper()
            # print(new_name)
            if name2 == name1:
                weighted_score = weighted_jaccard(gs1, gs2, gs_db1, gs_db2)
                similarities[name1] = weighted_score

    return similarities


# weighted version of the Jaccard's score taking IC into account
def weighted_jaccard(G_i, G_j, gsdb1, gsdb2):
    set_a = set(G_i)
    set_b = set(G_j)
    intersection = set_a.intersection(set_b)
    intersection_size = 0
    for gene in intersection:
        intersection_size += gsdb1.ic[gene]

    union = set_a.union(set_b)
    union_size = 0
    for gene in union:
        if gene in G_i:
            union_size += gsdb1.ic[gene]
        else:
            union_size += gsdb2.ic[gene]

    return intersection_size / union_size

def plot_gene_set_similarity(similarity_dict, top_n=None, title="Gene Set Similarity Across Versions", 
                             save_path="gene_set_similarity.pdf", show=True, vertical=True):
    """
    Plots a barplot of similarity scores between gene sets across database versions and saves to a PDF.
    """
    # Sort gene sets by similarity
    sorted_sim = sorted(similarity_dict.items(), key=lambda x: x[1])  # ascending
    if top_n:
        sorted_sim = sorted_sim[:top_n]

    gene_sets, similarities = zip(*sorted_sim)

    # Plot
    plt.figure(figsize=(0.5 * len(gene_sets), 6) if vertical else (10, 0.4 * len(gene_sets)))
    
    if vertical:
        sns.barplot(x=gene_sets, y=similarities, palette="coolwarm")
        plt.xticks(rotation=45, ha='right', fontsize=16)  # Tick size
        plt.ylabel("Similarity Score", fontsize=20, weight='bold')       # Label size
        plt.xlabel("Gene Set", fontsize=20, weight='bold')
    else:
        sns.barplot(x=similarities, y=gene_sets, palette="coolwarm", orient='h')
        plt.xlabel("Similarity Score", fontsize=20, weight='bold')
        plt.ylabel("Gene Set", fontsize=20, weight='bold')
        plt.yticks(fontsize=16)

    plt.title(title, fontsize=24, weight='bold')  # Make title big and bold
    plt.ylim(0, 1) if vertical else plt.xlim(0, 1)
    plt.tight_layout()

    # Save plot
    plt.savefig(save_path, format="pdf")
    if show:
        plt.show()
    else:
        plt.close()

class GSDB(object):
    def __init__(self, gsdb):
        self.gsdb_size = len(gsdb)
        freq = Counter()
        for _, gs in gsdb.items():
            freq += Counter(gs)
        self.db = gsdb
        self.presence = freq
        self.dist = {k: v / self.gsdb_size for k, v in freq.items()}
        self.ic = {k: - np.log10(v) for k, v in self.dist.items()}
        self.genes = sorted(freq.keys())

    def mac(self, L):
        max_coverage = 0
        for _, gs in self.db.items():
            gs_coverage = coverage(gs, L)
            if gs_coverage > max_coverage:
                max_coverage = gs_coverage
        return float(max_coverage)

    def weighted_mac(self, L):
        max_coverage = 0
        for _, gs in self.db.items():
            gs_coverage = self.weighted_coverage(gs, L)
            if gs_coverage > max_coverage:
                max_coverage = float(gs_coverage)
        return max_coverage

    def permeability(self, L, tau):
        delta = 0
        for _, gs in self.db.items():
            if coverage(gs, L) >= tau:
                delta += 1
        return delta

    def weighted_coverage(self, G_i, L):
        intersection = set(G_i).intersection(set(L))
        common_ic = sum([self.ic[gene] for gene in intersection])
        G_i_ic = sum([self.ic[gene] for gene in G_i])
        return common_ic / G_i_ic

    def weighted_permeability(self, L, tau):
        delta = 0
        for _, gs in self.db.items():
            if self.weighted_coverage(gs, L) >= tau:
                delta += 1
        return delta

    def bootstrap_test(self, L, weighted_mac=False, num_samples=1000):
        assert len(L) < len(self.genes)
        f = self.mac if weighted_mac == False else self.weighted_mac
        mac_score = f(L)
        count = 0
        for i in range(num_samples):
            S = np.random.choice(self.genes, size=len(L), replace=False)
            if f(S) > mac_score:
                count += 1
        pvalue = count / num_samples
        
        return {'mac': mac_score, 'pvalue': pvalue}