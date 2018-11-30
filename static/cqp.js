var myForm = document.getElementById('form');

function initTable() {
  var table = $("#table").DataTable({
    "bFilter": false,
    "bInfos": false,
    columns: [{
        data: "left_context"
      },
      {
        data: "pattern"
      },
      {
        data: "right_context"
      },
    ],
    "pageLength": 20,
    "bLengthChange": false
  });
}

function responseDisplay(response) {

  response=JSON.parse(response);
  datas=[];

  for (element in response) {

    result={};

    patternTokens=patternTokens=response[element]["query_result"]["tokens_reconstituted"]["pattern"];
    lcTokens=response[element]["query_result"]["tokens_reconstituted"]["left_context"];
    rcTokens=response[element]["query_result"]["tokens_reconstituted"]["right_context"];

    patternPos=response[element]["query_result"]["pos"]["pattern"].join(" ");
    lcPos=response[element]["query_result"]["pos"]["left_context"].join(" ");
    rcPos=response[element]["query_result"]["pos"]["right_context"].join(" ");

    patternLemmas=response[element]["query_result"]["lemmas"]["pattern"].join(" ");
    lcLemmas=response[element]["query_result"]["lemmas"]["left_context"].join(" ");
    rcLemmas=response[element]["query_result"]["lemmas"]["right_context"].join(" ");

    if (document.getElementById("tokens").checked) {
      result = {"left_context":"<span title=\""+lcPos+"&#10;"+lcLemmas+"\">"+lcTokens+"</span>",
                "pattern":"<span title=\""+patternPos+"&#10;"+patternLemmas+"\">"+patternTokens+"</span>",
                "right_context":"<span title=\""+rcPos+"&#10;"+rcLemmas+"\">"+rcTokens+"</span>"};
    }

    if (document.getElementById("pos").checked) {
      result = {"left_context":"<span title=\""+lcTokens+"&#10;"+lcLemmas+"\">"+lcPos+"</span>",
                "pattern":"<span title=\""+patternTokens+"&#10;"+patternLemmas+"\">"+patternPos+"</span>",
                "right_context":"<span title=\""+rcTokens+"&#10;"+rcLemmas+"\">"+rcPos+"</span>"};
    }

    if (document.getElementById("lemmes").checked) {
      result = {"left_context":"<span title=\""+lcPos+"&#10;"+lcTokens+"\">"+lcLemmas+"</span>",
                "pattern":"<span title=\""+patternPos+"&#10;"+patternTokens+"\">"+patternLemmas+"</span>",
                "right_context":"<span title=\""+rcPos+"&#10;"+rcTokens+"\">"+rcLemmas+"</span>"};
    }

    datas.push(result);

  }

  $("#table").DataTable().clear();
  $("#table").DataTable().rows.add(datas).draw();
}

$(document).ready(initTable())

myForm.addEventListener('submit', function(e) {
  $.ajax({
      type: "POST",
      url: "/query",
      data: {
        query: $("#query").val()
      },
      success: function(response) {
        if (response == "[]") {
          alert("Aucun résultat pour cette requête");
        } else {
          data = responseDisplay(response);
        }
      }
    })
  e.preventDefault();
});
