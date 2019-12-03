from django.shortcuts import render
from django.conf import settings
from sci_impact.models import Scientist, Institution
from social_impact.models import SIORMeasurement

import json


def __get_impact_objs():
    researchers = Scientist.objects.filter(is_pi_inb=True).values('id', 'last_name', 'first_name')
    impact_objs = []
    for researcher in researchers:
        impact_objs.append(
            {
                'id': researcher['id'],
                'name': researcher['first_name'] + ' ' + researcher['last_name'],
                'type': 'scientist'
            }
        )
    impact_objs.append(
        {
            'id': Institution.objects.get(is_inb=True).id,
            'name': 'INB',
            'type': 'institution'
        }
    )
    return impact_objs


def index(request):
    context = {
        'server_subfolder': settings.SERVER_SUBFOLDER,
        'impact_objs': json.dumps(__get_impact_objs()),
        'institution_name': Institution.objects.get(is_inb=True).name
    }
    return render(request, "main.html", context)


def sci_impact(request, **kwargs):
    impact_ref = kwargs.get('id')
    context = {
        'impact_obj': impact_ref if impact_ref else '',
        'show_pis_chart': 1 if impact_ref.split('_')[0] == 'institution' else 0,
        'show_table_papers': 1 if impact_ref.split('_')[0] == 'scientist' else 0,
        'server_subfolder': settings.SERVER_SUBFOLDER,
        'impact_objs': json.dumps(__get_impact_objs())
    }
    return render(request, 'sci_impact.html', context)


def social_impact(request):
    context = {
        'server_subfolder': settings.SERVER_SUBFOLDER,
        'impact_objs': json.dumps(__get_impact_objs())
    }
    return render(request, 'projects.html', context)


def social_impact_project(request, **kwargs):
    project_id = kwargs.get('id')
    context = {
        'server_subfolder': settings.SERVER_SUBFOLDER,
        'impact_objs': json.dumps(__get_impact_objs()),
        'project_id': project_id,
        'num_impacts': str(SIORMeasurement.objects.filter(created_by=request.user, project__id=project_id).count())
    }
    return render(request, 'project_impact.html', context)


def sci_impact_methodology(request, **kwargs):
    return render(request, 'sci_impact_methodology.html', {'impact_objs': json.dumps(__get_impact_objs())})


def social_impact_methodology(request, **kwargs):
    return render(request, 'social_impact_methodology.html', {'impact_objs': json.dumps(__get_impact_objs())})

