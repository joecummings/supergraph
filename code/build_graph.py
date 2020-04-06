import json
from pathlib import Path
from typing import List, Dict
import pandas as pd
from collections import defaultdict

DATA_FOLDER = Path("../data/")

def parse_to_valid_json(jsonl_file):
    data = []
    jsonl_file.seek(0,0)
    for line in jsonl_file.readlines():
        data.append(json.loads(line))
    return data

def read_file_into_dict(file_path: str) -> dict:

    path_list = (DATA_FOLDER / file_path).glob("*.json")
    json_dict = {}
    for path in path_list:
        with open(path, "r") as f:
            try:
                json_file = json.load(f)
            except json.decoder.JSONDecodeError as err:
                print(f"Reparsing JSONL file because of the following error - {err}")
                json_file = parse_to_valid_json(f)
            if file_path == "oneie":
                key = json_file[0]["doc_id"]
                json_dict[key] = json_file
            else:
                for doc in json_file:
                    key = doc["doc_id"]
                    json_dict[key] = {"events": doc["events"], "relations": doc["relations"], "mentions": doc["mentions"]}

    return json_dict

def standardize_oneie_format(oneie_raw: dict) -> dict:
    
    oneie_formatted = {}
    for doc in oneie_raw.keys():
        oneie_formatted[doc] = {}
        oneie_formatted[doc]["events"] = []
        for seg in oneie_raw[doc]:
            staged_event = {}
            if seg["graph"]["triggers"]:
                for i,trig in enumerate(seg["graph"]["triggers"]):
                    start_trig_idx = seg["token_ids"][trig[0]]
                    idxs = start_trig_idx.split(":")[1].split("-")
                    full_trig_idx = "".join(["[", idxs[0], ":", str(int(idxs[1])+1), ")"])
                    
                    
                    oneie_formatted[doc]["events"].append({
                            "event_id": full_trig_idx, 
                            "type": seg["graph"]["triggers"][i][2],
                        })
            
                
                print(res_str)
        exit(0)
    return oneie_formatted

def combine_graphs(graphs: Dict[str, dict]) -> dict:

    supergraph = {}
    
    graphs["oneie"] = standardize_oneie_format(graphs["oneie"])
       
    for g in graphs:
        for doc in graphs[g]:
            if doc not in supergraph.keys():
                supergraph[doc] = {"events": {}}

            all_events = graphs[g][doc]["events"]
            events_in_supergraph = supergraph[doc]["events"].keys()
            
            for event in all_events:
                event["source"] = [g] # set source name
                event["relations"] = [] # initialize relations
                event_id = event["event_id"]
                if event_id in events_in_supergraph:
                    supergraph[doc]["events"][event_id]["source"].extend(event["source"])
                else:
                    supergraph[doc]["events"][event_id] = event
        
            if g != "oneie":
                all_relations = graphs[g][doc]["relations"]
                for relation in all_relations:
                    key = relation["event1_id"]
                    supergraph[doc]["events"][key]["relations"].append(relation)

    return supergraph


def main():

    oneie_dict = read_file_into_dict("oneie")
    matres_dict = read_file_into_dict("tear/matres")
    tbd_dict = read_file_into_dict("tear/tbd")

    supergraph = combine_graphs({"oneie": oneie_dict, "tear-matres": matres_dict, "tear-tbd": tbd_dict})

    with open(DATA_FOLDER / "output/supergraph.json", "w") as f:
        json.dump(supergraph, f)

if __name__ == "__main__":

    main()
