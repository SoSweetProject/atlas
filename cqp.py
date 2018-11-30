# -*- coding: utf-8 -*-

from flask import Flask, url_for, render_template, request
from os.path import basename, splitext
from CWB.CL import Corpus
import PyCQP_interface
import ujson
import sys

corpus_list = ["dep_1.vrt", "dep_10.vrt", "dep_11.vrt", "dep_12.vrt", "dep_13.vrt", "dep_14.vrt", "dep_15.vrt", "dep_16.vrt", "dep_17.vrt", "dep_18.vrt", "dep_19.vrt", "dep_2.vrt", "dep_21.vrt", "dep_22.vrt", "dep_23.vrt", "dep_24.vrt", "dep_25.vrt", "dep_26.vrt", "dep_27.vrt", "dep_28.vrt", "dep_29.vrt", "dep_2a.vrt", "dep_2b.vrt", "dep_3.vrt", "dep_30.vrt", "dep_31.vrt", "dep_32.vrt", "dep_33.vrt", "dep_34.vrt", "dep_35.vrt", "dep_36.vrt", "dep_37.vrt", "dep_38.vrt", "dep_39.vrt", "dep_4.vrt", "dep_40.vrt", "dep_41.vrt", "dep_42.vrt", "dep_43.vrt", "dep_44.vrt", "dep_45.vrt", "dep_46.vrt", "dep_47.vrt", "dep_48.vrt", "dep_49.vrt", "dep_5.vrt", "dep_50.vrt", "dep_51.vrt", "dep_52.vrt", "dep_53.vrt", "dep_54.vrt", "dep_55.vrt", "dep_56.vrt", "dep_57.vrt", "dep_58.vrt", "dep_59.vrt", "dep_6.vrt", "dep_60.vrt", "dep_61.vrt", "dep_62.vrt", "dep_63.vrt", "dep_64.vrt", "dep_65.vrt", "dep_66.vrt", "dep_67.vrt", "dep_68.vrt", "dep_69.vrt", "dep_7.vrt", "dep_70.vrt", "dep_71.vrt", "dep_72.vrt", "dep_73.vrt", "dep_74.vrt", "dep_75.vrt", "dep_76.vrt", "dep_77.vrt", "dep_78.vrt", "dep_79.vrt", "dep_8.vrt", "dep_80.vrt", "dep_81.vrt", "dep_82.vrt", "dep_83.vrt", "dep_84.vrt", "dep_85.vrt", "dep_86.vrt", "dep_87.vrt", "dep_88.vrt", "dep_89.vrt", "dep_9.vrt", "dep_90.vrt", "dep_91.vrt", "dep_92.vrt", "dep_93.vrt", "dep_94.vrt", "dep_95.vrt"]

# reconstitue les chaînes de caractères à partir d'une liste de tokens
def reconstituteString(tok_list) :
    no_space_before=[',','.',')',']']
    no_space_after=['(','[','\'']
    second=False
    reconstituted_string = ""
    for c in tok_list :
        if (c==tok_list[-1]) :
            reconstituted_string+=c
        elif ((c=="'" or c=="\"")) :
            if (second==False) :
                reconstituted_string+=c
                second=True
            else :
                reconstituted_string+=c+" "
                second=False
        elif (tok_list[tok_list.index(c)+1]=="\"" or tok_list[tok_list.index(c)+1]=="'") :
            if (second) :
                reconstituted_string+=c
            else :
                reconstituted_string+=c+" "
        elif (tok_list[tok_list.index(c)+1] in no_space_before) :
            reconstituted_string+=c
        elif (c[-1] in no_space_after) :
            reconstituted_string+=c
        else :
            reconstituted_string+=c+" "
    return reconstituted_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=["POST"])
