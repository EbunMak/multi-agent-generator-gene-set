import os

def update_processed_phenotypes(processed_file, genes_dir):
    """
    Compare processed phenotypes (in a .txt file) with actual phenotypes
    having gene extraction JSON files in a directory, and update the file.

    Args:
        processed_file (str): Path to text file containing processed phenotype names.
        genes_dir (str): Directory containing gene extraction JSON files.
    """

    # Read processed phenotypes from file
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            processed = {line.strip() for line in f if line.strip()}
    else:
        processed = set()


    if os.path.exists(genes_dir):
        with open(genes_dir, "r") as f:
            actual = {line.strip() for line in f if line.strip()}
    else:
        actual = set()

    # Find differences
    missing_from_dir = actual - processed

    print(f"✅ Total processed in file: {len(processed)}")
    print(f"✅ Total found in directory: {len(actual)}")
    print(f"❌ To remove (in file, not in dir): {len(missing_from_dir)}")

    print(list(missing_from_dir))
    print(len(missing_from_dir))

# update_processed_phenotypes("processed_gene_sets_llama.txt", "499.txt")

# def rename_repaired_files(directory):
#     """
#     Rename all files ending with '_repaired.json' to remove the '_repaired' part.
#     Example: Splenomegaly_repaired.json → Splenomegaly.json
#     """
#     renamed = 0
#     for filename in os.listdir(directory):
#         if filename.endswith("_repaired.json"):
#             old_path = os.path.join(directory, filename)
#             new_filename = filename.replace("_repaired.json", ".json")
#             new_path = os.path.join(directory, new_filename)

#             try:
#                 os.rename(old_path, new_path)
#                 print(f"Renamed: {filename} to {new_filename}")
#                 renamed += 1
#             except Exception as e:
#                 print(f"Could not rename {filename}: {e}")

#     print(f"\nDone. Renamed {renamed} files in '{directory}'.")


# if __name__ == "__main__":
#     dir_path = "out/phenotype_generations/llama3.1:8b"  # e.g. "out/phenotype_generations"
#     rename_repaired_files(dir_path)

# no_new_genes = ['Abnormal caudate nucleus morphology', 'Abnormal circulating isoleucine concentration', 'Abnormal corneal epithelium morphology', 'Abnormal lung lobation', 'Abnormal muscle fiber alpha dystroglycan', 'Abnormal periungual morphology', 'Abnormal shoulder physiology', 'Abnormality of peripheral nerve conduction', 'Abnormality of the proximal phalanx of the 5th finger', 'Absence of the sacrum', 'Aplasia of the bladder', 'Aplasia of the ulna', 'Axillary freckling', 'Cardiac rhabdomyoma', 'Crackles', 'Cupped ribs', 'Deep venous thrombosis', 'Deviation of the 4th finger', 'Diffuse optic disc pallor', 'Distal symphalangism', 'Enuresis', 'Gastrointestinal desmoid tumor', 'Hyperventilation', 'Maternal autoimmune disease', 'Middle age onset', 'Slowly progressive', 'Spinal cord tumor', 'Thenar muscle atrophy']

# print(len(no_new_genes))

# lost_all_original  = ['Abnormal chromosome morphology', 'Abnormal circulating interleukin 10 concentration', 'Abnormality of the phalanges of the 3rd toe', 'Anhydramnios', 'Cerebellar hemorrhage', 'Craniofacial asymmetry', 'Dacryocystitis', 'Fifth finger distal phalanx clinodactyly', 'Large posterior fontanelle', 'Low back pain']
# print(len(lost_all_original))

