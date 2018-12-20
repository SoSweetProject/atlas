# -*- coding: utf-8 -*-

from flask import Flask, url_for, render_template, request
from os.path import basename, splitext
from collections import defaultdict,OrderedDict
from scipy.stats import hypergeom
from CWB.CL import Corpus
import PyCQP_interface
import pandas as pd
import numpy as np
import ujson
import sys
import re

corpus_list = ["old_dep_1.vrt", "old_dep_10.vrt", "old_dep_11.vrt", "old_dep_12.vrt", "old_dep_13.vrt", "old_dep_14.vrt", "old_dep_15.vrt", "old_dep_16.vrt", "old_dep_17.vrt", "old_dep_18.vrt", "old_dep_19.vrt", "old_dep_2.vrt", "old_dep_21.vrt", "old_dep_22.vrt", "old_dep_23.vrt", "old_dep_24.vrt", "old_dep_25.vrt", "old_dep_26.vrt", "old_dep_27.vrt", "old_dep_28.vrt", "old_dep_29.vrt", "old_dep_2a.vrt", "old_dep_2b.vrt", "old_dep_3.vrt", "old_dep_30.vrt", "old_dep_31.vrt", "old_dep_32.vrt", "old_dep_33.vrt", "old_dep_34.vrt", "old_dep_35.vrt", "old_dep_36.vrt", "old_dep_37.vrt", "old_dep_38.vrt", "old_dep_39.vrt", "old_dep_4.vrt", "old_dep_40.vrt", "old_dep_41.vrt", "old_dep_42.vrt", "old_dep_43.vrt", "old_dep_44.vrt", "old_dep_45.vrt", "old_dep_46.vrt", "old_dep_47.vrt", "old_dep_48.vrt", "old_dep_49.vrt", "old_dep_5.vrt", "old_dep_50.vrt", "old_dep_51.vrt", "old_dep_52.vrt", "old_dep_53.vrt", "old_dep_54.vrt", "old_dep_55.vrt", "old_dep_56.vrt", "old_dep_57.vrt", "old_dep_58.vrt", "old_dep_59.vrt", "old_dep_6.vrt", "old_dep_60.vrt", "old_dep_61.vrt", "old_dep_62.vrt", "old_dep_63.vrt", "old_dep_64.vrt", "old_dep_65.vrt", "old_dep_66.vrt", "old_dep_67.vrt", "old_dep_68.vrt", "old_dep_69.vrt", "old_dep_7.vrt", "old_dep_70.vrt", "old_dep_71.vrt", "old_dep_72.vrt", "old_dep_73.vrt", "old_dep_74.vrt", "old_dep_75.vrt", "old_dep_76.vrt", "old_dep_77.vrt", "old_dep_78.vrt", "old_dep_79.vrt", "old_dep_8.vrt", "old_dep_80.vrt", "old_dep_81.vrt", "old_dep_82.vrt", "old_dep_83.vrt", "old_dep_84.vrt", "old_dep_85.vrt", "old_dep_86.vrt", "old_dep_87.vrt", "old_dep_88.vrt", "old_dep_89.vrt", "old_dep_9.vrt", "old_dep_90.vrt", "old_dep_91.vrt", "old_dep_92.vrt", "old_dep_93.vrt", "old_dep_94.vrt", "old_dep_95.vrt"]

# calcule les spécificités pour le motif recherché
def specificities(freqMotifParDep) :
    freqTot = 32241194
    freqTotParDep = pd.read_hdf('./static/freqByDep.hdf', 'freqTokensByDep')
    freqTotMotif = freqMotifParDep.sum().sum()
    df_freqTotMotif = pd.DataFrame(freqMotifParDep.sum(axis=1), columns=["0"])
    expectedCounts = df_freqTotMotif.dot(freqTotParDep)/freqTot
    specif = freqMotifParDep.copy()
    for dep in freqMotifParDep.columns :
        if (freqMotifParDep.loc["freq",dep]<expectedCounts.loc["freq",dep]) :
            specif.loc["freq",dep]=hypergeom.cdf(freqMotifParDep.loc["freq",dep], freqTot, freqTotMotif, freqTotParDep.transpose().loc[dep])
        else:
            specif.loc["freq",dep]=1-hypergeom.cdf(freqMotifParDep.loc["freq",dep]-1, freqTot, freqTotMotif, freqTotParDep.transpose().loc[dep])
    specif=np.log10(specif)
    specif[freqMotifParDep>=expectedCounts]=-specif[freqMotifParDep>=expectedCounts]
    for dep in specif :
        specif.loc[specif[dep] > 10,dep] = 10
        specif.loc[specif[dep] < -10,dep] = -10
    specif.rename(index={"freq":"specif"},inplace=True)
    specif = pd.DataFrame.to_dict(specif)
    return specif

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

    freqParDepartement = defaultdict(int)
    for dep in corpus_list :
        n = re.match(r".*_(\d+[ab]?)\.vrt",dep)
        dep = n.group(1)
    if (re.match(r"^\d$",dep)) :
        dep="0"+dep
        freqParDepartement[dep.upper()]

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
                        "dep" : corpus_name.split("_")[2],
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

    # calcul des spécificités
    for r in query_result :
        if (re.match(r"^\d$",r["dep"])) :
            dep="0"+r["dep"]
        else :
            dep=r["dep"]
        freqParDepartement[dep]+=1
    freqParDepartementOrdered = OrderedDict(sorted(freqParDepartement.items(), key=lambda t: t[0]))

    df_queryFreq = pd.DataFrame(freqParDepartementOrdered, index=["freq"]).fillna(0)
    specif = specificities(df_queryFreq)

    # conversion au format json

    resultAndSpec = {}
    resultAndSpec["result"]=query_result
    resultAndSpec["specif"]=specif
    resultAndSpec=ujson.dumps(resultAndSpec)

    return resultAndSpec
