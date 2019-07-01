import datetime
import json
from collections import defaultdict
from django.db.models import Count, Sum
from django.shortcuts import render
from sci_impact.models import Scientist, Article, Impact, ArtifactCitation, ImpactDetail, FieldCitations


def dashboard_idx(request):
    start_year, end_year = 2003, datetime.datetime.now().year-1
    articles = Article.objects.filter(year__gte=start_year).filter(year__lte=end_year).\
        filter(inb_pi_as_author=True)
    citations = ArtifactCitation.objects.select_related().filter(to_artifact__in=articles)
    total_pis = Scientist.objects.filter(is_pi_inb=True).count()
    articles_by_year = articles.values('year').annotate(count=Count('year')).order_by('year')
    citations_by_year = defaultdict(int)
    for citation in citations:
        if citation.from_artifact.year <= end_year:
            citations_by_year[citation.from_artifact.year] += 1
    data_articles_chart = {
        'labels': [dict['year'] for dict in articles_by_year],
        'datasets': [
            {
                'data': [dict['count'] for dict in articles_by_year],
                'label': 'Articles',
                'color': '#4285F4',
                'fill': False
            }
        ]
    }
    data_citations_chart = {
        'labels': sorted(citations_by_year.keys()),
        'datasets': [
            {
                'data': [citations_by_year[year] for year in sorted(citations_by_year.keys())],
                'label': 'Citations',
                'color': '#17a2b8',
                'fill': False
            }
        ],
    }
    context = {
        'total_pis': total_pis,
        'total_articles': articles.count(),
        'total_citations': citations.count(),
        'start_year': start_year,
        'end_year': end_year,
        'data_articles_chart': json.dumps(data_articles_chart),
        'data_citations_chart': json.dumps(data_citations_chart)
    }
    return render(request, "main.html", context)


def __prepare_pi_impact_data(pi_obj):
    impact_name = f"Scientific Impact {pi_obj} 2009-2016"
    sci_impact_obj = Impact.objects.select_related().get(name=impact_name)
    sci_impact_details = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj)
    total_publications = sci_impact_details.aggregate(Sum('publications'))['publications__sum']
    total_citations = sci_impact_details.aggregate(Sum('citations'))['citations__sum']
    citations_per_publications = round(total_citations / total_publications, 2)
    cpp_years = [{'year': sci_impact_detail.year, 'cpp': round(sci_impact_detail.avg_citations_per_publication, 2)}
                 for sci_impact_detail in sci_impact_details]
    pi_impact_data = {
        'total_publications': total_publications,
        'total_citations': total_citations,
        'citations_per_publications': citations_per_publications,
        'sci_impact': round(sci_impact_obj.total_weighted_impact, 2),
        'citations_per_publications_year': cpp_years
    }
    return pi_impact_data


