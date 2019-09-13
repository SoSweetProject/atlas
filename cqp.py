# -*- coding: utf-8 -*-

from flask import Flask, url_for, render_template, request
from collections import defaultdict,OrderedDict
from os.path import basename, splitext
from scipy.stats import hypergeom
from multiprocessing import Pool
from datetime import datetime
from CWB.CL import Corpus
from joblib import Memory
import PyCQP_interface
import pandas as pd
import numpy as np
import datetime
import logging
import random
import ujson
import ast
import sys
import re
import os

# log
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("static/cqp_logFile.log")
handler.setFormatter(logging.Formatter("%(asctime)s; %(levelname)s; %(message)s"))
logger.addHandler(handler)

# Récupération de la fréquence de l'ensemble des tokens (par date et departement)
file = open("static/allTokensDic", "r")
fAllTokens = file.read()
allTokensDc = ast.literal_eval(fAllTokens)

def cqpQuery(param_list) :
    try :
        pool = Pool(processes=None)
        query_result = pool.starmap(f, param_list)
    finally:
        pool.close()
        pool.join()

    return query_result

def f(corpus,query,diag):
    """
    Envoi de la requête à CQP et mise en forme des données récupérées
        entrée : nom du corpus sur lequel la requête sera effectuée, la requête en question, la fréquence totale de l'ensemble des tokens par département et par mois, et le booléen indiquant s'il est nécessaire de récupérer les données pour afficher le diagramme ou non
        sortie : les données nécessaires à la reconstruction de l'échantillon de résultats, le nombre d'occurrences dans le département, et le nombre d'occurrences par mois dans le département
    """

    registry_dir="/usr/local/share/cwb/registry"
    cqp=PyCQP_interface.CQP(bin='/usr/local/bin/cqp',options='-c -r '+registry_dir)
    #cqp=PyCQP_interface.CQP(bin='/usr/local/cwb/bin//cqp',options='-c -r '+registry_dir)
    corpus_name=splitext(basename(corpus))[0].upper()
    dep=corpus_name.split("_")[1].upper()
    if (re.match(r"^\d$",dep)) :
        dep="0"+dep
    else :
        dep=dep

    resultDep = {}

    """
        Envoi de la requête
        Récupération des résultats, sous la forme d'une liste (results) qui contient autant de listes que de résultats correspondant à la requête effectuée, ou une liste vide si aucun résultat.
        Ces listes permettent de récupérer l'emplacement du premier et du dernier élément des motifs correspondants dans le corpus.
    """
    cqp.Exec(corpus_name+";")

    try :

        dc = []

        # si on veut avoir le diagramme
        if diag=="true" :

            # Récupération des fréquence par date
            corpusDates = ["2014-06", "2014-07", "2014-08", "2014-09", "2014-10", "2014-11", "2014-12", "2015-01", "2015-02", "2015-03", "2015-04", "2015-05", "2015-06", "2016-02", "2016-03", "2016-04", "2016-05", "2016-06", "2016-07", "2016-08", "2016-09", "2016-10", "2016-11", "2016-12", "2017-01", "2017-02", "2017-03", "2017-04", "2017-05", "2017-06", "2017-07", "2017-08", "2017-09", "2017-10", "2017-11", "2017-12", "2018-01", "2018-02", "2018-03"]

            for d in corpusDates :
                cqp.Query(query+'::match.text_date="'+d+'.*" within text;')
                rsizeD=int(cqp.Exec("size Last;"))

                # Récupération de la fréquence de tous les tokens
                for dicAllTokensDc in allTokensDc :
                    if dicAllTokensDc["date"]==d and dicAllTokensDc["dep"]==dep :
                        freqAllTokens=dicAllTokensDc["freq"]

                dicDC={"date":d, "dep":dep, "freq":rsizeD, "freqAllTokens":freqAllTokens}
                dc.append(dicDC)

        cqp.Query(query+" within text;")
        rsize=int(cqp.Exec("size Last;"))
        results=cqp.Dump(first=0,last=20)
        #cqp.Exec("sort Last by word;")
        cqp.Terminate()
        # fermeture du processus CQP car sinon ne se ferme pas
        os.popen("kill -9 " + str(cqp.CQP_process.pid))

        resultDep[dep] = {"results":results, "nbTotalResults":rsize, "dc":dc}

        #print(dep)

        return resultDep

    except Exception as e :
        return False

