from utils import phenotype_json_reader
from rag_pipeline_2 import create_control_flow

def main():
    phenotype_json_file = "out/only_in_db_p2g_details.json"
    phenotypes = phenotype_json_reader(phenotype_json_file)
    print(f"{len(phenotypes)} read")
    for phenotype in phenotypes[100:200]:
        #initiate lang chain graph
        print(f"The phenotype is {phenotype["name"]}")
        inputs = {
                "phenotype": phenotype,
            }

        graph = create_control_flow()
        events = []
        for event in graph.stream(inputs, stream_mode="values"):
            print("NEW EVENT\n\n")
            events.append(event)
        
        # answer_dict = dict(events[-1])
        # print(answer_dict.keys())
        # content = str(answer_dict["generation"])
        # print(content)


if __name__ == "__main__":
    main()