def __prepare_impact_data(impact_name, html_params):
    sci_impact_obj = Impact.objects.select_related().get(name=impact_name)
    sci_impact_start_year, sci_impact_end_year = sci_impact_obj.start_year, sci_impact_obj.end_year
    sci_impact = round(sci_impact_obj.total_weighted_impact, 2)
    sci_impact_details = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj)
    total_publications = sci_impact_details.aggregate(Sum('publications'))['publications__sum']
    total_citations = sci_impact_details.aggregate(Sum('citations'))['citations__sum']
    citations_per_publications = round(total_citations / total_publications, 2)
    years_range = []
    table_headers = ['Year', 'Publications', 'Citations', 'Citations per Publications', '% Not Cited Publications',
                     '% Self-citations', 'Avg. Citations in the Field', 'Scientific Impact',
                     '% Publication of the Total', 'Weighted Impact']
    table_rows, field_cpp_years = [], []
    for sci_impact_detail in sci_impact_details:
        years_range.append(sci_impact_detail.year)
        fc = FieldCitations.objects.select_related().get(year=sci_impact_detail.year)
        field_cpp_years.append(round(fc.avg_citations_field, 2))
        table_rows.append(
            {
                'year': sci_impact_detail.year,
                'publications': sci_impact_detail.publications,
                'citations': sci_impact_detail.citations,
                'citations_per_publications': round(sci_impact_detail.avg_citations_per_publication, 2),
                'prop_not_cited_publications': round(sci_impact_detail.prop_not_cited_publications, 2),
                'prop_self_citations': round(sci_impact_detail.prop_self_citations, 2),
                'avg_field_citations': round(fc.avg_citations_field, 2),
                'impact_field': round(sci_impact_detail.impact_field, 2),
                'prop_publications_year': round(sci_impact_detail.prop_publications_year, 2),
                'weighted_impact_field': round(sci_impact_detail.weighted_impact_field, 2)
            }
        )
    cpp_years = []
    for year in years_range:
        si = ImpactDetail.objects.select_related().get(impact_header=sci_impact_obj, year=year)
        cpp_years.append(round(si.avg_citations_per_publication, 2))
    # Prepare data for INB chart
    data_chart_inb = {
        'labels': years_range,
        'datasets': []
    }
    data_inb_cpp = {
        'data': cpp_years,
        'label': 'Avg. citations per article',
        'color': '#4285F4',
        'fill': False
    }
    data_chart_inb['datasets'].append(data_inb_cpp)
    data_field_cpp = {
        'data': field_cpp_years,
        'label': 'Avg. citations per article in the field',
        'color': '#292b2c',
        'fill': False
    }
    data_chart_inb['datasets'].append(data_field_cpp)
    # Prepare data for PI chart
    data_chart_pis = {
        'labels': years_range,
        'datasets': []
    }
    pis_obj = Scientist.objects.select_related().filter(is_pi_inb=True)
    colors = ['#3e95cd', '#8e5ea2', '#3cba9f', '#e8c3b9', '#c45850', '#f0ad4e', '#d9534f',
              '#a1204f', '#b8c05c', '#4a836d']
    for idx in range(0, len(pis_obj)):
        pi_obj = pis_obj[idx]
        pi_impact_data = __prepare_pi_impact_data(pi_obj)
        data_pi_cpp = {
            'data': [dict['cpp'] for dict in pi_impact_data['citations_per_publications_year']],
            'label': f"Avg. citations per article of {pi_obj}",
            'color': colors[idx],
            'fill': False
        }
        data_chart_pis['datasets'].append(data_pi_cpp)
    data_chart_pis['datasets'].append(data_field_cpp)
    # Prepare data to send back
    context = {
        'scientific_impact': sci_impact,
        'sci_impact_start_year': sci_impact_start_year,
        'sci_impact_end_year': sci_impact_end_year,
        'total_publications': total_publications,
        'total_citations': total_citations,
        'citations_per_publications': citations_per_publications,
        'data_inb_chart': json.dumps(data_chart_inb),
        'data_pis_chart': json.dumps(data_chart_pis),
        'table': {'headers': table_headers, 'rows': table_rows},
        'html_params': html_params
    }
    return context


def dashboard_sci_impact(request, **kwargs):
    impact_ref = kwargs.get('pi')
    #impact_ref = request.path.split('/')[-1]
    mapping_dict = {
        'carazo': 'Jose M Carazo',
        'dopazo': 'Joaquin Dopazo',
        'gelpi': 'Jose L Gelpi',
        'guigo': 'Roderic Guigo',
        'gut': 'Ivo G Gut',
        'navarro': 'Arcadi Navarro',
        'orozco': 'Modesto Orozco',
        'sanz': 'Ferran Sanz',
        'trellez': 'Oswaldo R Trellez',
        'valencia': 'Alfonso Valencia'
    }
    if impact_ref:
        impact_name = f"Scientific Impact {mapping_dict[impact_ref]} 2009-2016"
        html_params = {
            'title': f"Principal Investigator: { mapping_dict[impact_ref]}",
            'show_pis_charts': 0
        }
    else:
        impact_name = 'Scientific Impact INB 2009-2016'
        html_params = {
            'title': 'Spanish National Institute of Bioinformatics',
            'show_pis_charts': 1
        }
    context = __prepare_impact_data(impact_name, html_params)
    return render(request, "sci_impact.html", context)


def dashboard_social_impact(request):
    # Social Impact
    total_projects = 26
    social_impact = 0.0
    context = {
        'total_projects': total_projects,
        'social_impact': social_impact
    }
    return render(request, "sci_impact.html", context)