def specificities(freqMotifParD,unit) :
    """
        Calcule la spécificité du motif dans chaque département/date
            - entrée : dataframe contenant la fréquence du motif recherché par département/date
            - sortie : dictionnaire contenant pour chaque département/date la spécificité du motif
    """

    freqTot = 31868064

    if unit == "dep" :
        freqTotParD = pd.read_hdf('./static/freqByDep.hdf', 'freqTokensByDep')
    else :
        freqTotParD = {'2014-06': 1281304, '2014-07': 3052340, '2014-08': 2071458, '2014-09': 3258429, '2014-10': 2884758, '2014-11': 2658469, '2014-12': 1775167, '2015-01': 1398820, '2015-02': 2525192, '2015-03': 858732, '2015-04': 2527688, '2015-05': 3756662, '2015-06': 886843, '2016-02': 74474, '2016-03': 116072, '2016-04': 114956, '2016-05': 100259, '2016-06': 59248, '2016-07': 72920, '2016-08': 106720, '2016-09': 99928, '2016-10': 66127, '2016-11': 89694, '2016-12': 83990, '2017-01': 110474, '2017-02': 114353, '2017-03': 131706, '2017-04': 50000, '2017-05': 8453, '2017-06': 111296, '2017-07': 145444, '2017-08': 159090, '2017-09': 131391, '2017-10': 257807, '2017-11': 182684, '2017-12': 153895, '2018-01': 119240, '2018-02': 131928, '2018-03': 140053}
        freqTotParD = pd.DataFrame(freqTotParD, index=["0"]).fillna(0)

    freqTotMotif = freqMotifParD.sum().sum()
    df_freqTotMotif = pd.DataFrame(freqMotifParD.sum(axis=1), columns=["0"])

    # Calcul de la fréquence attendue du motif dans chaque département/date
    expectedCounts = df_freqTotMotif.dot(freqTotParD)/freqTot
    specif = freqMotifParD.copy()

    """
        Pour chaque département/date, la spécificité du motif est calculée à partir de :
            - la fréquence du motif dans le département/date en question (à partir de freqMotifParD)
            - la fréquence totale de tous les tokens (freqTot)
            - la fréquence totale du motif (freqTotMotif)
            - la fréquence totale de tous les tokens dans le département/date (à partir de freqTotParD)
    """
    for d in freqMotifParD.columns :
        if (freqMotifParD.loc["freq",d]<expectedCounts.loc["freq",d]) :
            specif.loc["freq",d]=hypergeom.cdf(freqMotifParD.loc["freq",d], freqTot, freqTotMotif, freqTotParD.transpose().loc[d])
        else:
            specif.loc["freq",d]=1-hypergeom.cdf(freqMotifParD.loc["freq",d]-1, freqTot, freqTotMotif, freqTotParD.transpose().loc[d])

    specif=np.log10(specif)
    specif[freqMotifParD>=expectedCounts]=-specif[freqMotifParD>=expectedCounts]

    # Les valeurs qui ne sont pas entre -10 et 10 sont tronquées
    for d in specif :
        specif.loc[specif[d] > 10,d] = 10
        specif.loc[specif[d] < -10,d] = -10

    specif.rename(index={"freq":"specif"},inplace=True)
    specif = pd.DataFrame.to_dict(specif)

    #print(specif)

    return specif

# reconstitue les chaînes de caractères à partir d'une liste de tokens
def reconstituteString(tok_list) :
    no_space_before=[',','.',')',']']
    no_space_after=['(','[','\'']
    second=False
    reconstituted_string = ""
    for i,c in enumerate(tok_list) :
        if (i==len(tok_list)-1) :
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

# pour stocker les résultats des requêtes déjà effectuées
location = 'static/cachedir'
memory = Memory(location, verbose=0, compress=True)
cqpQuery = memory.cache(cqpQuery)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/departements', methods=["POST"])
def getData():
    return render_template("departements.json")

