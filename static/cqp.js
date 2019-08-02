var myForm = document.getElementById('form');
var departements;
var stat = false;
var specif;
var data;
var freq;
var dep;

// Style des départements sur la carte par défaut
var defaultStyle = {
  weight: 1,
  color: '#77af75',
  fillColor: '#77af75',
  dashArray: '',
  fillOpacity: 0.3
}

// Mise en place de la carte
var map = L.map("map").setView([46.4, 2.35], 6);
var mapboxAccessToken = 'pk.eyJ1Ijoic2F0aWxsb3ciLCJhIjoiY2prYjhsenI2Mnl2dDNycXFxdXQ1YWxpNyJ9.ah5XcUxTiKF4xWs8CKLPrQ';
L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 8,
  minZoom: 5,
  id: 'mapbox.light',
  accessToken: mapboxAccessToken
}).addTo(map);

// Récupération et ajout des départements
$.ajax({
  method: "POST",
  url: "/departements",
  dataType: "json",
  success: function(response) {
    departements = L.geoJson(response, {
      onEachFeature: onEachFeature,
      style: getDefaultStyle
    });
    departements.addTo(map);
  }
});

// apparence par défaut
function getDefaultStyle(e) {
  return defaultStyle;
}

// Indication de ce qu'il se passe au survol de la souris sur les départements
function onEachFeature(feature, layer) {
  layer.on({
    mouseover: function(e) {
      var popup = L.popup()
        .setLatLng(e.latlng)
        .setContent(e.target.feature.properties.code + ' - ' + e.target.feature.properties.nom)
        .openOn(map);
    },
    mouseout: function(e) {
      map.closePopup()
    }
  });
}

// Retourne la couleur associée à la spécificité indiquée
function color(s) {
  colors = ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f'];
  return colors[parseInt((s + 10) / 2)]
}

// Légende de la carte
var legend = L.control({
  position: 'topright',
  id: 'legend'
});
legend.onAdd = function(map) {
  var div = L.DomUtil.create('div', 'info legend'),
    grades = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10];
  div.id = 'legend'
  div.innerHTML = "<b>Overused</b><br>";
  for (var i = 0; i < grades.length; i++) {
    div.innerHTML +=
      '<i style="background:' + color(grades[i]) + '"></i> <p> ' +
      grades[i]+' </p>';
  }
  div.innerHTML += "<b>Underused</b>";
  return div;
};
legend.addTo(map);

// Initialisation de la dataTable qui contiendra les résultats de la requête
function initTable() {
  var table = $("#table").DataTable({
    "bFilter": false,
    "bInfos": false,
    columns: [{
        data:"hide_column",
        visible: false
      },
      {
        orderData: [0],
        data: "left_context",
        width: "37%"
      },
      {
        data: "pattern",
        width: "20%"
      },
      {
        data: "right_context",
        width: "37%"
      },
      {
        data: "dep",
        width: "5%"
      },
    ],
    "pageLength": 20,
    "bLengthChange": false
  });
}

