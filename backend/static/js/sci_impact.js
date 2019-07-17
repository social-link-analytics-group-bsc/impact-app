function loadSummaryCards() {
    var endpoint = "/api/sci-impact/total-data";
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
    var endpoint = "/api/sci-impact/articles-by-year";
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var dataToDraw = {};
            dataToDraw.labels = data.years;
            dataToDraw.datasets = [];
            dataToDraw.datasets.push({
                "data": data.articles_by_year,
                "label": "Articles",
                "color": "#4285F4",
                "fill": false
            });
            drawLineChart("articleYearChart", dataToDraw, false, false);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function drawCitationsByYearChart(){
    var endpoint = "/api/sci-impact/citations-by-year";
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var dataToDraw = {};
            dataToDraw.labels = data.years;
            dataToDraw.datasets = [];
            dataToDraw.datasets.push({
                "data": data.citations_by_year,
                "label": 'Citations',
                "color": '#17a2b8',
                "fill": false
            });
            drawLineChart("citationYearChart", dataToDraw, false, false);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function loadSciImpactSummaryCards(impact_obj) {
    var endpoint = "/api/sci-impact/sci-impact-total-data";
    if (impact_obj != '') {
        endpoint = endpoint.concat(impact_obj);
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
            document.getElementById("dh-title").innerHTML = data.impact_obj_name;
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
    var endpoint = "/api/sci-impact/sci-impact-table";
    if (impact_obj != '') {
        endpoint = endpoint.concat(impact_obj);
    }
    $('#impactTable').DataTable( {
        "ajax":  {
            url: endpoint,
            dataSrc: 'body'
        },
        "columns": [
            { "data": "year" },
            { "data": "publications" },
            { "data": "citations" },
            { "data": "citations_per_publications" },
            { "data": "prop_not_cited_publications" },
            { "data": "prop_self_citations" },
            { "data": "avg_field_citations" },
            { "data": "impact_field" },
            { "data": "prop_publications_year" },
            { "data": "weighted_impact_field" },
        ]
    } );
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            document.getElementById("table_total_articles").innerHTML = data.foot.total_publications
            document.getElementById("table_total_citations").innerHTML = data.foot.total_citations
            document.getElementById("table_total_impact").innerHTML = data.foot.total_impact + '<sup>a</sup>'
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    });
}

function drawAvgCitationsByYearChart(impact_obj){
    var endpoint = "/api/sci-impact/avg-citations-by-year";
    if (impact_obj != '') {
        endpoint = endpoint.concat(impact_obj);
    }
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var dataToDraw = {};
            dataToDraw.labels = data.years;
            dataToDraw.datasets = [];
            if (data.datasets.length == 2) {
                var chartOptions = {
                    "labels": ["Avg. citations per article", "Avg. citations per article in the field"],
                    "colors": ["#4285F4", "#292b2c"],
                    "lineType": [[],[20, 5]]  // solid, dashed
                };
            } else {
                var chartOptions = {
                    "labels": ["Avg. citations per article", "Avg. citations per article in the field",
                               "Avg. citations per article in the INB"],
                    "colors": ["#8e5ea2", "#292b2c", "#4285F4"],
                    "lineType": [[],[20, 5], []]  // solid, dashed
                };
            }
            for (i=0; i < data.datasets.length; i++) {
                dataToDraw.datasets.push({
                    "data": data.datasets[i],
                    "label": chartOptions.labels[i],
                    "color": chartOptions.colors[i],
                    "fill": false,
                    "lineType": chartOptions.lineType[i]
                });
            }
            drawLineChart("avgCitationsPerArticleYearChart", dataToDraw, true, false);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function drawAvgCitationsByYearPIsChart(impact_obj){
    var endpoint = "/api/sci-impact/avg-citations-by-year-pis";
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var dataToDraw = {};
            dataToDraw.labels = data.years;
            dataToDraw.datasets = [];
            var chartOptions = {
                "colors": ['#3e95cd', '#8e5ea2', '#3cba9f', '#e8c3b9', '#c45850', '#f0ad4e', '#d9534f',
                           '#a1204f', '#b8c05c', '#4a836d', '#292b2c'],
                "lineType": [[], [], [], [], [], [], [], [], [], [], [20, 5]]  // solid, dashed
            };
            for (i=0; i < data.datasets.length; i++) {
                dataToDraw.datasets.push({
                    "data": data.datasets[i],
                    "label": "Avg. citations per article of ".concat(data.dataset_names[i]),
                    "color": chartOptions.colors[i],
                    "fill": false,
                    "lineType": chartOptions.lineType[i]
                });
            }
            drawLineChart("avgCitationsPerArticlePIsYearChart", dataToDraw, true, false);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data);
        }
    })
}

function createPIPapersTable(impact_obj) {
    var endpoint = "/api/sci-impact/articles-table/";
    if (impact_obj != '') {
        endpoint = endpoint.concat(impact_obj);
    }
    $('#articlesTable').DataTable( {
        "ajax":  {
            url: endpoint,
            dataSrc: 'body'
        },
        "columns": [
            { "data": "year" },
            { "data": "title" },
            { "data": "citations" }
        ]
    } );

}