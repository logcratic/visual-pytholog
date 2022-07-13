import collections
import inspect
import itertools
import graphviz
import pytholog as pl

rules_file = r''
facts_file = r''
constant_facts_file = r''
wizard_facts_file = r''
facts_location_file = r''

def path_to_tree(path, constants = None):
    tree = graphviz.Digraph(format='png')

    nodes = []
    edges = []
    substitutes = []
    for item in path:
        if item[0].fact.count(":-") == 1:
            substitutes.append(item[0].lh.f)
            nodes.append(item[0].lh.f)
            nodes.append(item[2].f)
            edges.append((item[2].f, item[0].lh.f))
            for rh_item in item[0].rhs:
                nodes.append(rh_item.f)
                nodes.append(item[0].lh.f)
                edges.append((item[0].lh.f, rh_item.f))
        else:
            nodes.append(item[0].fact)
            nodes.append(item[2].f)
            edges.append((item[2].f, item[0].fact))

    # remove subsitution redundant nodes
    new_edges = []
    for sub in substitutes:
        for edge in edges:
            if (edge[0].split("(")[0] == sub.split("(")[0] and edge[0].count(",") == sub.count(",")):
                edges.remove(edge)
                nodes.remove(edge[0])
                new_edges.append((sub,edge[1]))
            if (edge[1].split("(")[0] == sub.split("(")[0] and edge[1].count(",") == sub.count(",")):
                edges.remove(edge)
                nodes.remove(edge[1])
                new_edges.append((edge[0], sub))


    edges = set(edges + new_edges)
    for edge in list(set(edges)):
        tree = record_format(tree, edge[0])
        tree = record_format(tree, edge[1])
        if edge[0] == edge[1]:
            continue
        if len(edge) == 2:
            tree.edge(edge[0], edge[1])
        elif len(edge) == 3:
            if edge[2] == "possible":
                tree.edge(edge[0] + ":here", edge[1] + ":here", label="♦", style="dashed")
            else:
                tree.edge(edge[0] + ":here", edge[1] + ":here", color=edge[2])

    for edge in edges:
        node1, node2 = edge[0], edge[1]
        if "start(search)" in node1:
            search_constants = [term for term in zip(node2[:-1].split("(")[1].split((",")),constants)]
            search_variables = [term for term in node2[:-1].split("(")[1].split((",")) if term[0].isupper() and term not in sum(search_constants,())]
            tree.node("start(search)", shape="Mdiamond", color="red",
                      label="start(search)\n\nConstants:\n" + "\n".join([constant[0] + " = " + constant[1] for constant in search_constants]) + "\n\nVariables:\n" + "\n".join(search_variables))
        if "boilerplate" in node1 or "in_text_table" in node1:
            tree.node(node1, color="brown")
        elif "type" in node1:
            tree.node(node1, color="orange")
        elif "valid" in node1:
            tree.node(node1, color="yellow")
        else:
            tree.node(node1, color="violet")
        if "boilerplate" in node2 or "in_text_table" in node2:
            tree.node(node2, color="brown")
        elif "keyword" in node2:
            tree.node(node2, color="blue")
        elif "type" in node2:
            tree.node(node2, color="orange")
        elif "valid" in node2:
            tree.node(node2, color="yellow")
        elif "(" not in node2:
            tree.node(node2, color="darkviolet")
        else:
            tree.node(node2, color="green")

    print(tree.source)
    tree.node_attr = {'fixedsize': 'false', 'width': '2.5', 'height': '3', 'fontsize': '12.0'}
    tree.render(r'', view=True)


def rules_to_graph(kb):
    tree = graphviz.Digraph(format='png')

    rules = [key for key in kb.db.keys() if key != '']

    edges = []
    for rule in rules:
        for instance in kb.db[rule]['facts']:
            for rh in instance.rhs:
                edges.append((instance.lh.f, rh.f))
                if any(term == term.lower() for term in rh.terms):
                    print(rh.f)
                    for rule in rules:
                        if rh.predicate == rule.split("(") and len(rh.terms) == len(rule.split(",")):
                            edges.append((rh.f, rule))

    tree.edges(set(edges))
    tree.node_attr = {'fixedsize': 'false'}
    tree.render(r'', view=True)



def test(query):
    kb = pl.KnowledgeBase("processed_trilodocs")
    kb.from_file(facts_file)
    kb.from_file(wizard_facts_file)
    kb.from_file(constant_facts_file)
    kb.from_file(rules_file)
    kb.clear_cache()
    try:
        constants = [term for term in query[:-1].split("(")[1].split((",")) if term[0].islower()]
        q, path= kb.query(pl.Expr(query),show_path=True)
        path_to_tree(path, constants)
        print(q)
    except:
        q = kb.query(pl.Expr(query), show_path=True)
        print(q)


