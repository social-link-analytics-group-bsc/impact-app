from django.db import models


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


class Artifact(models.Model):
    title = models.CharField(max_length=300)
    year = models.IntegerField()
    url = models.URLField(null=True, blank=True)
    language = models.CharField(max_length=50, default='eng')


class Person(models.Model):
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True, choices=GENDERS)
    nationality = models.ForeignKey('Country', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        abstract = True


class Country(models.Model):
    name = models.CharField(max_length=100)
    iso_code = models.CharField(max_length=3, null=True, blank=True)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "countries"


class Region(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __unicode__(self):
        return f"{self.name}, {self.country.name}"

    def __str__(self):
        return f"{self.name}"


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.CASCADE)
    wikipage = models.URLField(blank=True, null=True)

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

    def __unicode__(self):
        return f"{self.name}: {self.value} ({self.type})"

    def __str__(self):
        return f"{self.name}: {self.value} ({self.type})"


class Venue(models.Model):
    name = models.CharField(max_length=300)
    type = models.CharField(max_length=100, choices=DATA_TYPE, default='journal')
    issn = models.CharField(max_length=10, null=True, blank=True)
    volume = models.IntegerField(null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    issue = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    month = models.CharField(max_length=10, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=300, null=True, blank=True)
    impact_factor = models.IntegerField(null=True, blank=True)
    conference_ranking = models.CharField(max_length=10, null=True, blank=True)
    quartile = models.CharField(max_length=10, null=True, blank=True)

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"


class Scientist(Person):
    orcid = models.CharField(max_length=50, null=True, blank=True)
    scopus_id = models.CharField(max_length=50, null=True, blank=True)
    pmc_id = models.CharField(max_length=50, null=True, blank=True)
    # production
    scientific_publications_as_first_author = models.IntegerField(default=0)
    scientific_publications_with_citations = models.IntegerField(default=0)
    books = models.IntegerField(default=0)
    patents = models.IntegerField(default=0)
    datasets = models.IntegerField(default=0)
    tools = models.IntegerField(default=0)
    # citations
    book_citations = models.IntegerField(default=0)
    dataset_citations = models.IntegerField(default=0)
    patent_citations = models.IntegerField(default=0)
    tools_citations = models.IntegerField(default=0)
    total_citations = models.IntegerField(default=0)
    # productivity measure
    h_index = models.IntegerField(default=0)
    i10_index = models.IntegerField(default=0)

    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Article(Artifact):
    doi = models.CharField(max_length=300, null=True, blank=True)
    pages = models.CharField(max_length=50, null=True, blank=True)
    keywords = models.CharField(max_length=300, null=True, blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    academic_db = models.CharField(max_length=100, choices=ACADEMIC_REPO, default='other')
    # publication id on academic repositories
    repo_ids = models.ForeignKey(CustomField, on_delete=models.CASCADE)

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

    class Meta:
        unique_together = ('from_artifact', 'to_artifact')


class Authorship(models.Model):
    author = models.ForeignKey(Scientist, on_delete=models.CASCADE)
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE, null=True, blank=True)
    first_author = models.BooleanField(default=False)
    corresponding_author = models.BooleanField(default=False)


class Institution(models.Model):
    name = models.CharField(max_length=300, default='')
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.CASCADE)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    web_page = models.URLField(blank=True, null=True)

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
    book_citations = models.IntegerField(default=0)
    dataset_citations = models.IntegerField(default=0)
    patent_citations = models.IntegerField(default=0)
    tools_citations = models.IntegerField(default=0)
    total_citations = models.IntegerField(default=0)

    def __unicode__(self):
        return f"{self.scientist.last_name}, {self.scientist.first_name}, {self.institution.name}"

    def __str__(self):
        return f"{self.scientist.last_name}, {self.scientist.first_name}, {self.institution.name}"


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


