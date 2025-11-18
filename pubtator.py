import requests
import time 

LOG_FILE = "abstract_data.txt"

def log_abstract_data(query, total_pages, page_limit, total_abstracts):
    with open(LOG_FILE, "a") as f:
        f.write(f"Query: {query}\n")
        f.write(f"Total available pages: {total_pages}\n")
        f.write(f"Page limit used: {page_limit}\n")
        f.write(f"Total abstracts retrieved: {total_abstracts}\n")
        f.write("-" * 40 + "\n")


class Pubtator:
    BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"

    @staticmethod
    def find_entity_ID(entity_details: str, bioconcept: str = None, limit: int = 100):
        """
        Find out the identifier for a specific bioconcept through free text query.

        :param entity_details: Free text (e.g., 'aspirin', 'BRCA1')
        :param bioconcept: Optional entity type (gene, disease, chemical, variant, species, cellline)
        :param limit: Max results
        """
        url = f"{Pubtator.BASE_URL}/entity/autocomplete/"
        params = {
            "query": entity_details,
            "concept": bioconcept,
            "limit": limit
        }
        r = requests.get(url, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()

    @staticmethod
    def find_related_entity(entity_id: str, relation_type: str = None, entity_type: str = None):
        """
        Query related entities for a given PubTator entity ID.

        :param entity_id: Entity ID, e.g. '@GENE_BRCA1'
        :param relation_type: Relation type (optional), e.g. 'positive_correlate'
        :param entity_type: Entity type (optional), e.g. 'disease', 'gene'
        """
        url = f"{Pubtator.BASE_URL}/relations"
        params = {
            "e1": entity_id,
            "type": relation_type,
            "e2": entity_type
        }
        r = requests.get(url, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()

    @staticmethod
    def search_pubtator_ID(query: str = "", relation: str = None, limit: int = 25):
        """
        Retrieve relevant search results from PubTator3.

        :param query: Can be free text, entityId (e.g., '@CHEMICAL_remdesivir'), or relations.
        :param relation: Optional relation string (e.g., 'relations:ANY|@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms')
        """

        results = []
        page = 1
        num_of_pages = 1  # initial value for first API call
        page_limit = limit
        query = query + " AND genes"
        total_available_pages = 1


        while True:
            url = f"{Pubtator.BASE_URL}/search/"
            

            params = {
                "text": relation if relation else query,
                "page": page
            }
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()

            # Set total pages from first API response
            if page == 1:
                total_available_pages = data.get('total_pages', 1)
                num_of_pages = min(data.get('total_pages', 1), page_limit)
                print(f"Parsing through {num_of_pages} pages")

            curr_result = data.get('results', [])
            pmids = [item["pmid"] for item in curr_result if "pmid" in item]
            results.extend(pmids)

            page += 1
            if page > num_of_pages:
                break

            # Add a short delay every 100 pages to avoid server overload
            # if page % 110 == 0:
            #     print(f"Waiting 0.3 seconds after {page} pages...")
            #     time.sleep(5)
            
            time.sleep(.3)

        # Log the stats
        log_abstract_data(
            query=query,
            total_pages=total_available_pages,
            page_limit=page_limit,
            total_abstracts=len(results)
        )

        return results


    @staticmethod
    def export_abstract(pmid: str, check_for_genes=True):
        """
        Retrieve metadata + gene annotations for a given PMID.

        :param pmid: PubMed ID
        :return: dict with title, journal, abstract, and gene annotations
        """
        url = f"{Pubtator.BASE_URL}/publications/export/biocjson?pmids={pmid}"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        # Base result container
        result = {
            "pmid": pmid,
            "title": None,
            "journal": None,
            "abstract": None,
            "genes": []
        }

        # Extract core metadata
        pub = data["PubTator3"][0]
        passages = pub.get("passages", [])
        result["journal"] = pub.get("journal", None)

        for p in passages:
            p_type = p.get("infons", {}).get("type")
            if p_type == "title":
                result["title"] = p.get("text")
            elif p_type == "abstract":
                result["abstract"] = p.get("text")

            # Extract gene annotations from each passage
            for ann in p.get("annotations", []):
                infons = ann.get("infons", {})
                if infons.get("type", "").lower() == "gene":
                    gene_entry = {
                        "name": infons.get("name"),
                        "identifier": infons.get("identifier"),
                        "accession": infons.get("accession"),
                        "text": ann.get("text"),
                        "location": ann.get("locations", [{}])[0].get("offset", None)
                    }
                    result["genes"].append(gene_entry)
        if check_for_genes:
            if not result["genes"]:
                return None
        return result
