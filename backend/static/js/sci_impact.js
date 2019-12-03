function getBaseURL(server_subfolder) {
    var base_url = window.location.origin;
    if (server_subfolder != '') {
        server_subfolder = '/'.concat(server_subfolder);
        base_url = base_url.concat(server_subfolder);
    }
    return base_url;
}

function loadSummaryCards(server_subfolder) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/dashboard/total-data");
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
            console.log(error_data.responseText);
        }
    });
}

function drawArticlesByYearChart(server_subfolder){
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/articles-by-year");
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
            console.log(error_data.responseText);
        }
    })
}

function drawCitationsByYearChart(server_subfolder){
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/citations-by-year");
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
            console.log(error_data.responseText);
        }
    })
}

function loadSciImpactSummaryCards(impact_obj, server_subfolder) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/sci-impact-total-data/");
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
            document.getElementById("dh-title").innerHTML += ' ' + data.impact_obj_name;
            document.getElementById("total_articles").innerHTML = data.sci_impact_total_articles;
            document.getElementById("articles_source").textContent = data.articles_source;
            document.getElementById("total_citations").innerHTML = data.sci_impact_total_citations;
            document.getElementById("citations_source").textContent = data.citations_source;
            document.getElementById("avg_citations_article").innerHTML = data.sci_impact_citations_per_publications
            document.getElementById("scientific_impact_score").innerHTML = data.sci_impact_score
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data.responseText);
        }
    })
}

function createSciImpactTable(impact_obj, server_subfolder) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/sci-impact-table/");
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
            console.log(error_data.responseText);
        }
    });
}

function drawAvgCitationsByYearChart(impact_obj, server_subfolder){
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/avg-citations-by-year/");
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
            console.log(error_data.responseText);
        }
    })
}

function drawAvgCitationsByYearPIsChart(server_subfolder){
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/avg-citations-by-year-pis");
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
            console.log(error_data.responseText);
        }
    })
}

function createPIPapersTable(impact_obj, server_subfolder) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/sci-impact/articles-table/");
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


function generateSciImpactMenu(server_subfolder, impactObjs) {
    var researchersMenu = document.getElementById("researchers_menu");
    var institutionMenu = document.getElementById("institution_menu");
    var menuItem, menuSpan, menuI;
    var base_url = getBaseURL(server_subfolder);
    var url = base_url.concat("/", "dashboard/sci_impact/");
    for (i=0; i < impactObjs.length; i++) {
        menuItem = document.createElement("a");
        menuItem.href = url.concat(impactObjs[i].type, '_', impactObjs[i].id);
        if (impactObjs[i].type == 'scientist') {
            menuItem.className = "collapse-item";
            menuItem.innerHTML = impactObjs[i].name;
            researchersMenu.appendChild(menuItem);
        }
        if (impactObjs[i].type == 'institution') {
            menuItem.className = "nav-link";
            menuI = document.createElement("i");
            menuI.className = "fas fa-fw fa-university";
            menuItem.appendChild(menuI);
            menuSpan = document.createElement("span");
            menuSpan.innerHTML = impactObjs[i].name;
            menuItem.appendChild(menuSpan);
            institutionMenu.appendChild(menuItem);
        }
    }
}


function loadSocialImpactSummaryCards(server_subfolder) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/social-impact/projects-meta-data/");
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            var sy_elements = document.getElementsByClassName("start_year");
            var ey_elements = document.getElementsByClassName("end_year");
            for (i = 0; i < sy_elements.length; i++) {
                sy_elements[i].textContent = data.start_year;
                ey_elements[i].textContent = data.end_year;
            }
            document.getElementById("total_projects").innerHTML = data.total_projects;
            document.getElementById("project_source").innerHTML = data.projects_source;
            document.getElementById("active_projects").innerHTML = data.active_projects;
            document.getElementById("projects_with_impact").innerHTML = data.projects_with_impact;
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data.responseText);
        }
    })
}


function createProjectList(server_subfolder) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/", "api/social-impact/projects/");
     $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            // get impact column
            var target_name, target_end_point, targets, target_scores, target_score;
            for (i = 0; i < data.body_impact.length; i++) {
                targets = '';
                target_scores = '';
                for (j = 0; j < data.body_impact[i].impact_targets.length; j++) {
                    target_name = data.body_impact[i].impact_targets[j];
                    target_score = data.body_impact[i].impact_scores[j]
                    target_end_point = base_url.concat("/", "dashboard/social_impact/projects/impact/", data.body_impact[i].id, "/");
                    targets += target_name + '<br>';
                    target_scores += target_score + '<a href="' + target_end_point + '"> [more details]</a><br>';
                }
                data.body_impact[i].impact_on = targets;
                data.body_impact[i].impact_scores = target_scores;
            }
            $('#project_details_impact').DataTable( {
                "data": data.body_impact,
                "columns": [
                    { "width": "15%", "data": "name" },
                    { "width": "30%", "data": "description" },
                    { "width": "5%", "data": "status" },
                    { "width": "5%", "data": "start_date" },
                    { "width": "5%", "data": "end_date" },
                    { "width": "15%", "data": "coordinator" },
                    { "width": "15%", "data": "impact_on" },
                    { "width": "15%", "data": "impact_scores" }
                ]
            } );
            $('#project_details_no_impact').DataTable( {
                "data": data.body_no_impact,
                "columns": [
                    { "data": "name" },
                    { "data": "description" },
                    { "data": "status" },
                    { "data": "start_date" },
                    { "data": "end_date" },
                    { "data": "coordinator" }
                ]
            } );
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data.responseText);
        }
    })
}