"""
    Comportement lors de la réception d'une requête
    -----------------------------------------------
    Entrée -> requête
    Sortie -> dictionnaire contenant :
        - Un extrait des résultats obtenus pour le motif recherché (liste de dictionnaires ; un dictionnaire par résultat) - resultAndSpec["result"]
        - la spécificité du motif dans chaque département (dictionnaire) - resultAndSpec["specif"]
        - le nombre total de résultats (int) - resultAndSpec["nbResults"]
        - le nombre d'occurrences par département (dictionnaire) - resultAndSpec["nbOccurrences"]
        - le nombre d'occurrences par mois et par département (liste de dictionnaires) - resultAndSpec["dc"]
"""
@app.route('/query', methods=["POST"])
def query():

    diag = request.form["diag"]
    query=request.form["query"]
    query_result=[]
    specByDate=[]
    allDc=[]

    corpus_list = [("dep_1",query,diag), ("dep_10",query,diag), ("dep_11",query,diag), ("dep_12",query,diag), ("dep_13",query,diag), ("dep_14",query,diag), ("dep_15",query,diag), ("dep_16",query,diag), ("dep_17",query,diag), ("dep_18",query,diag), ("dep_19",query,diag), ("dep_2",query,diag), ("dep_21",query,diag), ("dep_22",query,diag), ("dep_23",query,diag), ("dep_24",query,diag), ("dep_25",query,diag), ("dep_26",query,diag), ("dep_27",query,diag), ("dep_28",query,diag), ("dep_29",query,diag), ("dep_2a",query,diag), ("dep_2b",query,diag), ("dep_3",query,diag), ("dep_30",query,diag), ("dep_31",query,diag), ("dep_32",query,diag), ("dep_33",query,diag), ("dep_34",query,diag), ("dep_35",query,diag), ("dep_36",query,diag), ("dep_37",query,diag), ("dep_38",query,diag), ("dep_39",query,diag), ("dep_4",query,diag), ("dep_40",query,diag), ("dep_41",query,diag), ("dep_42",query,diag), ("dep_43",query,diag), ("dep_44",query,diag), ("dep_45",query,diag), ("dep_46",query,diag), ("dep_47",query,diag), ("dep_48",query,diag), ("dep_49",query,diag), ("dep_5",query,diag), ("dep_50",query,diag), ("dep_51",query,diag), ("dep_52",query,diag), ("dep_53",query,diag), ("dep_54",query,diag), ("dep_55",query,diag), ("dep_56",query,diag), ("dep_57",query,diag), ("dep_58",query,diag), ("dep_59",query,diag), ("dep_6",query,diag), ("dep_60",query,diag), ("dep_61",query,diag), ("dep_62",query,diag), ("dep_63",query,diag), ("dep_64",query,diag), ("dep_65",query,diag), ("dep_66",query,diag), ("dep_67",query,diag), ("dep_68",query,diag), ("dep_69",query,diag), ("dep_7",query,diag), ("dep_70",query,diag), ("dep_71",query,diag), ("dep_72",query,diag), ("dep_73",query,diag), ("dep_74",query,diag), ("dep_75",query,diag), ("dep_76",query,diag), ("dep_77",query,diag), ("dep_78",query,diag), ("dep_79",query,diag), ("dep_8",query,diag), ("dep_80",query,diag), ("dep_81",query,diag), ("dep_82",query,diag), ("dep_83",query,diag), ("dep_84",query,diag), ("dep_85",query,diag), ("dep_86",query,diag), ("dep_87",query,diag), ("dep_88",query,diag), ("dep_89",query,diag), ("dep_9",query,diag), ("dep_90",query,diag), ("dep_91",query,diag), ("dep_92",query,diag), ("dep_93",query,diag), ("dep_94",query,diag), ("dep_95",query,diag)]

    # Ici, autant de processus qu'indiqués en argument de Pool vont se partager les tâches (récupérer pour chaque département le résultat de la requête cqp)
    #start_time = datetime.datetime.now()
    query_result = cqpQuery(corpus_list)

    if query_result[0]==False :
        return "Erreur de syntaxe"

    else :
        allResults=[]

        freqParDepartement = defaultdict(int)
        # Construction d'un dataframe contenant la fréquence du motif recherché dans chaque département
        # récupération de l'ensemble des résultats dans une seule et même liste
        for depResult in query_result :
            for codeDep in depResult :
                # Récupération des fréquences par date et par département dans une même liste
                for e in depResult[codeDep]["dc"] :
                    allDc.append(e)
                freqParDepartement[codeDep]=depResult[codeDep]["nbTotalResults"]
                if depResult[codeDep]["results"]!=[['']] :
                    for result in depResult[codeDep]["results"] :
                        allResults.append({"dep":codeDep, "result":result})

        # calcul des spécificités
        freqParDepartementOrdered = OrderedDict(sorted(freqParDepartement.items(), key=lambda t: t[0]))
        df_queryFreq = pd.DataFrame(freqParDepartementOrdered, index=["freq"]).fillna(0)
        specif = specificities(df_queryFreq, "dep")

        resultsExtract = []
        registry_dir="/usr/local/share/cwb/registry"
        # Récupération des contextes gauche/droit + mise en forme, pour un extrait des résultats seulement (200 tirés au hasard)
        allResults_shuffle=[]
        random.shuffle(allResults)
        for i,dic in enumerate(allResults) :
            if i<200 :
                dep = dic["dep"]
                if (re.match(r"^0\d$",dep)) :
                    corpus_name = "dep_"+re.match(r"^0(\d)$",dep).group(1).lower()
                else :
                    corpus_name = "dep_"+dep.lower()

                r = dic["result"]

                corpus=Corpus(corpus_name,registry_dir=registry_dir);

                # permettra de récupérer par la suite le token, la POS ou le lemme correspondant à la position indiquée
                words=corpus.attribute("word","p")
                postags=corpus.attribute("pos","p")
                lemmas=corpus.attribute("lemma","p")

                sentences=corpus.attribute(b"text","s")
                id=corpus.attribute(b"text_id","s")
                dates=corpus.attribute(b"text_date","s")
                geo=corpus.attribute(b"text_geo","s")
                users=corpus.attribute(b"text_user","s")

                left_context=[]
                right_context=[]
                start=int(r[0])
                end=int(r[1])

                # Récupération de la position du début et de la fin du tweet dans lequel le motif a été trouvé
                s_bounds=sentences.find_pos(end)
                # Récupérarion de ses attributs (id, date, coordonnées et id de l'utilisateur)
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

                # Construction du dictionnaire qui contiendra les informations qui nous intéressent
                result={"id" : id_bounds[-1],
                        "date" : date_bounds[-1].decode("utf8").split("T")[0],
                        "geo" : coord,
                        "dep" : dep,
                        "user" : user_bounds[-1],
                        "hide_column" : "",
                        "left_context" : "",
                        "pattern" : "",
                        "right_context" : ""}

                lc_tokens = []
                lc_pos = []
                lc_lemmas = []
                rc_tokens = []
                rc_pos = []
                rc_lemmas = []

                # récupération du contexte gauche (tokens, pos et lemmes)
                for lp in left_context :
                    lc_tokens.append(words[lp])
                    lc_pos.append(postags[lp])
                    lc_lemmas.append(lemmas[lp])
                lc_tokens=reconstituteString(lc_tokens)
                lc_pos=" ".join(lc_pos)
                lc_lemmas=" ".join(lc_lemmas)

                # récupération du motif recherché (tokens, pos et lemmes)
                pattern_tokens=reconstituteString(words[start:end+1])
                pattern_pos=" ".join(postags[start:end+1])
                pattern_lemmas=" ".join(lemmas[start:end+1])

                # récupération du contexte droit (tokens, pos et lemmes)
                for rp in right_context :
                    rc_tokens.append(words[rp])
                    rc_pos.append(postags[rp])
                    rc_lemmas.append(lemmas[rp])
                rc_tokens=reconstituteString(rc_tokens)
                rc_pos=" ".join(rc_pos)
                rc_lemmas=" ".join(rc_lemmas)

                # mise en forme ici pour ne pas ajouter du temps de traitement côté client
                result["hide_column"]=lc_tokens[::-1]
                result["left_context"]="<span title=\""+lc_pos+"&#10;"+lc_lemmas+"\">"+lc_tokens+"</span>"
                result["pattern"]="<span title=\""+pattern_pos+"&#10;"+pattern_lemmas+"\">"+pattern_tokens+"</span>"
                result["right_context"]="<span title=\""+rc_pos+"&#10;"+rc_lemmas+"\">"+rc_tokens+"</span>"

                resultsExtract.append(result)

        #print(datetime.datetime.now()-start_time)
        if diag == "true" :
            # calcul des spécificités par date
            freqMotifParDate = {}
            for dic in allDc :
                if dic["date"] not in freqMotifParDate :
                    freqMotifParDate[dic["date"]] = dic["freq"]
                else :
                    freqMotifParDate[dic["date"]] += dic["freq"]
            freqMotifParDate = pd.DataFrame(freqMotifParDate, index=["freq"]).fillna(0)
            specByDate_temp = specificities(freqMotifParDate, "date")

            for e in specByDate_temp :
                specByDate.append({"date":e, "spec":specByDate_temp[e]["specif"]})

        resultAndSpec = {}
        resultAndSpec["result"]=resultsExtract
        resultAndSpec["specif"]=specif
        resultAndSpec["nbResults"]=int(df_queryFreq.sum().sum())
        resultAndSpec["nbOccurrences"]=freqParDepartement
        resultAndSpec["dc"]=allDc
        resultAndSpec["specifByDate"]=specByDate
        resultAndSpec=ujson.dumps(resultAndSpec)

        logger.info("ip : %s, query : %s, diag : %s."%(str(request.remote_addr),query, diag))

        return resultAndSpec
