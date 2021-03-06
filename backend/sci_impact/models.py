from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

import datetime

# Constants

GENDERS = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
)

CITATION_TYPE = (
    ('slides', 'Slides'),
    ('syllabus', 'Syllabus'),
    ('tweet', 'Tweet'),
    ('wikipedia', 'Wikipedia'),
    ('blog', 'Blog'),
    ('grey_literature', 'Grey Literature'),
    ('sci_publication', 'Scientific Publication'),
    ('book', 'Book'),
    ('patent', 'Patent'),
)

ACADEMIC_REPO = (
    ('gscholar', 'Google Scholar'),
    ('wos', 'Web of Science'),
    ('scopus', 'Scopus'),
    ('pubmed', 'PubMed'),
    ('other', 'Other'),
)

VENUE_TYPE = (
    ('journal', 'Journal'),
    ('proceeding', 'Proceeding'),
    ('other', 'Other'),
)

DATA_TYPE = (
    ('int', 'Integer'),
    ('str', 'String'),
    ('bool', 'Boolean'),
    ('float', 'Float'),
    ('list', 'List'),
    ('dict', 'Dictionary'),
)

NET_TYPE = (
    ('directed', 'Directed'),
    ('undirected', 'Undirected'),
)

YEAR_CHOICES = []
for year in range(2000, datetime.date.today().year+1):
    YEAR_CHOICES.append((year, year))


class Artifact(models.Model):
    title = models.CharField(max_length=300)
    year = models.IntegerField()
    url = models.URLField(max_length=500, null=True, blank=True)
    language = models.CharField(max_length=50, default='eng')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Artifact, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.title}"

    def __str__(self):
        return self.title