// Traitement de la réponse
function responseDisplay(response) {
  nbOccurrences=response["nbResults"]
  // Création et affichage du diagramme en bâtons du nombre d'occurrences par date
  document.getElementById("diagramme").style.display='block'
  var dics = response["dc"]
  var chart = dc.barChart("#freqByMonth");

    dics.forEach(function (d) {
      d.date = d3.timeParse("%Y-%m")(d.date);
      d.freq = +d.freq;
      d.dep = d.dep;
      d.freqAllTokens = +d.freqAllTokens;
  });

  var occXFil = crossfilter(dics);
  var dateDim = occXFil.dimension(function(d) {
      return d.date;
  });
  var depDim = occXFil.dimension(function(d) {
      return d.dep;
  });
  var occPerMonth = dateDim.group().reduceSum(function(d) {
    return d.freq;
  });
  var occPerDep = depDim.group().reduceSum(function(d) {
    return d.freq;
  });
  var occPerDepAllTokens = depDim.group().reduceSum(function(d) {
    return d.freqAllTokens;
  });
  var totalOcc = occXFil.groupAll().reduceSum(function(d) {
     return d.freq;
  }).value();

  chart
    .dimension(dateDim)
    .group(occPerMonth)
    .x(d3.scaleTime().domain([new Date(2014, 4, 1), new Date(2018, 3, 31)]))
    .xUnits(function() {return 100})
    .colors(d3.scaleOrdinal().domain(["higher","lower"])
                            .range(["#955467","#597493"]))
    .colorAccessor(function(d) {
        if(d.value > totalOcc/39) {
          return "higher";
        } else {
          return "lower";
        }
      })
    .brushOn(true)
    .yAxisLabel("nombre d'occurrences")
    .margins({left: 50, top: 20, right: 10, bottom: 20})
    .controlsUseVisibility(true);

  dc.renderAll()

  // pour la période séléctionnée, calcul des spécificités pour chaque département :
  chart.on('filtered', function(chart) {
    var selectionOccPerDep = occPerDep.top(Infinity)
    var selectionOccPerDepAllTokens = occPerDepAllTokens.top(Infinity)
    var specifByDep = {};
    var freqByDep = {};
    for(var i=0; i < selectionOccPerDep.length; i++) {
      freqByDep[selectionOccPerDep[i].key]=selectionOccPerDep[i].value
      dep = selectionOccPerDep[i].key;
      // Récupération de la fréquence totale du motif
      K = occXFil.groupAll().reduceSum(function(d){return d.freq;}).value();
      // Récupération de la fréquence du motif dans le département
      k = selectionOccPerDep[i].value;
      // Récupératin de la fréquence totale de tous les tokens
      N = occXFil.groupAll().reduceSum(function(d){return d.freqAllTokens;}).value();
      // Récupération de la fréquence de tous les tokens dans le département
      n = _.findWhere(selectionOccPerDepAllTokens, {key: dep})["value"];
      // Calcul de la spécificité
      if (k > n * K / N) {
        specif = Math.abs(Math.log10(jStat.hypgeom.pdf(k, N, K, n)))
        if (specif > 10) {
          specif=10
        }
      } else {
        specif = -Math.abs(Math.log10(jStat.hypgeom.pdf(k, N, K, n)))
        if (specif < -10) {
          specif=-10;
        }
      }
      specifByDep[dep.toString()]=specif;
    }
    nbOccurrencesSelection = Object.values(freqByDep).reduce((a, b) => a + b);

    // Affichage du nombre d'occurences dans la sélection
    document.getElementById("nbOccurrences").innerHTML = ""
    document.getElementById("nbOccurrences").append(new Intl.NumberFormat().format(response["nbResults"])+" occurrences dans le corpus ("+nbOccurrencesSelection+" dans la sélection)");

    // Coloration de la carte en fonction des spécificités du motif recherché par département et dans la période sélectionnée
    departements.eachLayer(function(layer) {
      style = {
        fillColor: color(specifByDep[layer.feature.properties.code]),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
      };
      layer.setStyle(style);
      layer.on({
        mouseover: function(e) {
          var popup = L.popup()
            .setLatLng(e.latlng)
            .setContent("<dt>"+e.target.feature.properties.code +' - '+ e.target.feature.properties.nom +'</dt><dl>'+ freqByDep[e.target.feature.properties.code] +' occurrences</dl>')
            .openOn(map);
        },
        mouseout: function(e) {
          map.closePopup()
        }
      });
    })
  });

  document.getElementById("resetDiagramme").onclick = function () {
    resetDiagramme(chart,nbOccurrences);
  };

  datas=[];

  // affichade du nombre d'occurrences trouvées
  document.getElementById("nbOccurrences").innerHTML = ""
  document.getElementById("nbOccurrences").append(nbOccurrences+" occurrences dans le corpus");

  // Coloration de la carte en fonction des spécificités du motif recherché par département
  departements.eachLayer(function(layer) {
    style = {
      fillColor: color(response["specif"][layer.feature.properties.code]["specif"]),
      weight: 2,
      opacity: 1,
      color: 'white',
      dashArray: '3',
      fillOpacity: 0.7
    };
    layer.setStyle(style);
    layer.on({
      mouseover: function(e) {
        var popup = L.popup()
          .setLatLng(e.latlng)
          .setContent("<dt>"+e.target.feature.properties.code +' - '+ e.target.feature.properties.nom +'</dt><dl>'+ response["nbOccurrences"][e.target.feature.properties.code] +' occurrences</dl>')
          .openOn(map);
      },
      mouseout: function(e) {
        map.closePopup()
      }
    });
  })

  // Ajout des résultats obtenus dans la dataTable
  $("#table").DataTable().clear();
  $("#table").DataTable().rows.add(response["result"]).draw();
}