def record_format(tree, name):
    try:
        predicate, terms = name.split("(")
        terms = terms.split(")")[0].split(",")
        label = '<here> ' + predicate + "|{" + "|".join(terms) + "}"
        tree.node(name, label, shape='record')
        return tree
    except:
        tree.node(name)
        return tree



colors = ["black", "green", "red", "blue", "yellow", "orange", "violet", "cyan","magenta"]
def rules_to_graph(kb):
    tree = graphviz.Digraph(format='png')
    rules = [key for key in kb.db.keys() if key != '']
    instances = [item.lh.f for rule in rules for item in kb.db[rule]['facts']]

    edges = []
    for rule in rules:
        for instance in kb.db[rule]['facts']:
            # catch recursive rule and denote possible edges
            if instance.lh.f in [rh.f for rh in instance.rhs]:
                for rh in instance.rhs:
                    edges.append((instance.lh.f, rh.f, "possible"))
                continue

            instance_index = list(kb.db[rule]['facts']).index(instance)
            for rh in instance.rhs:
                edges.append((instance.lh.f, rh.f, colors[instance_index]))

                # catch overspecified rules and conect them with abstract rules
                if any(term == term.lower() for term in rh.terms):
                    for cont_instance in instances:
                        if rh.predicate == cont_instance.split("(")[0] \
                                and len(rh.terms) == len(cont_instance.split(",")) \
                                and cont_instance.split("(")[1] != cont_instance.split("(")[1].lower():
                            # check that specification is not replaced
                            terms_rh = rh.f.split("(")[1].split(",")
                            terms_inst = cont_instance.split("(")[1].split(",")
                            for i in range(len(terms_inst)):
                                if (terms_inst[i] == terms_inst[i].lower() and terms_rh[i] == terms_rh[i].lower()):
                                    same_specs = True
                                    break
                                else:
                                    same_specs = False
                            if not same_specs: edges.append((rh.f, cont_instance))

                # catch underspecified rules and connect them with their specified instance
                if rh.f.split("(")[0] in rules and any(item != item.lower() for item in rh.f.split("(")[1].split(",")):
                    corr_instances = [instance for instance in instances if
                                      rh.f.split("(")[0] == instance.split("(")[0]
                                      and len(rh.f.split(",")) == len(instance.split(","))
                                      and any(item == item.lower() for item in instance.split("(")[1].split(","))]
                    for corr_instance in corr_instances:
                        # check that specification is not replaced
                        terms_rh = rh.f.split("(")[1].split(",")
                        terms_inst = corr_instance.split("(")[1].split(",")
                        for i in range(len(terms_inst)):
                            if (terms_inst[i] == terms_inst[i].lower() and terms_rh[i] == terms_rh[i].lower()):
                                same_specs = True
                                break
                            else:
                                same_specs = False
                        if not same_specs: edges.append((rh.f, corr_instance))


    for edge in list(set(edges)):
        tree = record_format(tree, edge[0])
        tree = record_format(tree, edge[1])
        if edge[0] == edge[1]:
            continue
        if len(edge) == 2:
            tree.edge(edge[0], edge[1])
        elif len(edge) == 3:
            if edge[2] == "possible":
                tree.edge(edge[0] + ":here", edge[1] + ":here", label="♦", style="dashed")
            else:
                tree.edge(edge[0] + ":here", edge[1] + ":here", color=edge[2])

    for edge in edges:
        node1, node2 = edge[0], edge[1]
        if "boilerplate" in node1 or "in_text_table" in node1:
            tree.node(node1, color="brown")
        elif "type" in node1:
            tree.node(node1, color="orange")
        elif "valid" in node1:
            tree.node(node1, color="yellow")
        else:
            tree.node(node1, color="violet")
        if "boilerplate" in node2 or "in_text_table" in node2:
            tree.node(node2, color="brown")
        elif "keyword" in node2:
            tree.node(node2, color="blue")
        elif "type" in node2:
            tree.node(node2, color="orange")
        elif "valid" in node2:
            tree.node(node2, color="yellow")
        elif "(" not in node2:
            tree.node(node2, color="darkviolet")
        else:
            tree.node(node2, color="green")
    tree.node_attr = {'fixedsize': 'false'}
    tree.render(r'', view=True)






