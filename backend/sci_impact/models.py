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


class Citation(models.Model):
    type = models.CharField(max_length=50, choices=CITATION_TYPE)
    cite_id = models.CharField(max_length=45)
    cite_url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return f"{self.type}, {self.cite_id}"


class Scientist(models.Model):
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    birth_date = models.DateField(null=True, blank=True)
    orcid = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True, choices=GENDERS)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    # production
    scientific_publications = models.IntegerField(default=0)
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


class ScientificPublication(models.Model):
    title = models.CharField(max_length=100)
    doi = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField()
    category = models.CharField(max_length=100, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    citations = models.ManyToManyField(Citation, blank=True)
    authors = models.ManyToManyField(Scientist)

    def __unicode__(self):
        return f"{self.title}"


class Book(models.Model):
    title = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, null=True, blank=True)
    year = models.IntegerField()
    url = models.URLField(null=True, blank=True)
    citations = models.ManyToManyField(Citation, blank=True)
    authors = models.ManyToManyField(Scientist)

    def __unicode__(self):
        return f"{self.title}"


class Dataset(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    citations = models.ManyToManyField(Citation, blank=True)
    authors = models.ManyToManyField(Scientist)

    def __unicode__(self):
        return f"{self.name}"


class Tool(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    source_repo = models.URLField(null=True, blank=True)
    citations = models.ManyToManyField(Citation, blank=True)
    authors = models.ManyToManyField(Scientist)

    def __unicode__(self):
        return f"{self.name}"


class Patent(models.Model):
    title = models.CharField(max_length=100)
    year = models.IntegerField()
    url = models.URLField(null=True, blank=True)
    citations = models.ManyToManyField(Citation, blank=True)
    authors = models.ManyToManyField(Scientist)

    def __unicode__(self):
        return f"{self.title}"


class Institution(models.Model):
    name = models.CharField(max_length=100, default='')
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.CASCADE)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    web_page = models.URLField(blank=True, null=True)
    scientists = models.ManyToManyField(Scientist, through='Affiliation')

    def __unicode__(self):
        return f"{self.name}"

    def __str__(self):
        return self.name


class Affiliation(models.Model):
    scientist = models.ForeignKey(Scientist, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    data_joined = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return f"{self.scientist.last_name}, {self.scientist.first_name} - {self.institution.name}"

    def __str__(self):
        return f"{self.scientist.last_name}, {self.scientist.first_name} - {self.institution.name}"
