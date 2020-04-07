import csv
from datetime import date
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
TODAY = date.today()

def get_unique_relations(all_rel):
    return [dict(s) for s in set(frozenset(rel.items()) for rel in all_rel)] # have to filter out the duplicates

def find_good_relations(graph, doc, found_in_both):
    good_relations = [0, 0, 0]
    relation_count = 0

    for event in found_in_both:
        relations = []
        for key, val in graph[doc][event].items():
            if "relations" in key:
                relations.extend(val)
        unique_relations = get_unique_relations(relations)
        for relation in unique_relations:
            relation_count += 1
            for i, conf in enumerate(BOUNDS):
                if relation["confidence"] >= conf:
                    for j in range(i+1):
                        good_relations[j] += 1
                else:
                    break

    return good_relations, relation_count


def calc_rel_distribution(doc: str, graph: dict) -> List[float]:
    rel_conf_scores = []

    for event in graph[doc]:
        relations = []
        for key, val in graph[doc][event].items():
            if "relations" in key:
                relations.extend(val)
        unique_relations = get_unique_relations(relations)
        for relation in unique_relations:
            rel_conf_scores.append(relation["confidence"])

    return rel_conf_scores


def plot_rel_distribution(doc: str, graph: dict) -> None:
    conf_scores = calc_rel_distribution(doc, graph)

    plt.figure()

    plt.hist(conf_scores, edgecolor="black", range=(0, 1))

    plt.title(
        f"Distribution of E-E Relation Confidences for Events in Doc {doc}")
    plt.xlabel("E-E Relation Confidence Score (%)")
    plt.ylabel("E-E Relations")

    plt.savefig(f"../analysis/figures/{doc}_relation_dist")

    return


def write_intersection_stats(graph: dict, doc: str, out_f: object, pair: tuple, found_in_both: List[str]) -> None:
    good_relations, all_relations = find_good_relations(
                    graph, doc, found_in_both)

    num_x = len(found_in_both)
    out_f.write(
        f"\tEvents extracted by {pair}: {num_x}; Num of relations: {all_relations} \n")
    for i, conf in enumerate(BOUNDS):
        out_f.write(
            f"\t\tRelations in set with confidence >= {conf}: {good_relations[i]}; as percentage: {round(good_relations[i]/all_relations, 2)}\n")

    return

def plot_venn_diagrams(venn, doc):
    plt.figure()
    c = venn3_unweighted([venn["oneie"], venn["tear-tbd"], venn["tear-matres"]], tuple(
        ["OneIE Events", "TEAR-TBD Events", "TEAR-MATRES Events"]), alpha=0.5)
    plt.savefig(f"../analysis/figures/{doc}_venn")

    return

def generate_text_report_and_figures(graph):
    with open(f"../analysis/{TODAY}.txt", "w") as out_f:
        for doc in graph:
            out_f.write(f"Doc ID: {doc}\n")

            plot_rel_distribution(doc, graph)

            venn = {}
            for src in SRCS:

                src_docs = [x for x in graph[doc]
                            if src in graph[doc][x]["source"]]

                gr, ar = find_good_relations(graph, doc, src_docs)

                num_src_docs = len(src_docs)
                out_f.write(
                    f"\tEvents extracted by '{src}': {num_src_docs}; % relations conf >= 75%: {round(gr[0]/ar, 2)}\n")

                venn[src] = Counter(src_docs)
            
            plot_venn_diagrams(venn, doc)

            for pair in itertools.combinations(SRCS, 2):
                pair_intersection = venn[pair[0]] & venn[pair[1]]
                write_intersection_stats(graph, doc, out_f, pair, pair_intersection)

            triple_intersection = venn[SRCS[0]] & venn[SRCS[1]] & venn[SRCS[2]]
            write_intersection_stats(graph, doc, out_f, tuple(SRCS), triple_intersection)

            out_f.write("- - - - - - - - - -\n")

    return


def generate_csv_appendix(graph):
    with open(f"../analysis/appendix/{TODAY}.csv", "w") as csvf:
        csv_writer = csv.writer(csvf,)
        csv_writer.writerow(["event_token", "event_span", "doc_id", "source_MATRES", "source_TBD",
                             "source_OneIE", "type", "has_relations_TBD", "events_AFTER_TBD", "has_relations_MATRES", "events_AFTER_MATRES"])

        for doc in graph:

            for event_id in graph[doc]:

                event_obj = graph[doc][event_id]

                event_token = event_obj["text"]
                src_dict = {}
                for src in SRCS:
                    src_dict[src] = 1 if src in event_obj["source"] else 0
                oneie_type = event_obj["type"] if event_obj.get(
                    "type") else "--"

                tbd_event_relations = [rel["event2_id"]
                                       for rel in event_obj.get("tear-tbd_relations", [])]
                matres_event_relations = [rel["event2_id"]
                                          for rel in event_obj.get("tear-matres_relations", [])]

                tbd_has_relations = 1 if tbd_event_relations else 0
                matres_has_relations = 1 if matres_event_relations else 0

                csv_writer.writerow([event_token, event_id, doc, src_dict["tear-matres"], src_dict["tear-tbd"], src_dict["oneie"],
                                     oneie_type, tbd_has_relations, tbd_event_relations, matres_has_relations, matres_event_relations])

    return


def main():

    with open(DATA_FOLDER / "output/supergraph.json", "r") as f:
        graph = json.load(f)

    generate_text_report_and_figures(graph) 
    generate_csv_appendix(graph)

    return


if __name__ == "__main__":
    main()
