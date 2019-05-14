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
    mouseover: showdepartementPopup,
    mouseout: function(e) {
      map.closePopup()
    }
  });
}

// Popups
function showdepartementPopup(e) {
  var popup = L.popup()
    .setLatLng(e.latlng)
    .setContent(e.target.feature.properties.code + ' - ' + e.target.feature.properties.nom)
    .openOn(map);
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

  datas=[];

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
  })

  // Ajout des résultats obtenus dans la dataTable
  $("#table").DataTable().clear();
  $("#table").DataTable().rows.add(response["result"]).draw();
}

$(document).ready(initTable())
document.getElementById('loader').style.visibility='hidden';

// Envoi de la requête (cf. cqp.py)
myForm.addEventListener('submit', function(e) {
  $('form :submit').attr("disabled", true);
  document.getElementById('button').style.visibility='hidden';
  document.getElementById('loader').style.visibility='visible';
  $.ajax({
      type: "POST",
      url: "/query",
      data: {
        query: $("#query").val()
      },
      success: function(response) {
        response=JSON.parse(response);
        // Si la requête n'a pas donné de résultats
        if (response.result.length === 0) {
          alert("Aucun résultat pour cette requête");
          departements.eachLayer(function(layer) {
            layer.setStyle(defaultStyle);
          })
          $('#table').dataTable().fnClearTable();
        } else {
          data = responseDisplay(response);
        }
        document.getElementById('loader').style.visibility='hidden';
        document.getElementById('button').style.visibility='visible';
        $('form :submit').attr("disabled", false);
      }
    })
  e.preventDefault();
});
