import json
from pathlib import Path
import datetime
import itertools
import matplotlib.pyplot as plt
from matplotlib_venn import venn3_unweighted
from collections import Counter
import pdb

DATA_FOLDER = Path("../data/")
SRCS = ["oneie", "tear-tbd", "tear-matres"]
BOUNDS = [0.75, 0.85, 0.95]

def find_good_relations(graph, doc, found_in_both):
    good_relations = [0,0,0]
    relations = 0

    for key in found_in_both: 
        # pdb.set_trace()
        for relation in graph[doc]["events"][key]["relations"]:
            relations += 1
            # pdb.set_trace()
            for i, conf in enumerate(BOUNDS):
                if relation["confidence"] >= conf:
                    for j in range(i+1):
                        good_relations[j] += 1
                else:
                    break

    return good_relations, relations

def main():
    
    with open(DATA_FOLDER / "output/supergraph.json", "r") as f:
        graph = json.load(f)
    
    with open(f"../analysis/{datetime.datetime.now().isoformat()}.txt", "w") as out_f:
        for doc in graph:
            out_f.write(f"Doc ID: {doc}\n")
            
            venn = {}
            for src in SRCS:
                src_docs = [x for x in graph[doc]["events"] if src in graph[doc]["events"][x]["source"]]

                # gr, ar = find_good_relations(graph, doc, src_docs)
                # print(gr, ar)

                num_src_docs = len(src_docs)
                out_f.write(f"\tEvents extracted by '{src}': {num_src_docs}\n")

                venn[src] = Counter(src_docs)
            # exit()
            plt.figure()    
            c = venn3_unweighted([venn["oneie"], venn["tear-tbd"], venn["tear-matres"]], tuple(["OneIE Events", "TEAR-TBD Events", "TEAR-MATRES Events"]), alpha=0.5)
            plt.savefig(f"../analysis/{doc}")

            for pair in itertools.combinations(SRCS, 2):
                found_in_both = venn[pair[0]] & venn[pair[1]] # intersection between the two sets

                good_relations, all_relations = find_good_relations(graph, doc, found_in_both)
                
                num_x = len(found_in_both)
                out_f.write(f"\tEvents extracted by {pair}: {num_x}; Num of relations: {all_relations} \n")
                for i,conf in enumerate(BOUNDS):
                    out_f.write(f"\t\tRelations in set with confidence >= {conf}: {good_relations[i]}; as percentage: {round(good_relations[i]/all_relations, 2)}\n")

            # 3 way comparison
            found_in_both = venn[SRCS[0]] & venn[SRCS[1]] & venn[SRCS[2]]
            num_x = len(found_in_both)
            good_relations, all_relations = find_good_relations(graph, doc, found_in_both)
            out_f.write(f"\tEvents extracted by {tuple(SRCS)}: {num_x}; Num of relations: {all_relations} \n")
            for i,conf in enumerate(BOUNDS):
                out_f.write(f"\t\tRelations in set with confidence >= {conf}: {good_relations[i]}; as percentage: {round(good_relations[i]/all_relations, 2)}\n")

            out_f.write("- - - - - - - - - -\n")        

            # exit(0)          

if __name__ == "__main__":
    main()