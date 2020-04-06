import csv
import datetime
import itertools
import json
import pdb
from collections import Counter
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib_venn import venn3_unweighted

DATA_FOLDER = Path("../data/")
SRCS = ["oneie", "tear-tbd", "tear-matres"]
BOUNDS = [0.75, 0.85, 0.95]
TODAY = datetime.datetime.now().isoformat()

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

def calc_rel_distribution(doc: str, graph: dict) -> List[float]:
    rel_conf_scores = []

    for event in graph[doc]["events"]:
        for relation in graph[doc]["events"][event]["relations"]:
            rel_conf_scores.append(relation["confidence"])

    return rel_conf_scores

def plot_rel_distribution(doc: str, graph: dict) -> None:
    conf_scores = calc_rel_distribution(doc, graph)

    plt.figure()

    plt.hist(conf_scores, edgecolor = "black", range=(0, 1))

    plt.title(f"Distribution of E-E Relation Confidences for Events in Doc {doc}")
    plt.xlabel("E-E Relation Confidence Score (%)")
    plt.ylabel("E-E Relations")

    plt.savefig(f"../analysis/figures/{doc}_relation_dist")

    return

def generate_text_report_and_figures(graph):
    with open(f"../analysis/{TODAY}.txt", "w") as out_f:
        for doc in graph:
            out_f.write(f"Doc ID: {doc}\n")

            plot_rel_distribution(doc, graph)

            venn = {}
            for src in SRCS:
                src_docs = [x for x in graph[doc]["events"] if src in graph[doc]["events"][x]["source"]]

                # gr, ar = find_good_relations(graph, doc, src_docs)
                # print(gr, ar)
                gr, ar = find_good_relations(graph, doc, src_docs)

                num_src_docs = len(src_docs)
                out_f.write(f"\tEvents extracted by '{src}': {num_src_docs}; % relations conf >= 75%: {round(gr[0]/ar, 2)}\n")

                venn[src] = Counter(src_docs)
            # exit()
            plt.figure()    
            c = venn3_unweighted([venn["oneie"], venn["tear-tbd"], venn["tear-matres"]], tuple(["OneIE Events", "TEAR-TBD Events", "TEAR-MATRES Events"]), alpha=0.5)
            plt.savefig(f"../analysis/figures/{doc}_venn")

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