# similarity_matric = {'Abnormal activity of mitochondrial respiratory chain': 0.8924990866444699, 'Abnormal bronchoalveolar lavage fluid morphology': 0.8022499772790546, 'Abnormal cardiac biomarker test': 0.47623962954526516, 'Abnormal cardiac septum morphology': 0.016489731037993557, 'Abnormal caudate nucleus morphology': 0.849237764053316, 'Abnormal chromosome morphology': 0.0, 'Abnormal circulating bilirubin concentration': 0.6564769401452089, 'Abnormal circulating interleukin 10 concentration': 0.0, 'Abnormal circulating iron concentration': 0.6589484595691869, 'Abnormal circulating isoleucine concentration': 0.5071809698307658, 'Abnormal corneal epithelium morphology': 0.009367829275092346, 'Abnormal corpus striatum morphology': 0.8323379407847807, 'Abnormal head movements': 0.594193098961446, 'Abnormal liver enzyme activity or concentration': 0.7998695654558118, 'Abnormal lung lobation': 0.5142442077592551, 'Abnormal lymphatic vessel morphology': 0.6449977784403387, 'Abnormal mast cell morphology': 0.7310854459090295, 'Abnormal morphology of the limbic system': 0.7378219051316967, 'Abnormal muscle fiber alpha dystroglycan': 1.0, 'Abnormal muscle tissue metabolite concentration': 0.7697603860722272, 'Abnormal nasal skeleton morphology': 0.529839364816036, 'Abnormal ossification involving the femoral head and neck': 0.041132566625700716, 'Abnormal pericardium morphology': 0.6809304703690541, 'Abnormal periungual morphology': 0.8187205425162478, 'Abnormal portal venous system morphology': 0.1434017422686895, 'Abnormal pulse': 0.5798832437364392, 'Abnormal relationship': 0.875106490724694, 'Abnormal shoulder physiology': 0.5530740126973677, 'Abnormal toenail morphology': 0.48042597378681845, 'Abnormal tricuspid valve physiology': 0.5657016234142752, 'Abnormal ureter morphology': 0.6958464715800783, 'Abnormal urine magnesium concentration': 0.6333549105245806, 'Abnormal wrist physiology': 0.3813556784887806, 'Abnormality of endocrine pancreas physiology': 0.15600217148983359, 'Abnormality of neuronal migration': 0.7954697613429949, 'Abnormality of peripheral nerve conduction': 0.8847969947665556, 'Abnormality of superoxide metabolism': 0.3721900814782671, 'Abnormality of the bladder': 0.5692758575913317, 'Abnormality of the distal phalanges of the toes': 0.7498517141234199, 'Abnormality of the phalanges of the 3rd toe': 0.0, 'Abnormality of the proximal phalanx of the 5th finger': 0.8080408351459961, 'Abnormality of the pulmonary veins': 0.641579239388927, 'Abnormality of the tonsils': 0.02586048987605101, 'Absence of the sacrum': 0.9243824500138006, 'Absent inner dynein arms': 0.38220438807397955, 'Absent pubertal growth spurt': 0.4927310437429845, 'Absent pubic hair': 0.7534327835375189, 'Amaurosis fugax': 0.038409994128976895, 'Amyotrophic lateral sclerosis': 0.9253531388548116, 'Anhydramnios': 0.0, 'Antineutrophil antibody positivity': 0.037620241066432726, 'Aortic valve calcification': 0.3543653760515807, 'Aplasia of the bladder': 0.5859341157904788, 'Aplasia of the ulna': 1.0, 'Arterial thrombosis': 0.8857617998130112, 'Arthralgia of the hip': 0.22372529581918943, 'Asymmetry of the thorax': 0.07487344223318093, 'Axillary freckling': 0.8220801462604574, 'Axillary pterygium': 0.787478377880895, 'Bile duct proliferation': 0.5216529112907383, 'Biliary atresia': 0.06671255120158653, 'Biliary tract neoplasm': 0.6080692729039828, 'Blepharophimosis': 0.6095232839864742, 'Bone marrow hypocellularity': 0.09965788766227361, 'Calvarial osteosclerosis': 0.7083339834588522, 'Cardiac rhabdomyoma': 0.8298396563287388, 'Cerebellar hemorrhage': 0.0, 'Cerebral inclusion bodies': 0.8088675868437903, 'Cervical kyphosis': 0.2561577317500665, 'Chronic pulmonary obstruction': 0.6560587572917348, 'Colon cancer': 0.5597312673301271, 'Crackles': 0.6338532248927351, 'Cranial nerve compression': 0.0017941043870448043, 'Craniofacial asymmetry': 0.0, 'Craniofacial osteosclerosis': 0.1404664004412627, 'Cupped ribs': 0.03978358418553194, 'Cutaneous cyst': 0.7487906100856749, 'Dacryocystitis': 0.0, 'Decreased circulating copper concentration': 0.5828122329859285, 'Decreased glomerular filtration rate': 0.03367900746847583, 'Decreased head circumference': 0.00551167008079058, 'Decreased miniature endplate potentials': 0.8053431953947962, 'Decreased urine output': 0.7388045204988561, 'Deep venous thrombosis': 0.2489143957996064, 'Dehydration': 0.697167194731082, 'Delayed somatosensory central conduction time': 0.38295215249411874, 'Deviation of the 4th finger': 0.24596241072579533, 'Diffuse cerebellar atrophy': 0.3971687599709407, 'Diffuse optic disc pallor': 0.6839824842312408, 'Distal symphalangism': 0.7925440604492794, 'Dry skin': 0.6671175299188936, 'Ecchymosis': 0.6709544774287808, 'Elevated hepatic iron concentration': 0.541094429956879, 'Elevated urinary vanillylmandelic acid': 0.7818140794119148, 'Emphysema': 0.4150532530340503, 'Enlarged epiphyses': 0.481698622449432, 'Enlarged posterior fossa': 0.04907404698736566, 'Enuresis': 0.6263244427005811, 'Epidermal acanthosis': 0.021682575624027374, 'Erythroid hyperplasia': 0.6668346227660472, 'Extrahepatic cholestasis': 0.336476693711073, 'Fetal ultrasound soft marker': 0.5522259680033356, 'Fifth finger distal phalanx clinodactyly': 0.0, 'Fingernail dysplasia': 0.7350309686038488, 'Fingerprint intracellular accumulation of autofluorescent lipopigment storage material': 0.9000478697318746, 'Focal autonomic seizure': 0.1667227537709792, 'Focal dystonia': 0.6105580278253432, 'Follicular hyperplasia': 0.6474448316258278, 'Gait ataxia': 0.8251947050551153, 'Gastrointestinal desmoid tumor': 0.8869353000757465, 'Gastrointestinal obstruction': 0.7562692135010648, 'Glutaric aciduria': 0.23988130736316648, 'Helicobacter pylori infection': 0.5071809698307658, 'Hemangioblastoma': 0.05534962608480507, 'Hepatic fibrosis': 0.7458944698525806, 'High forehead': 0.47292489549140776, 'Hyperextensibility of the finger joints': 0.5815472453230885, 'Hyperventilation': 0.0688325786047293, 'Hypohidrosis': 0.7508435022333251, 'Hypokalemic alkalosis': 0.6516888362222595, 'Hypokalemic metabolic alkalosis': 0.09868033034391731, 'Hypokinesia': 0.016383203712189515, 'Hypoplastic iris stroma': 0.2998965565672667, 'Incisor macrodontia': 0.39783424930506256, 'Increased intervertebral space': 0.42744749782199376, 'Increased pulmonary vascular resistance': 0.5522712637979565, 'Intestinal malrotation': 0.04900910627348928, 'Ketotic hypoglycemia': 0.669523224390996, 'Knee joint hypermobility': 0.3318101757942363, 'Lactic acidosis': 0.7276890590429865, 'Large posterior fontanelle': 0.0, 'Large sella turcica': 0.6198503159324499, 'Leber optic atrophy': 0.47096924836064796, 'Long nose': 0.29818918927429006, 'Low back pain': 0.0, 'Lower limb spasticity': 0.7696026569801988, 'Lymphangiectasis': 0.495167190442968, 'Macule': 0.7420680833704282, 'Malignant neoplasm of the central nervous system': 0.7160084391613575, 'Mandibular aplasia': 0.0501596126183991, 'Maternal autoimmune disease': 0.7042969227740233, 'Median cleft upper lip': 0.6241851750257984, 'Metatarsal synostosis': 0.1438715675476842, 'Microcytic anemia': 0.739586691648942, 'Middle age onset': 0.13318935496279935, 'Slowly progressive': 0.532776976323667, 'Spinal cord tumor': 0.4658952003375543, 'Splenomegaly': 0.4356427956373478, 'Thenar muscle atrophy': 0.03782622824395236}
# fully_similar = []
# for key, value in similarity_matric.items():
#     if value == 1.0:
#         fully_similar.append(key)
# print(len(fully_similar))


