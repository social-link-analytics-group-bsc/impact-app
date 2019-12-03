from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from sci_impact.models import Country, Institution

STATUSES = (
    ('active', 'Active'),
    ('finished', 'Finished'),
    ('other', 'Other'),
)

SDGs = (
    ('poverty', 'SGD 1. No poverty'),
    ('hunger', 'SGD 2. Zero hunger'),
    ('health', 'SGD 3. Good health and well-being'),
    ('education', 'SGD 4. Quality education'),
    ('gender', 'SGD 5. Gender equality'),
    ('water', 'SGD 6. Clean water and sanitation'),
    ('energy', 'SGD 7. Affordable and clean energy'),
    ('work', 'SGD 8. Decent work and economic growth'),
    ('industry', 'SGD 9. Industry, innovation, and infrastructure'),
    ('inequalities', 'SGD 10. Reduced inequalities'),
    ('sustainable', 'SGD 11. Sustainable cities and communities'),
    ('consumption', 'SGD 12. Responsible consumption and production'),
    ('climate', 'SGD 13. Climate action'),
    ('life_water', 'SGD 14. Life below water'),
    ('life_land', 'SGD 15. Life on land'),
    ('peace', 'SGD 16. Peace, justice, and strong institutions'),
    ('partnership', 'SGD 17. Partnership for the goals'),
    ('other', 'Other societal objectives'),
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


@receiver(pre_delete, sender=Publication)
def publication_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


class SocialImpactSearch(models.Model):
    name = models.CharField(max_length=300)
    publications = models.ManyToManyField(Publication)
    dictionary = models.FileField(upload_to='dictionaries/', blank=True, null=True, max_length=500)
    completed = models.BooleanField(default=False, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Social Impact Searches"


@receiver(pre_delete, sender=SocialImpactSearch)
def socialimpactsearch_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.dictionary.delete(False)


class SocialImpactSearchPublication(models.Model):
    social_impact_header = models.ForeignKey(SocialImpactSearch, on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return f"{self.social_impact_header}, {self.publication}"

    def __str__(self):
        return f"{self.social_impact_header}, {self.publication}"

    class Meta:
        verbose_name_plural = "Social Impact Publications"


class ImpactMention(models.Model):
    search = models.ForeignKey(SocialImpactSearch, on_delete=models.CASCADE )
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    page = models.IntegerField()
    sentence = models.TextField()
    impact_mention = models.CharField(max_length=300)
    mention_is_correct = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return f"[{self.publication.project}] {self.sentence} (Report: {self.publication})"

    def __str__(self):
        return f"[{self.publication.project}] {self.sentence} (Report: {self.publication})"


class SIORMeasurement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    evidence = models.ForeignKey(ImpactMention, on_delete=models.CASCADE)
    scientific_evidence = models.BooleanField(default=False, verbose_name='Is the evidence a scientific publication or '
                                                                          'an official report?')
    sdg = models.CharField(max_length=300, choices=SDGs, verbose_name='Social Target')
    percentage_improvement = models.FloatField(null=True, blank=True)
    description_improvement = models.TextField(null=True, blank=True)
    sustainability = models.BooleanField(default=False)
    description_sustainability = models.TextField(null=True, blank=True)
    replicability = models.BooleanField(default=False)
    description_replicability = models.TextField(null=True, blank=True)
    score = models.IntegerField(default=0, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return f"Project: {self.project}, Impact: {self.score}"

    def __str__(self):
        return f"Project: {self.project}, Impact: {self.score}"