from pubtator import Pubtator

if __name__ == "__main__":
    # 1. Find entity ID for "aspirin"
    print("🔍 Searching PubTator for 'aspirin'...")
    entities = Pubtator.find_entity_ID("aspirin", bioconcept="chemical", limit=3)
    print("Entities found:", entities)

    if not entities:
        print("No entities found for aspirin.")
    else:
        # Take the first entity ID
        entity_id = entities[0]["_id"]
        print(f"\n✅ Using entity ID: {entity_id}")

        # 2. Find related diseases for aspirin
        print("\n🔍 Finding related diseases...")
        related = Pubtator.find_related_entity(entity_id, relation_type=None, entity_type="disease")
        print("Related entities:", related[:2])  # show first 2 only

        if related:
            # Take the first related disease
            related_entity = related[0]["source"]
            print(f"\n✅ First related disease entity ID: {related_entity}")

            # 3. Search PubTator for articles linking aspirin and that disease
            print("\n🔍 Searching PubTator for co-mentioned articles...")
            relation_query = f"relations:ANY|{entity_id}|{related_entity}"
            articles = Pubtator.search_pubtator_ID(query=None, relation=relation_query, num_of_pages=1)
            print("Articles found:", [a.get("pmid") for a in articles[:3]])  # show PMIDs

            if articles:
                pmid = articles[0].get("pmid")
                print(f"\n✅ Fetching abstract for PMID {pmid}...")
                abstract = Pubtator.export_abstract(pmid)
                print("\n📄 Abstract Result:")
                print("Title:", abstract["title"])
                print("Journal:", abstract["journal"])
                print("Abstract:", abstract["abstract"])
                print("Annotations:", abstract["annotations"][:5])  # show first 5 annotations
        else:
            print("No related diseases found.")