class Person(models.Model):
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True, choices=GENDERS)
    nationality = models.ForeignKey('Country', on_delete=models.CASCADE, null=True, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    class Meta:
        abstract = True


class Country(models.Model):
    name = models.CharField(max_length=100)
    iso_code = models.CharField(max_length=3, null=True, blank=True)
    alternative_names = models.TextField(null=True, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Country, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "countries"


class Region(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Region, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}, {self.country.name}"

    def __str__(self):
        return f"{self.name}"


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.CASCADE)
    wikipage = models.URLField(blank=True, null=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(City, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.region:
            return f"{self.name}, {self.region.name}, {self.country.name}"
        else:
            return f"{self.name}, {self.country.name}"

    class Meta:
        verbose_name_plural = "cities"


class CustomField(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=DATA_TYPE, default='int')
    source = models.URLField(null=True, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(CustomField, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}: {self.value} ({self.type})"

    def __str__(self):
        return f"{self.name}: {self.value} ({self.type})"


class Venue(models.Model):
    name = models.CharField(max_length=300)
    type = models.CharField(max_length=100, choices=DATA_TYPE, default='journal')
    issn = models.CharField(max_length=10, null=True, blank=True)
    volume = models.CharField(max_length=100, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    issue = models.CharField(max_length=300, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    month = models.CharField(max_length=10, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=300, null=True, blank=True)
    impact_factor = models.IntegerField(null=True, blank=True)
    conference_ranking = models.CharField(max_length=10, null=True, blank=True)
    quartile = models.CharField(max_length=10, null=True, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Venue, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"


class Scientist(Person):
    # scientist ids (orcid, scopus, pmc, etc)
    scientist_ids = models.ForeignKey(CustomField, on_delete=models.CASCADE, null=True, blank=True)
    # production
    articles = models.IntegerField(default=0)
    articles_as_first_author = models.IntegerField(default=0)
    articles_as_last_author = models.IntegerField(default=0)
    articles_with_citations = models.IntegerField(default=0)
    books = models.IntegerField(default=0)
    patents = models.IntegerField(default=0)
    datasets = models.IntegerField(default=0)
    tools = models.IntegerField(default=0)
    # citations
    article_citations = models.IntegerField(default=0)
    book_citations = models.IntegerField(default=0)
    dataset_citations = models.IntegerField(default=0)
    patent_citations = models.IntegerField(default=0)
    tool_citations = models.IntegerField(default=0)
    total_citations = models.IntegerField(default=0)
    # productivity measure
    h_index = models.IntegerField(default=0)
    i10_index = models.IntegerField(default=0)
    # additional fields
    is_duplicate = models.BooleanField(default=False)
    possible_duplicate = models.BooleanField(default=False)
    is_pi_inb = models.BooleanField(default=False)
    most_recent_pi_inb_collaborator = models.ForeignKey('Scientist', on_delete=models.CASCADE, null=True, blank=True)
    alternative_names = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Scientist, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Article(Artifact):
    doi = models.CharField(max_length=300, null=True, blank=True)
    pages = models.CharField(max_length=50, null=True, blank=True)
    keywords = models.TextField(null=True, blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    academic_db = models.CharField(max_length=100, choices=ACADEMIC_REPO, default='other')
    funding_details = models.TextField(null=True, blank=True)
    cited_by = models.IntegerField(default=0)
    # publication id on academic repositories
    repo_id = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    # other fields
    inb_pi_as_author = models.BooleanField(default=False)

    def __unicode__(self):
        return f"{self.title}"

    def __str__(self):
        return f"{self.title}"


class Book(Artifact):
    isbn = models.CharField(max_length=20, null=True, blank=True)

    def __unicode__(self):
        return f"{self.title}"

    def __str__(self):
        return f"{self.title}"


class Dataset(Artifact):

    def __unicode__(self):
        return f"{self.title}"

    def __str__(self):
        return f"{self.title}"


class Tool(Artifact):
    source_repo = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return f"{self.title}"

    def __str__(self):
        return f"{self.title}"


class Patent(Artifact):

    def __unicode__(self):
        return f"{self.title}"

    def __str__(self):
        return f"{self.title}"


class ArtifactCitation(models.Model):
    from_artifact = models.ForeignKey(Artifact, related_name='from_artifact', on_delete=models.CASCADE)
    to_artifact = models.ForeignKey(Artifact, related_name='to_artifact', on_delete=models.CASCADE)
    self_citation = models.BooleanField(default=False)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(ArtifactCitation, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('from_artifact', 'to_artifact')

    def __unicode__(self):
        return f"From {self.from_artifact.title} To {self.to_artifact.title}"

    def __str__(self):
        return f"From {self.from_artifact.title} To {self.to_artifact.title}"


class Authorship(models.Model):
    author = models.ForeignKey(Scientist, on_delete=models.CASCADE)
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE, null=True, blank=True)
    first_author = models.BooleanField(default=False)
    last_author = models.BooleanField(default=False)
    corresponding_author = models.BooleanField(default=False)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Authorship, self).save(*args, **kwargs)


class Institution(models.Model):
    name = models.TextField()
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.CASCADE)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    web_page = models.URLField(blank=True, null=True)
    is_inb = models.BooleanField(default=False)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Institution, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name


class Affiliation(models.Model):
    scientist = models.ForeignKey(Scientist, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    joined_date = models.DateField(null=True, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    # production
    articles = models.IntegerField(default=0)
    articles_as_first_author = models.IntegerField(default=0)
    articles_with_citations = models.IntegerField(default=0)
    books = models.IntegerField(default=0)
    patents = models.IntegerField(default=0)
    datasets = models.IntegerField(default=0)
    tools = models.IntegerField(default=0)
    # citations
    article_citations = models.IntegerField(default=0)
    book_citations = models.IntegerField(default=0)
    dataset_citations = models.IntegerField(default=0)
    patent_citations = models.IntegerField(default=0)
    tool_citations = models.IntegerField(default=0)
    total_citations = models.IntegerField(default=0)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Affiliation, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.scientist.last_name}, {self.scientist.first_name}, {self.institution.name}"

    def __str__(self):
        return f"{self.scientist.last_name}, {self.scientist.first_name}, {self.institution.name}"

    class Meta:
        unique_together = ('scientist', 'institution')


class Network(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=50, choices=NET_TYPE, default='undirected')
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Network, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"


class NetworkNode(models.Model):
    name = models.CharField(max_length=500)
    network = models.ForeignKey(Network, on_delete=models.CASCADE)
    attrs = models.ManyToManyField(CustomField, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(NetworkNode, self).save(*args, **kwargs)


class NetworkEdge(models.Model):
    node_a = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, related_name='node_a')
    node_b = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, related_name='node_b')
    network = models.ForeignKey(Network, on_delete=models.CASCADE)
    attrs = models.ManyToManyField(CustomField, blank=True)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(NetworkEdge, self).save(*args, **kwargs)


class Impact(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now, editable=False)
    scientist = models.ForeignKey(Scientist, null=True, blank=True, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.CASCADE)
    start_year = models.IntegerField(choices=YEAR_CHOICES)
    end_year = models.IntegerField(choices=YEAR_CHOICES)
    total_publications = models.IntegerField(default=0, editable=False)
    total_weighted_impact = models.FloatField(default=0, editable=False)
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Impact, self).save(*args, **kwargs)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"


class ImpactDetail(models.Model):
    impact_header = models.ForeignKey(Impact, on_delete=models.CASCADE)
    year = models.IntegerField(choices=YEAR_CHOICES)
    publications = models.IntegerField()
    citations = models.IntegerField()
    avg_citations_per_publication = models.FloatField()
    prop_not_cited_publications = models.FloatField()
    prop_self_citations = models.FloatField()
    impact_field = models.FloatField()
    prop_publications_year = models.FloatField()
    weighted_impact_field = models.FloatField()
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(ImpactDetail, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('impact_header', 'year')


class FieldCitations(models.Model):
    field = models.CharField(max_length=200)
    source_name = models.CharField(max_length=200)
    source_url = models.URLField(blank=True, null=True)
    year = models.IntegerField(choices=YEAR_CHOICES)
    avg_citations_field = models.FloatField()
    # audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        # On save, update timestamps
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(FieldCitations, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "field citations"

# class Citation(models.Model):
#     title = models.CharField(max_length=100, null=True, blank=True)
#     cite_id = models.CharField(max_length=45)
#     url = models.URLField(blank=True, null=True)
#     type = models.CharField(max_length=50, choices=CITATION_TYPE)
#
#     def __unicode__(self):
#         return f"{self.type}, {self.cite_id}"
#
#     def __str__(self):
#         if self.title:
#             return f"{self.title}, {self.type}"
#         elif self.url:
#             return f"{self.url}, {self.type}"
#         else:
#             return f"{self.cite_id}, {self.type}"


