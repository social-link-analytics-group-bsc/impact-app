from django.conf import settings
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from social_impact.models import Project, SIORMeasurement, Publication


class ProjectsMetaData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        projects = Project.objects.filter(created_by=request.user).order_by('start_date')
        active_projects = Project.objects.filter(status='active', created_by=request.user).count()
        projects_with_impact = SIORMeasurement.objects.filter(created_by=request.user).distinct('project').count()
        response = {
            'total_projects': projects.count(),
            'projects_source': 'Cordis',
            'active_projects': active_projects,
            'start_year': projects[0].start_date.year,
            'end_year': projects.order_by('-start_date')[0].start_date.year,
            'projects_with_impact': projects_with_impact
        }
        return Response(response)


class ProjectList(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        projects = Project.objects.filter(created_by=request.user).order_by('-start_date')
        sior_measurements = SIORMeasurement.objects.filter(created_by=request.user)
        projects_with_impact = [measurement.project.id for measurement in sior_measurements.distinct('project')]
        table_impact, table_no_impact = [], []
        for project in projects:
            coordinador = f"{project.coordinator} ({project.coordinator_country})"
            dict_row = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.get_status_display(),
                'start_date': project.start_date.strftime("%d/%m/%Y"),
                'end_date': project.end_date.strftime("%d/%m/%Y"),
                'coordinator': coordinador
            }
            if project.id in projects_with_impact:
                project_impacts = sior_measurements.filter(project=project)
                impact_targets, impact_scores = [], []
                for project_impact in project_impacts:
                    impact_targets.append(project_impact.get_sdg_display())
                    impact_scores.append(project_impact.score)
                dict_row['impact_targets'] = impact_targets
                dict_row['impact_scores'] = impact_scores
                table_impact.append(dict_row)
            else:
                table_no_impact.append(dict_row)
        response = {'body_impact': table_impact,
                    'body_no_impact': table_no_impact}
        return Response(response)


class ProjectImpactOverall(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, **kwargs):
        project_id = kwargs.get('id')
        project_impacts = SIORMeasurement.objects.filter(created_by=request.user, project__id=project_id)
        targets, scores = [], []
        for project_impact in project_impacts:
            targets.append(project_impact.get_sdg_display())
            scores.append(int(project_impact.score))
        response = {
            'name': project_impacts[0].project.name,
            'start_date': project_impacts[0].project.start_date.strftime("%d/%m/%Y"),
            'end_date': project_impacts[0].project.end_date.strftime("%d/%m/%Y"),
            'targets': ' '.join(targets),
            'overall_score': max(scores)
        }
        return Response(response)


class ProjectImpactDetails(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, **kwargs):
        project_id = kwargs.get('id')
        project_impacts = SIORMeasurement.objects.filter(created_by=request.user, project__id=project_id)
        impacts = []
        for project_impact in project_impacts:
            file_url = '/'.join(project_impact.evidence.publication.file.url.split('/')[1:])
            dict_url = settings.MEDIA_URL + '/'.join(project_impact.evidence.search.dictionary.url.split('/')[1:])
            impact_dict = {
                'evidence': {
                    'name': project_impact.evidence.publication.name,
                    'page': project_impact.evidence.page,
                    'sentence': project_impact.evidence.sentence,
                    'impact_keywords': project_impact.evidence.impact_mention,
                    'is_scientific': str(project_impact.scientific_evidence),
                    'file': file_url
                },
                'social_target': project_impact.get_sdg_display(),
                'percentage_improvement': project_impact.percentage_improvement,
                'description_achievement': project_impact.description_achievement,
                'sustainability':  project_impact.sustainability,
                'description_sustainability': project_impact.description_sustainability,
                'replicability': project_impact.replicability,
                'description_replicability': project_impact.description_replicability,
                'score': project_impact.score,
                'dictionary': dict_url
            }
            impacts.append(impact_dict)
        docs = Publication.objects.filter(created_by=request.user, project_id=project_id)
        project_reports = []
        for doc in docs:
            for impact in impacts:
                if doc.name != impact['evidence']['name']:
                    doc_url = '/'.join(doc.file.url.split('/')[1:])
                    project_reports.append({'name': doc.name, 'url': doc_url})
        response = {
            'impacts': impacts,
            'docs': project_reports
        }
        return Response(response)