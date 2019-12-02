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
    let evidence_data = Array();
    let sior_data = Array();
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function(data){
            const div_container = document.getElementById('container');
            for (i = 0; i < data.impacts.length; i++) {
                let target = 'Social Target: ' + data.impacts[i].social_target;
                // create div row
                let div_row = document.createElement('div');
                div_row.className = 'row';
                // create div col
                let div_col = document.createElement('div');
                div_col.className = 'col-xl-12 col-md-12 mb-4';
                // create div card shadow
                let div_card_shadow = document.createElement('div');
                div_card_shadow.className = 'card shadow mb-4';
                // create div card header
                let div_card_header = document.createElement('div');
                div_card_header.className = 'card-header py-3 d-flex flex-row align-items-center justify-content-between';
                div_card_header.innerHTML = '<h6 class="m-0 font-weight-bold text-primary">' + target + '</h6>';
                div_card_shadow.appendChild(div_card_header);
                // create div card body
                let div_card_body = document.createElement('div');
                div_card_body.className = 'card-body';
                div_card_shadow.appendChild(div_card_body);

                // create empty div
                let div_empty = document.createElement('div');
                div_card_body.appendChild(div_empty);

                // create div table responsive
                let div_table = document.createElement('div');
                div_table.className = 'table-responsive';
                div_empty.appendChild(div_table);

                // create evidence table
                let table = document.createElement('table');
                table.className = 'table table-bordered';
                table.width = '100%';
                table.cellspacing = '0';
                table.id = 'tableevidence' + i+1;
                // create table headers
                let headers = Array('Evidence', 'Document', 'Page', 'Impact Keywords', 'File', 'Impact Dictionary');
                for (j=0; j < headers.length; j++) {
                    let header = table.createTHead();
                    th = document.createElement('th');
                    th.innerHTML = headers[j];
                    header.appendChild(th);
                }
                // create table body
                let table_body = document.createElement('tbody');
                table.appendChild(table_body);
                div_table.appendChild(table);

                // create empty div
                div_empty = document.createElement('div');
                div_card_body.appendChild(div_empty);

                // create div table responsive
                div_table = document.createElement('div');
                div_table.className = 'table-responsive';
                div_empty.appendChild(div_table);

                // create sior table
                table = document.createElement('table');
                table.className = 'table table-bordered';
                table.width = '100%';
                table.cellspacing = '0';
                table.id = 'table_sior_' + i+1;
                // create table headers
                headers = Array('Evidence is scientific or official', 'Improvement (%)', 'Description of Improvement', 'Sustainability', 'Replicability');
                for (j=0; j < headers.length; j++) {
                    let header = table.createTHead();
                    th = document.createElement('th');
                    th.innerHTML = headers[j];
                    header.appendChild(th);
                }
                // create table body
                table_body = document.createElement('tbody');
                table.appendChild(table_body);
                div_table.appendChild(table);

                div_col.appendChild(div_card_shadow);
                div_row.appendChild(div_col);
                div_container.appendChild(div_row);

                evidence_data.push(
                    {
                        'evidence': data.impacts[i].evidence.sentence,
                        'document': data.impacts[i].evidence.name,
                        'page': data.impacts[i].evidence.page,
                        'impact_keywords': data.impacts[i].impact_keywords,
                        'file': '<a href="' + data.impacts[i].evidence.file + '>' + data.impacts[i].evidence.name + '</a>',
                        'dictionary': data.impacts[i].dictionary
                    }
                );

                sior_data.push(
                    {
                        'scientific': data.impacts[i].evidence.is_scientific,
                        'improvement': data.impacts[i].percentage_improvement,
                        'desc_improvement': data.impacts[i].description_improvement,
                        'sustainability': data.impacts[i].description_sustainability,
                        'replicability': data.impacts[i].description_replicability
                    }
                );
            }
            console.log($.fn.dataTable.tables());

            /*for (i = 0; i < evidence_data.length; i++) {
                table_evidence_id = '#table_evidence_' + i+1;
                $('#tableevidence01').DataTable( {
                "data": evidence_data[i],
                "columns": [
                    { "width": "35%", "data": "evidence" },
                    { "width": "20%", "data": "document" },
                    { "width": "5%", "data": "page" },
                    { "width": "10%", "data": "impact_keywords" },
                    { "width": "20%", "data": "file" },
                    { "width": "10%", "data": "dictionary" }
                ]
                });
            }*/

             /*impact_data = {
                'evidence_data': evidence_data,
                'sior_data': sior_data
             };*/

             //return impact_data; //loadSocialImpactTables(impact_data);
        },
        error: function(error_data){
            console.log("Error!");
            console.log(error_data.responseText);
        }
    });
}


function loadSocialImpactTables(data) {
    let table_evidence_id, table_sior_id;
    for (i = 0; i < data.evidence_data.length; i++) {
        table_evidence_id = '#table_evidence_' + i+1;
        table_sior_id = '#table_sior_' + i+1;
        $(table_evidence_id).DataTable( {
            "data": data.evidence_data[i],
            "columns": [
                { "width": "35%", "data": "evidence" },
                { "width": "20%", "data": "document" },
                { "width": "5%", "data": "page" },
                { "width": "10%", "data": "impact_keywords" },
                { "width": "20%", "data": "file" },
                { "width": "10%", "data": "dictionary" }
            ]
        });
        $(table_sior_id).DataTable( {
            "data": data.sior_data[i],
            "columns": [
                { "width": "10%", "data": "scientific" },
                { "width": "5%", "data": "improvement" },
                { "width": "25%", "data": "desc_improvement" },
                { "width": "20%", "data": "sustainability" },
                { "width": "20%", "data": "replicability" }
            ]
        });
    }
}