import re
from utils import load_gmt

gene_sets = list(load_gmt("phenotype_consensus_gene_sets.gmt").keys())

def analyze_queries(file_path):
    query_pattern = re.compile(r"^Query:\s*(.+)")
    total_pages_pattern = re.compile(r"^Total available pages:\s*(\d+)")
    total_abstracts_pattern = re.compile(r"^Total abstracts retrieved:\s*(\d+)")

    query_data = {}
    current_query = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Match Query
            match_query = query_pattern.match(line)
            
            if match_query:
                current_query = match_query.group(1)
                continue
            # if current_query.split("AND genes")[0].strip() not in gene_sets:
            #     continue
            # Match Total available pages
            match_pages = total_pages_pattern.match(line)
            if match_pages and current_query:
                pages = int(match_pages.group(1))
                query_data.setdefault(current_query, {})["pages"] = pages
                continue

            # Match Total abstracts retrieved
            match_abs = total_abstracts_pattern.match(line)
            if match_abs and current_query:
                abstracts = int(match_abs.group(1))
                query_data.setdefault(current_query, {})["abstracts"] = abstracts
                continue

    # Compute stats
    num_distinct = len(query_data)
    avg_total_pages = sum(q["pages"] for q in query_data.values()) / num_distinct if num_distinct > 0 else 0
    num_below_250 = sum(1 for q in query_data.values() if q.get("pages", 0) <= 25)
    max_pages = max(q["pages"] for q in query_data.values()) if num_distinct > 0 else 0
    min_pages = min(q["pages"] for q in query_data.values()) if num_distinct > 0 else 0
    percent_below_250 = (num_below_250 / num_distinct * 100) if num_distinct > 0 else 0

    # Print results
    print(f"Number of distinct queries: {num_distinct}")
    print(f"Average total available pages across distinct queries: {avg_total_pages:.2f}")
    print(f"Percentage of queries with total abstracts ≤ 250: {percent_below_250:.2f}%")
    print(f"Maximum total available pages: {max_pages}")
    print(f"Minimum total available pages: {min_pages}")

# # Example usage:
# # analyze_queries("queries.txt")

# # Example usage:
# # analyze_queries("queries.txt")


analyze_queries("new_abstract_details.txt")
print(gene_sets[:5])