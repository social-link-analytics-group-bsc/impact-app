function loadSummaryCards() {
    var endpoint = new URL("api/sci-impact/total-data", window.location.origin).href;
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            document.getElementById("total_pis").innerHTML = data.total_pis;
            sy_elements = document.getElementsByClassName("start_year");
            ey_elements = document.getElementsByClassName("end_year");
            for (i = 0; i < sy_elements.length; i++) {
                sy_elements[i].textContent = data.total_year_range[0];
                ey_elements[i].textContent = data.total_year_range[1];
            }
            document.getElementById("total_articles").innerHTML = data.total_articles;
            document.getElementById("articles_source").textContent = data.articles_source;
            document.getElementById("total_citations").innerHTML = data.total_citations;
            document.getElementById("citations_source").textContent = data.citations_source;
            document.getElementById("total_projects").innerHTML = data.total_projects;
            document.getElementById("projects_source").textContent = data.projects_source;
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function drawArticlesByYearChart(){
    var endpoint = new URL("api/sci-impact/articles-by-year", window.location.origin).href;
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            drawLineChart("articleYearChart", data.chart, false, false);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function drawCitationsByYearChart(){
    var endpoint = new URL("api/sci-impact/citations-by-year", window.location.origin).href;
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            drawLineChart("citationYearChart", data.chart, false, false);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function loadSciImpactSummaryCards(impact_obj) {
    if (impact_obj == '') {
        var endpoint = new URL("api/sci-impact/sci-impact-total-data", window.location.origin).href;
    }
    else {
        var endpoint = new URL("api/sci-impact/sci-impact-total-data/".concat(impact_obj), window.location.origin).href;
    }
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var sy_elements = document.getElementsByClassName("start_year");
            var ey_elements = document.getElementsByClassName("end_year");
            for (i = 0; i < sy_elements.length; i++) {
                sy_elements[i].textContent = data.sci_impact_year_range[0];
                ey_elements[i].textContent = data.sci_impact_year_range[1];
            }
            document.getElementById("total_articles").innerHTML = data.sci_impact_total_articles;
            document.getElementById("articles_source").textContent = data.articles_source;
            document.getElementById("total_citations").innerHTML = data.sci_impact_total_citations;
            document.getElementById("citations_source").textContent = data.citations_source;
            document.getElementById("avg_citations_article").innerHTML = data.sci_impact_citations_per_publications
            document.getElementById("scientific_impact_score").innerHTML = data.sci_impact_score
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function createSciImpactTable(impact_obj) {
    var table = document.querySelector("table");
    if (impact_obj == '') {
        var endpoint = new URL("api/sci-impact/sci-impact-table", window.location.origin).href;
    }
    else {
        var endpoint = new URL("api/sci-impact/sci-impact-table/".concat(impact_obj), window.location.origin).href;
    }
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var table_div = document.querySelector("table");
            // generate the header
            var thead = table_div.createTHead();
            var thead = table_div.createTHead();
            var row = thead.insertRow();
            for (i = 0; i < data.header.length; i++) {
                var th = document.createElement("th");
                var text = document.createTextNode(header[i]);
                th.appendChild(text);
                row.appendChild(th);
            }
            // generate the body
            for (var element of data.body) {
                var row = table_div.insertRow();
                for (key in element) {
                    var cell = row.insertCell();
                    var text = document.createTextNode(element[key]);
                    cell.appendChild(text);
                }
            }
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })


}