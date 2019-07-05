from django.shortcuts import render


def index(request):
    return render(request, "main.html", {})


def sci_impact(request, **kwargs):
    impact_ref = kwargs.get('pi')
    context = {
        'impact_obj': impact_ref if impact_ref else '',
        'show_pis_chart': 1 if not impact_ref else 0
    }
    return render(request, 'sci_impact.html', context)


def social_impact(request):
    # Social Impact
    total_projects = 26
    social_impact = 0.0
    context = {
        'total_projects': total_projects,
        'social_impact': social_impact
    }
    return render(request, 'sci_impact.html', context)


def sci_impact_methodology(request, **kwargs):
    return render(request, 'sci_impact_methodology.html', {})