def count_graph_rules():
    kb = pl.KnowledgeBase("processed_trilodocs")
    kb.from_file(rules_file)

    #tree = graphviz.Digraph(format='png')
    rules = [key for key in kb.db.keys() if key != '']
    instances = [item.lh.f for rule in rules for item in kb.db[rule]['facts']]
    facts = []
    for rule in rules:
        for instance in kb.db[rule]['facts']:
            for fact in instance.rhs:
                facts.append(fact.f)

    ### count number of occurrences
    all_queries = set(instances + facts)
    count_dict = {}
    kb.from_file(facts_file)
    kb.from_file(wizard_facts_file)
    kb.from_file(constant_facts_file)

    for query in all_queries:
        if query.startswith("/*"):
            continue
        try:
            q = kb.query(pl.Expr(query))
        except:
            q = []
        try:
            prob_filter_q = [item for item in q if 'No' != item]
            count_dict[query] = query + "\nCount " + str(len(set(prob_filter_q)))
        except:
            prob_filter_q = [item for item in q if 'No' not in item.values()]
            count_dict[query] = query + "\nCount " + str(len(set(frozenset(d.items()) for d in prob_filter_q)))

    del facts
    ### draw rules graph
    tree = graphviz.Digraph(format='png')

    edges = []
    for rule in rules:
        for instance in kb.db[rule]['facts']:
            # catch recursive rule and denote possible edges
            if instance.lh.f in [rh.f for rh in instance.rhs]:
                for rh in instance.rhs:
                    edges.append((count_dict[instance.lh.f], count_dict[rh.f], "possible"))
                continue

            for rh in instance.rhs:
                edges.append((count_dict[instance.lh.f], count_dict[rh.f]))

                # catch overspecified rules and connect them with abstract rules
                if any(term == term.lower() for term in rh.terms):
                    for cont_instance in instances:
                        if rh.predicate == cont_instance.split("(")[0] \
                                and len(rh.terms) == len(cont_instance.split(",")) \
                                and cont_instance.split("(")[1] != cont_instance.split("(")[1].lower():
                            # check that specification is not replaced
                            terms_rh = rh.f.split("(")[1].split(",")
                            terms_inst = cont_instance.split("(")[1].split(",")
                            for i in range(len(terms_inst)):
                                if (terms_inst[i] == terms_inst[i].lower() and terms_rh[i] == terms_rh[i].lower()):
                                    same_specs = True
                                    break
                                else:
                                    same_specs = False
                            if not same_specs: edges.append((count_dict[rh.f], count_dict[cont_instance]))

                # catch underspecified rules and connect them with their specified instance
                if rh.f.split("(")[0] in rules and any(item != item.lower() for item in rh.f.split("(")[1].split(",")):
                    corr_instances = [instance for instance in instances if
                                      rh.f.split("(")[0] == instance.split("(")[0]
                                      and len(rh.f.split(",")) == len(instance.split(","))
                                      and any(item == item.lower() for item in instance.split("(")[1].split(","))]
                    for corr_instance in corr_instances:
                        # check that specification is not replaced
                        terms_rh = rh.f.split("(")[1].split(",")
                        terms_inst = corr_instance.split("(")[1].split(",")
                        for i in range(len(terms_inst)):
                            if (terms_inst[i] == terms_inst[i].lower() and terms_rh[i] == terms_rh[i].lower()):
                                same_specs = True
                                break
                            else:
                                same_specs = False
                        if not same_specs: edges.append((count_dict[rh.f], count_dict[corr_instance]))

    for edge in list(set(edges)):
        if edge[0] == edge[1]:
            continue
        if len(edge) == 2:
            tree.edge(edge[0], edge[1])
        elif len(edge) == 3:
            if edge[2] == "possible":
                tree.edge(edge[0], edge[1], label="♦", style="dashed")

    for edge in edges:
        node1, node2 = edge[0], edge[1]
        if "boilerplate" in node1 or "in_text_table" in node1:
            tree.node(node1, color="brown")
        elif "type" in node1:
            tree.node(node1, color="orange")
        elif "valid" in node1:
            tree.node(node1, color="yellow")
        else:
            tree.node(node1, color="violet")
        if "boilerplate" in node2 or "in_text_table" in node2:
            tree.node(node2, color="brown")
        elif "keyword" in node2:
            tree.node(node2, color="blue")
        elif "type" in node2:
            tree.node(node2, color="orange")
        elif "valid" in node2:
            tree.node(node2, color="yellow")
        elif "(" not in node2:
            tree.node(node2, color="darkviolet")
        else:
            tree.node(node2, color="green")
    tree.node_attr = {'fixedsize': 'false'}
    tree.render(r'', view=True)