def query():
    query=request.form["query"]+";"
    query_result=[]

    registry_dir="/usr/local/share/cwb/registry"
    cqp=PyCQP_interface.CQP(bin='/usr/local/bin/cqp',options='-c -r '+registry_dir)

    for corpus in corpus_list :
        corpus_name=splitext(basename(corpus))[0].upper()

        # Envoi de la requête
        cqp.Exec(corpus_name+";")
        cqp.Query(query)
        cqp.Exec("sort Last by word;")
        rsize=int(cqp.Exec("size Last;"))
        results=cqp.Dump(first=0,last=rsize)
        cqp.Terminate()

        corpus=Corpus(corpus_name,registry_dir=registry_dir);
        words=corpus.attribute("word","p")
        postags=corpus.attribute("pos","p")
        lemmas=corpus.attribute("lemma","p")
        sentences=corpus.attribute(b"text","s")
        id=corpus.attribute(b"text_id","s")
        dates=corpus.attribute(b"text_date","s")
        geo=corpus.attribute(b"text_geo","s")
        users=corpus.attribute(b"text_user","s")

        id_query=0
        if (results!=[[""]]) :
            for line in results:
                id_query+=1
                left_context=[]
                right_context=[]
                start=int(line[0])
                end=int(line[1])

                s_bounds=sentences.find_pos(end)
                id_bounds=id.find_pos(end)
                date_bounds=dates.find_pos(end)
                geo_bounds=geo.find_pos(end)
                user_bounds=users.find_pos(end)

                coord = geo_bounds[-1].decode("utf8").split(", ")

                # récupération de la position des mots des contextes droit et gauche
                for pos in range(s_bounds[0],s_bounds[1]+1) :
                    if (pos<start) :
                        left_context.append(pos)
                    if (pos>end) :
                        right_context.append(pos)

                tokens_leftContext=[]
                tokens_rightContext=[]
                tokens_pattern=[]
                pos_leftContext=[]
                pos_rightContext=[]
                pos_pattern=[]
                lemmas_leftContext=[]
                lemmas_rightContext=[]
                lemmas_pattern=[]

                result={"id" : id_bounds[-1],
                        "date" : date_bounds[-1].decode("utf8"),
                        "geo" : coord,
                        "dep" : corpus_name.split("_")[1],
                        "user" : user_bounds[-1],
                        "query_result" : {
                            "tokens" : {
                                "left_context" : [],
                                "pattern" : [],
                                "right_context" : []},
                            "tokens_reconstituted" : {
                                "left_context" : "",
                                "pattern" : "",
                                "right_context" : ""},
                            "pos" : {
                                "left_context" : [],
                                "pattern" : [],
                                "right_context" : []},
                            "pos_reconstituted" : {
                                "left_context" : "",
                                "pattern" : "",
                                "right_context" : ""},
                            "lemmas" : {
                                "left_context" : [],
                                "pattern" : [],
                                "right_context" : []},
                            "lemmas_reconstituted" : {
                                "left_context" : "",
                                "pattern" : "",
                                "right_context" : ""}}}

                # construction de la liste qui contiendra l'ensemble des résultats de la requête
                query_result.append(result)

                # récupération du contexte gauche sous forme d'une liste de tokens, d'une liste de pos et d'une liste de lemmes
                for lp in left_context :
                    result["query_result"]["tokens"]["left_context"].append(words[lp])
                    result["query_result"]["pos"]["left_context"].append(postags[lp])
                    result["query_result"]["lemmas"]["left_context"].append(lemmas[lp])
                result["query_result"]["tokens_reconstituted"]["left_context"]=reconstituteString(result["query_result"]["tokens"]["left_context"])

                # récupération du motif recherché sous forme d'une liste de tokens, d'une liste de pos et d'une liste de lemmes
                result["query_result"]["tokens"]["pattern"]=words[start:end+1]
                result["query_result"]["tokens_reconstituted"]["pattern"]=reconstituteString(words[start:end+1])
                result["query_result"]["pos"]["pattern"]=postags[start:end+1]
                result["query_result"]["lemmas"]["pattern"]=lemmas[start:end+1]

                # récupération du contexte droit sous forme d'une liste de tokens, d'une liste de pos et d'une liste de lemmes
                for rp in right_context :
                    result["query_result"]["tokens"]["right_context"].append(words[rp])
                    result["query_result"]["pos"]["right_context"].append(postags[rp])
                    result["query_result"]["lemmas"]["right_context"].append(lemmas[rp])
                result["query_result"]["tokens_reconstituted"]["right_context"]=reconstituteString(result["query_result"]["tokens"]["right_context"])

    # conversion au format json
    query_result=ujson.dumps(query_result)

    return query_result
