from Geneset import Geneset, get_gene_set_description
from evaluation_utils import GSDB, ic_db2db_similarity, db2db_similarity, get_similarity_matrix, plot_gene_set_similarity, presence_score, plot_presence
import csv
import os
from utils import id_mapping

def measure_db2db_similarity(db1_file, db2_file):
    db1 = Geneset()
    db2 = Geneset()
    db1.read_table(db1_file)
    db2.read_table(db2_file)
    try:
        assert len(db1.gene_set_names) == len(db2.gene_set_names)
        similarity_score = db2db_similarity(db1.geneset, db2.geneset)
        weighted_similarity_score = ic_db2db_similarity(db1.geneset, db2.geneset)
        db_name = 'HPO'#db2.gene_set_names[0].split('_')[0]

        print(f'The similarity score is {similarity_score} \n')
        print(f'The weighted similarity score is {weighted_similarity_score} \n')
        with open('out/similarity_results.txt', 'a') as file:
            file.write(db_name + '\t' + str(similarity_score) + '\t' + str(weighted_similarity_score))
        
        similarity_matrix = get_similarity_matrix(db1.geneset, db2.geneset)
        print(similarity_matrix)
        save_path = "out/gene_set_similarity_"+ db_name.capitalize() + ".pdf"
        plot_gene_set_similarity(similarity_matrix, title="Gene Set Similarity for " + db_name.capitalize(), save_path=save_path)
        with open('out/'+db_name+'_similarity_matrix.txt', 'a') as file:
            file.write(db_name+"\t"+str(similarity_matrix))
    except AssertionError:
        print(f'Geneset DB 1 length is {len(db1.gene_set_names)} is not equal to Geneset DB 2 length {len(db2.gene_set_names)}')
        # for key in db1.geneset.keys():
        #     keys2 = list(db2.geneset.keys())
        #     if key not in keys2:
        #         print(f'The difference is {key}')


def run_bootstrap_test(dbs, phenotype, file_path, weighted_mac=False):
    """
    Calculate the non-information content or information content based 
    `MAC` score and determine it's statistical significance. The result 
    is stored in a csv file in the output directory.
    """
    for phenotype_name, L in phenotype.items():
        for db_name, db in dbs.items():
            db_i = {}
            for name, gs in db.geneset.items():
                db_i[name] = []
                for g in gs:
                    db_i[name].append(int(g))
            gsdb = GSDB(db_i)
            # print(gsdb)
            if weighted_mac:
                mac_score = gsdb.weighted_mac(L)
                print(mac_score)
            else:
                mac_score = gsdb.mac(L)
                print(mac_score)
            result = gsdb.bootstrap_test(L, weighted_mac=weighted_mac, num_samples=1000)
            mac, pvalue = result['mac'], result['pvalue']
            assert mac == mac_score
            print(f'{phenotype_name}\t{db_name}\t{mac}\t{pvalue}')
            new_row = [phenotype_name, db_name, mac, pvalue]
            with open(file_path,'a',newline='') as f:
                writer = csv.writer(f)
                writer.writerow(new_row)

def eval_presence(gene_list, db_file, db_name=""):
    db = Geneset()
    db.read_table(db_file)
    with open(gene_list) as fin:
        genes = [int(gene_id) for gene_id in fin.read().strip().split('\n')]

    presence_dict = {}
    sum = 0
    for g in genes:
        presence_dict[g] = presence_score(g,db.geneset)
        sum+=presence_dict[g]
    title = "Presence Score in "+db_name+" for Genes Associated with JIA"
    path = "out/"+db_name+"_gene_set_presence.pdf"
    print("total for ", db_name, " is:", sum)
    plot_presence(presence_dict, title=title, save_path=path)


def mac_evaluation():
    out_dir = 'out/'
    data_dir = 'geneset data/'

    # Create an output directory for significant assessment of MAC scores
    os.makedirs(os.path.join(out_dir, 'MAC'), exist_ok=True)

    phenotype_files = {
        'AMD': 'AMD.txt',
        'Hyperactive': 'Hyperactive.txt',
        'JIA': 'JIA_genes.txt',
        'Schizophrenia': 'Schizophrenia.txt',
        'UvealMelanoma': 'UvealMelanoma.txt',
        'Glioblastoma': 'Glioblastoma.txt',
        'SLE': 'Systemic Lupus Erythematosus_entrez.txt',
        'Rheumatoid Arthritis': 'Rheumatoid Arthritis_entrez.txt',
        'Medullablastoma': 'Medulloblastoma_entrez.txt',
        'IBD': 'Inflammatory Bowel Disease_entrez.txt'
    }
    
    db_paths = {
        # 'HALLMARK': 'geneset data/h.all.v2024.1.Hs.entrez .gmt',
        # 'HALLMARK_Star': 'sample_Hallmark_final.gmt',
        'KEGG': 'geneset data/c2.cp.kegg_legacy.v2024.1.Hs.entrez.gmt',
        'KEGG_New': 'kegg_genes_final.gmt'
        }

    dbs = {}
    for name, path in db_paths.items():
        dbs[name] = Geneset()
        dbs[name].read_table(path)

    
    phenotype = {}

    # Create the list of genes for each phenotype
    for name, file in phenotype_files.items():
        with open(os.path.join(data_dir, file)) as fin:
            phenotype[name] = [int(gene_id) for gene_id in fin.read().strip().split('\n')]
    
    # run bootstrap test for the mac score for each dataset
    file = os.path.join(out_dir, 'MAC/significant_mac.csv')
    run_bootstrap_test(dbs, phenotype, file)

    
    # run bootstrap test for the IC based mac score for each dataset
    file = os.path.join(out_dir, 'MAC/significant_ic_mac.csv')
    run_bootstrap_test(dbs, phenotype, file, weighted_mac=True)
    


def main():
    db1_file = "consensus_gene_sets_100.gmt"
    db2_file = "phenotype_consensus_gene_sets_100.gmt"
    # measure_db2db_similarity(db1_file, db2_file)
    # db1_file = "kegg_genes_final.gmt"
    # db2_file = "geneset data/c2.cp.kegg_legacy.v2024.1.Hs.entrez.gmt"
    
    # # mac_evaluation()

    eval_presence("geneset data/Hyperactive.txt",db1_file,db_name="Curated_HPO")
    eval_presence("geneset data/Hyperactive.txt",db2_file,db_name="Original_HPO")

    # with open('geneset data/Glioblastoma_symbols.txt', "r") as fin:
    #     genes_symbols = [gene_id for gene_id in fin.read().strip().split('\n')]

    # genes_entrez,_,_ = id_mapping(genes_symbols)

    # with open('geneset data/Glioblastoma.txt', 'w') as fin:
    #     for gene in genes_entrez:
    #         fin.write(f'{gene}\n')


if __name__ == "__main__":
    main()