// enlever le filtre du diagramme
function resetDiagramme(chart,nbOccurrences) {
  chart.filterAll();
  dc.redrawAll();
  document.getElementById("nbOccurrences").innerHTML = ""
  document.getElementById("nbOccurrences").append(nbOccurrences+" occurrences dans le corpus");
}

$(document).ready(initTable())
document.getElementById('loader').style.visibility='hidden';

// afficher l'aide
$(document).ready(function(){
    $('#img').click(function(){
      $('#aide').slideToggle();
      $('#memo').slideUp();
      $('#pos').slideUp();
  });
});
// afficher la liste des pos
$(document).ready(function(){
    $('#viewPos').click(function(){
      document.getElementById('memo').style.display=null;
      document.getElementById('pos').style.display="inline";
  });
});
//afficher le memo
$(document).ready(function(){
    $('#viewMemo').click(function(){
      document.getElementById('memo').style.display="inline";
      document.getElementById('pos').style.display=null;
  });
});

// Envoi de la requête (cf. cqp.py)
myForm.addEventListener('submit', function(e) {
  $('form :submit').attr("disabled", true);
  document.getElementById('submitButton').style.visibility='hidden';
  document.getElementById('loader').style.visibility='visible';
  $.ajax({
      type: "POST",
      url: "/query",
      data: {
        query: $("#query").val()
      },
      success: function(response) {
        if (response=="Erreur de syntaxe") {
          alert("Erreur de syntaxe dans la requête");
          departements.eachLayer(function(layer) {
            layer.setStyle(defaultStyle);
            layer.on({
              mouseover: function(e) {
                var popup = L.popup()
                  .setLatLng(e.latlng)
                  .setContent(e.target.feature.properties.code + ' - ' + e.target.feature.properties.nom)
                  .openOn(map);
              },
              mouseout: function(e) {
                map.closePopup()
              }
            });
          })
          $('#table').dataTable().fnClearTable();
          document.getElementById("nbOccurrences").innerHTML = ""
          document.getElementById("diagramme").style.display='none'
        } else {
          response=JSON.parse(response);
          // Si la requête n'a pas donné de résultats
          if (response.result.length === 0) {
            alert("Aucun résultat pour cette requête");
            departements.eachLayer(function(layer) {
              layer.setStyle(defaultStyle);
              layer.on({
                mouseover: function(e) {
                  var popup = L.popup()
                    .setLatLng(e.latlng)
                    .setContent(e.target.feature.properties.code + ' - ' + e.target.feature.properties.nom)
                    .openOn(map);
                },
                mouseout: function(e) {
                  map.closePopup()
                }
              });
            })
            $('#table').dataTable().fnClearTable();
            document.getElementById("nbOccurrences").innerHTML = ""
            document.getElementById("diagramme").style.display='none'
          } else {
            data = responseDisplay(response);
          }
        }
        document.getElementById('loader').style.visibility='hidden';
        document.getElementById('submitButton').style.visibility='visible';
        $('form :submit').attr("disabled", false);
      }
    })
  e.preventDefault();
});
