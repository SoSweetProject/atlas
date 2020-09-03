# README
L'atlas a pour but de permettre l'observation des variations linguistiques en France métropolitaine dans un corpus d'environ 2,5 millions de tweets. Il donne ainsi la possibilité de rechercher un motif linguistique et de visualiser sa représentation dans les différents départements (s'il est sur ou sous-représenté dans un ou plusieurs d'entre eux par exemple), ainsi que son contexte d'utilisation.  

Le site est fait en python (avec Flask), et nécessite au préalable d’avoir cwb d’installé sur sa machine (*http://cwb.sourceforge.net/* ; pour indéxer un corpus, cf. *http://cwb.sourceforge.net/files/CWB_Encoding_Tutorial.pdf*). 

Pour faire tourner le site en local, lancer d’abord les commandes suivantes, dans l'ordre : 
* python3 -m venv venv
* source venv/bin/activate 
* pip install cython 
* export CWB_DIR=</chemin/vers/cwb>
* pip install -r requirements.txt 
* export FLASK_APP=cqp.py 
* export FLASK_ENV=development 
* venv/bin/flask run

## Contenu 

* **cqp.py** : contient donc toute la partie serveur du site. 
    1. **Envoi de la requête et récupération des résultats**. Lorsqu'une requête est effectuée sur le site, plusieurs processus vont envoyer simultanément cette requête à CQP (via  *https://pypi.org/project/cwb-python/*) dans chacun des départements (il y a un corpus par département, qui contient tous les tweets produits dans ce département). 
    Pour l'exemple, imaginons que nous faisons comme requête **"la" "plage"**.
    
        Le résultat renvoyé par CQP se présente de la façon suivante : chaque occurrence du motif recherché est représenté par une liste contenant l'emplacement du premier et du dernier mot correspondant à celui-ci dans le corpus, et nous avons donc une liste pour chaque occurrence trouvée. Dans un soucis de performance, nous ne récupérons que 20 résultats max par corpus (donc par département).
        En parallèle, nous récupérons également le nombre total d'occurrences trouvées dans chaque département.
        Pour chacun des départements nous nous retrouvons alors avec un résultat de cette forme : {'06': {'results': [['27529', '27530', '-1', '-1'], ['51971', '51972', '-1', '-1'], ['56323', '56324', '-1', '-1'], ['62013', '62014', '-1', '-1'], ['75919', '75920', '-1', '-1'], ['78800', '78801', '-1', '-1'], ['82388', '82389', '-1', '-1'], ['108491', '108492', '-1', '-1'], ['108923', '108924', '-1', '-1'], ['114653', '114654', '-1', '-1'], ['124999', '125000', '-1', '-1'], ['125058', '125059', '-1', '-1'], ['125464', '125465', '-1', '-1'], ['131091', '131092', '-1', '-1'], ['144367', '144368', '-1', '-1'], ['144563', '144564', '-1', '-1'], ['148353', '148354', '-1', '-1'], ['151836', '151837', '-1', '-1'], ['167288', '167289', '-1', '-1'], ['168710', '168711', '-1', '-1'], ['169464', '169465', '-1', '-1']], 'nbTotalResults': 71}}. Ici par exemple, le département dont le code est 06 (Alpes-Maritimes) contient au total 71 occurrences du motif "la plage", et la première occurence va du mot n°27529 au mot 27530 inclus. 
        
        Une fois tous les départements passés en revue, l'ensemble des résultats de chaque département est récupéré dans une liste. 
        
    2. **Calcul des spécificités**. À partir des résultats décrits ci-dessus, un dictionnaire contenant pour chaque département le nombre d'occurence du motif par département est créé (*freqParDepartement*), que l'on transforme en dataframe contenant donc en colonne le numéro des départements et en ligne le nombre d'occurrences trouvées dans chacun d'entre eux (*df_queryFreq*).

	   |      | 01 | 02 | 03 | 04 | 05 | 06 | etc. |  
	   |:---: |:--:|:--:|:--:|:--:|:--:|:--:| :--: |
	   | freq | 1  | 2  | 0  | 1  | 1  | 71 |      |  

	   Le département de l'Ain (01) contient par exemple ainsi seulement une occurrence de "la plage", comme les départements 04 et 05.
	
        C'est à partir de ce dataframe que l'on peut ensuite calculer pour chaque département le score de spécificité du motif recherché (fonction specificities()), ce qui nous indiquera si le motif recherché est sur ou sous représenté dans chacun des départements. Pour cela, nous avons également besoin : 
        - du dataframe précédemment décrit contenant pour chaque département le nombre d'occurrences du motif dans celui-ci (*freqMotifParDep*)
        - du nombre total de tokens dans l'ensemble du corpus, donc tous départements confondus (ici inscrit en dur dans le code, *freqTot*)
        - le nombre total d'occurrences du motif recherché tous départements confondus (*freqTotMotif*)
        - du nombre total de tokens dans chaque département (*freqTotParDep*), dataframe organisé de la même façon que *freqMotifParDep* (=*df_queryFreq*) récupéré à partir du fichier hdf *freqByDep.hdf*
        
        Pour calculer le score de spécificité du motif dans chaque département (donc pour voir s'il est sur ou sous représenté dans tel ou tel département), nous calculons d'abord le nombre d'occurrences attendus de celui-ci dans chaque département en multipliant le nombre total d'occurrences du motif tous départements confondus par le nombre total de mots dans le département, et en divisant ce nombre par le nombre total de mots tous départements confondus. Dans notres cas, le nombre attendu d'occurrences de "la plage" dans le département des Alpes-Maritimes serait donc de **23.481692** (1447*517150/31868064).
            
        C'est ensuite à partir de ce nombre, ainsi que du nombre de fois ou "la plage" apparait dans chacun des départements, du nombre total de tokens dans chacun des départements, et du nombre total de tokens dans le corpus que nous pouvons ensuite calculer le score de spécificité de "la plage" dans chacun des départements (pour plus de détails sur ce calcul, cf. *http://textometrie.enslyon.fr/html/doc/manual/0.7.9/fr/manual43.xhtml*). 
            
        Dans le cas du motif "la plage" par exemple, le score obtenu pour le département des Alpes-Maritimes sera de **10** (les résultats supérieurs à 10 ou inférieurs à -10 sont tronqués), donc "la plage" est sur-représenté dans ce département.

    3. **Reconstitution du tweet**. Afin d'avoir une idée du contexte d'utilisation du motif recherché, nous reconstituons à partir de la position dans le corpus de celui-ci ses contextes droit et gauche. Toujours dans un souci de performance, nous sélectionnons au hasard 200 des occurrences trouvées par CQP (pour rappel, nous ne disposons alors que des informations suivantes : le corpus (département) dans lequel se trouve l'occurrence en question, et sa position dans celui-ci). 
    Pour chacune de ces 200 occurrences, une requête est faite à CQP, afin de récupérer la position dans le corpus du début et de la fin des tweets dans lesquels elles se trouvent. À partir de cela, nous récupérons ensuite la position des mots du contexte droit et gauche (sous cette forme : [71468, 71469, 71470, 71471, 71472, 71473]), et à partir de ces positions, nous récupérons pour chacun des mots du contexte le token correpondant, ainsi que le lemme et la partie du discours. Le tweet est enfin reconstitué (fonction reconstituteString()) à partir de la liste des tokens.
    
    4. Au final, à partir de la requête effectuée au départ, nous nous retrouvons avec un objet au format JSON contenant trois éléments : 
        - **result** : liste de dictionnaires. Chaque dictionnaire correspond à une des occurrences du motif recherché et contient son contexte droit, son contexte gauche, le département auquel il appartient, etc. 
        - **specif** : dictionnaire contenant pour chaque département le score de spécificité du motif recherché dans celui-ci. 
        - **nbResults** : le nombre total d'occurrences du motif recherché.
        - **nbOccurrences** : dictionnaire contenant pour chaque département le nombre d'occurrence du motif recherché dans chacun d'entre eux. 
        
* **répertoire *static*** : 

    - **cqp.js** : envoi de la requête et récupération des résultats renvoyés par **cqp.py** (cf. point 4 ci-dessus) et les ajoute à la carte (*https://leafletjs.com/*) ainsi que dans le concordancier (*https://datatables.net/*) ; gère aussi les "animations" pour l'affichage du mémo et des parties du discours. 
    - **infoHover.png, info.png, favicon_32.png** : images pour la favicon et le bouton d'aide.
    - **freqByDep.hdf** : 
    - **cqp.css**

* **répertoire *templates*** : 
    - **departements.json** : contours des départements de France métropolitaine au format JSON. 
    - **index.html** 

* **requirements.txt** : contient la liste des librairies python à installer. 
* **PyCQP_interface.py** : version un peu modifiée (par rapport aux versions de python (par ex. précision de l'encodage, du type, vers l.86-94), essayer de remplacer *./venv/lib/python3.7/site-packages/PyCQP_interface.py* avec ce fichier si problème lors des requêtes à CQP. *(mv ./PyCQP_interface.py ./venv/lib/python3.7/site-packages/)*
