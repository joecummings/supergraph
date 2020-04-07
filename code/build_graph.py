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
            idx_to_event = {} # temp directory to hold the event that we're building/converting

            for i,trig in enumerate(seg["graph"]["triggers"]): # need to create the event_id first
                start_trig_idx = seg["token_ids"][trig[0]]
                idxs = start_trig_idx.split(":")[1].split("-")
                full_idx = "".join(["[", idxs[0], ":", str(int(idxs[1])+1), ")"])

                idx_to_event[i] = {
                        "event_id": full_idx,
                        "text": seg["tokens"][trig[0]], # this is assuming that a trigger is only one token long 
                        "type": seg["graph"]["triggers"][i][2],
                        "arguments": []
                    }
             
            for role in seg["graph"]["roles"]: # add argument and argument roles to the event
                entity_idx = role[1]
                entity_tkn_start_idx = seg["graph"]["entities"][entity_idx][0]
                entity_tkn_end_idx = seg["graph"]["entities"][entity_idx][1]
                entity_lst = []

                # get entity
                for j in range(entity_tkn_start_idx, entity_tkn_end_idx):
                    entity_lst.append(seg["tokens"][j])
                entity = " ".join(entity_lst)

                event_idx = role[0]
                idx_to_event[event_idx]["arguments"].append({
                    "role": role[2],
                    "token": entity
                })
                
            # add event to the final events graph
            oneie_formatted[doc]["events"].extend(list(idx_to_event.values()))

    return oneie_formatted

def get_token_from_mention_id(graph, mention_id):
    return next(mention for mention in graph["mentions"] if mention["mention_id"] == mention_id)["text"]

def combine_graphs(graphs: Dict[str, dict]) -> dict:

    supergraph = {}
    
    graphs["oneie"] = standardize_oneie_format(graphs["oneie"])
       
    for g in graphs:
        for doc in graphs[g]:
            if doc not in supergraph.keys():
                supergraph[doc] = {}

            all_events_in_g = graphs[g][doc]["events"]
            events_in_supergraph = supergraph[doc].keys()

            for event in all_events_in_g:
                new_event = {}
                
                event_id = event["event_id"]
                new_event["text"] = event["text"]

                if g == "oneie":
                    new_event["type"] = event["type"]
                    new_event["oneie_args"] = event["arguments"]
                else:
                    args = event["arguments"]
                    args_with_tokens = []
                    for arg in args:
                        token = get_token_from_mention_id(graphs[g][doc], arg["mention_id"])
                        args_with_tokens.append({"role": arg["role"], "token": token})
                    new_event[f"{g}_args"] = args_with_tokens
                
                if event_id in events_in_supergraph:
                    for key in new_event:
                        supergraph[doc][event_id][key] = new_event[key]
                    supergraph[doc][event_id]["source"].append(g) # this actually causes duplicates but that's okay for now
                else:
                    new_event["source"] = [g] # set source name
                    supergraph[doc][event_id] = new_event
        
            if g != "oneie":
                all_relations = graphs[g][doc]["relations"]
                for relation in all_relations:
                    key = relation["event1_id"]
                    if supergraph[doc][key].get(f"{g}_relations"):
                        supergraph[doc][key][f"{g}_relations"].append(relation)
                    else:
                        supergraph[doc][key][f"{g}_relations"] = [relation]

    return supergraph


def main():

    oneie_dict = read_file_into_dict("oneie")
    matres_dict = read_file_into_dict("tear/matres")
    tbd_dict = read_file_into_dict("tear/tbd")

    supergraph = combine_graphs({"tear-matres": matres_dict, "tear-tbd": tbd_dict, "oneie": oneie_dict})

    with open(DATA_FOLDER / "output/supergraph.json", "w") as f:
        json.dump(supergraph, f)

if __name__ == "__main__":

    main()