function loadProjectSocialImpactSummaryCards(server_subfolder, project_id) {
    var base_url = getBaseURL(server_subfolder);
    var endpoint = base_url.concat("/api/social-impact/projects/impact/", project_id, "/overall/");
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data) {
            document.getElementById("dh-title").innerHTML += data.name;
            let sd_elements = document.getElementsByClassName("start_date");
            let ed_elements = document.getElementsByClassName("end_date");
            for (i = 0; i < sd_elements.length; i++) {
                sd_elements[i].textContent = data.start_date;
                ed_elements[i].textContent = data.end_date;
            }
            document.getElementById("social_targets").innerHTML = data.targets;
            document.getElementById("overall_impact_score").innerHTML = data.overall_score;
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data.responseText);
        }
    })
}


function createSocialImpactTables(server_subfolder, project_id) {
    let base_url = getBaseURL(server_subfolder);
    let endpoint = base_url.concat("/", "api/social-impact/projects/impact/", project_id, "/details/");
    let target, evidence_data, sior_data, impact_header_id, table_evidence_id;
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            const div_container = document.getElementById('container');
            for (i = 0; i < data.impacts.length; i++) {
                impact_header_id = 'header_impact_' + (i+1);
                table_evidence_id = '#table_evidence_' + (i+1);
                table_sior_id = '#table_sior_' + (i+1);
                document.getElementById(impact_header_id).innerHTML = 'Social Target: ' + data.impacts[i].social_target;
                doc_url = base_url.concat("/", data.impacts[i].evidence.file);
                dic_url = base_url.concat("/", data.impacts[i].dictionary);
                evidence_data = [{
                    'evidence': data.impacts[i].evidence.sentence,
                    'document': '<a href="'+ doc_url +'" target="_blank">'+ data.impacts[i].evidence.name +'</a>',
                    'page': data.impacts[i].evidence.page,
                    'impact_keywords': data.impacts[i].evidence.impact_keywords,
                    'dictionary': '<a href="'+dic_url+'" target="_blank">Download</a>'
                }];
                $(table_evidence_id).DataTable({
                    "data": evidence_data,
                    "columns": [
                        { "width": "35%", "data": "evidence" },
                        { "width": "20%", "data": "document" },
                        { "width": "5%", "data": "page" },
                        { "width": "10%", "data": "impact_keywords" },
                        { "width": "10%", "data": "dictionary" }
                    ]
                });
                if (data.impacts[i].percentage_improvement != null) {
                    improvement = data.impacts[i].percentage_improvement;
                }
                else {
                    improvement = '-';
                }
                if (data.impacts[i].description_achievement != '') {
                    desc_achievement = data.impacts[i].description_achievement;
                }
                else {
                    desc_achievement = '-';
                }
                if (data.impacts[i].description_sustainability != '') {
                    sustainability = data.impacts[i].description_sustainability;
                } else {
                    sustainability = '-'
                }
                if (data.impacts[i].description_replicability != '') {
                    replicability = data.impacts[i].description_replicability;
                } else {
                    replicability = '-';
                }
                if (data.impacts[i].evidence.is_scientific == 'True') {
                    scientific_evidence = 'Yes';
                }
                else {
                    scientific_evidence = 'No';
                }
                sior_data = [{
                    'improvement': improvement,
                    'desc_achievement': desc_achievement,
                    'sustainability': sustainability,
                    'replicability': replicability,
                    'scientific': scientific_evidence,
                    'score': data.impacts[i].score
                }];
                $(table_sior_id).DataTable({
                    "data": sior_data,
                    "columns": [
                        { "width": "10%", "data": "improvement" },
                        { "width": "15%", "data": "desc_achievement" },
                        { "width": "20%", "data": "sustainability" },
                        { "width": "20%", "data": "replicability" },
                        { "width": "10%", "data": "scientific" },
                        { "width": "5%", "data": "score" }
                    ]
                });
            }
            loadOtherDocsTables(data, base_url);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data.responseText);
        }
    });
}


function loadOtherDocsTables(data, base_url) {
    let docs = Array();
    for (i = 0; i < data.docs.length; i++) {
        doc_url = base_url.concat("/", data.docs[i].url);
        docs.push(
            {
                'name': '<a href="' + doc_url + '" target="_blank">'+ data.docs[i].name + '</a>'
            }
        );
    }
    $('#table_other_docs').DataTable( {
        "data": docs,
        "columns": [
            { "data": "name" }
        ]
    });
}