from django.contrib.auth.models import User
from django.db import models
from sci_impact.models import Country, Institution

STATUSES = (
    ('active', 'Active'),
    ('finished', 'Finished'),
    ('other', 'Other'),
)

SDGs = (
    ('poverty', 'No poverty'),
    ('hunger', 'Zero hunger'),
    ('health', 'Good health and well-being'),
    ('education', 'Quality education'),
    ('gender', 'Gender equality'),
    ('water', 'Clean water and sanitation'),
    ('energy', 'Affordable and clean energy'),
    ('work', 'Decent work and economic growth'),
    ('industry', 'Industry, innovation, and infrastructure'),
    ('inequalities', 'Reduced inequalities'),
    ('sustainable', 'Sustainable cities and communities'),
    ('consumption', 'Responsible consumption and production'),
    ('climate', 'Climate action'),
    ('life_water', 'Life below water'),
    ('life_land', 'Life on land'),
    ('peace', 'Peace, justice, and strong institutions'),
    ('partnership', 'Partnership for the goals'),
)


class Project(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    twitter_account = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUSES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    funded_by = models.TextField(null=True, blank=True)
    overall_budget = models.FloatField(null=True, blank=True)
    budget_eu = models.FloatField(null=True, blank=True)
    coordinator = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.CASCADE)
    coordinator_country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    cordis_url = models.URLField(null=True, blank=True)
    twitter_hashtag = models.CharField(max_length=100, null=True, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name


class Publication(models.Model):
    name = models.CharField(max_length=300)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    file = models.FileField(upload_to='docs/', blank=True, null=True, max_length=500)
    url = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name


class ImpactMention(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    page = models.IntegerField()
    sentence = models.TextField()
    impact_mention = models.CharField(max_length=300)
    mention_is_correct = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class SIORMeasurement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    evidence = models.ForeignKey(ImpactMention, on_delete=models.CASCADE)
    sdg = models.CharField(max_length=300, choices=SDGs)
    percentage_improvement = models.FloatField(null=True, blank=True)
    description_improvement = models.TextField(null=True, blank=True)
    sustainability = models.BooleanField(default=False)
    replicability = models.BooleanField(default=False)
    score = models.IntegerField(default=0, editable=False)

    def __unicode__(self):
        return f"Project: {self.project}, Impact: {self.score}"

    def __str__(self):
        return f"Project: {self.project}, Impact: {self.score}"
