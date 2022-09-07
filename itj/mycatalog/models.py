from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.contrib.staticfiles.storage import staticfiles_storage

from ckeditor.fields import RichTextField

URL_MAINSITE = 'MAIN'
URL_LINKEDIN = 'LINKEDIN'
URL_ANGELCO = 'ANGELCO'
URL_CRUNCHBASE = 'CRUNCHBASE'
URL_FACEBOOK = 'FACEBOOK'
URL_TWITTER = 'TWITTER'
URL_GLASSDOOR = 'GLASSDOOR'
URL_YOUTUBE = 'YOUTUBE'
URL_INSTAGRAM = 'INSTAGRAM'
URL_STACKOVERFLOW = 'STACKOVERFLOW'
URL_GITHUB = 'GITHUB'
URL_OTHER = 'OTHER'

URL_TYPES = (
    (URL_MAINSITE, 'Company Website'),
    (URL_LINKEDIN, 'LinkedIn'),
    (URL_ANGELCO, 'AngelList'),
    (URL_CRUNCHBASE, 'Crunchbase'),
    (URL_FACEBOOK, 'Facebook'),
    (URL_TWITTER, 'Twitter'),
    (URL_GLASSDOOR, 'Glassdoor'),
    (URL_YOUTUBE, 'YouTube'),
    (URL_INSTAGRAM, 'Instagram'),
    (URL_STACKOVERFLOW, 'Stackoverflow'),
    (URL_GITHUB, 'GitHub'),
    (URL_OTHER, 'OTHER'),
)


class CompanyDomainsClassifier(models.Model):
    class Meta:
        verbose_name = 'Company Domain'
        verbose_name_plural = 'Company Domains'

    domain_name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(blank=True, max_length=255, unique=True)

    def __str__(self):
        return self.domain_name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.domain_name)
        super(CompanyDomainsClassifier, self).save(*args, **kwargs)


class Company(models.Model):
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    NUM_PEOPLE_TEN = 'TEN'
    NUM_PEOPLE_FIFTY = 'FIFTY'
    NUM_PEOPLE_HUNDRED = 'HUNDRED'
    NUM_PEOPLE_TWO_HUNDREDS = 'TWOHUNDREDS'
    NUM_PEOPLE_FIVE_HUNDREDS = 'FIVEHUNDREDS'
    NUM_PEOPLE_THOUSAND = 'THOUSAND'
    NUM_PEOPLE_LARGE = 'LARGE'

    NUM_PEOPLE = (
        (NUM_PEOPLE_TEN, '1-10'),
        (NUM_PEOPLE_FIFTY, '11-50'),
        (NUM_PEOPLE_HUNDRED, '51-100'),
        (NUM_PEOPLE_HUNDRED, '101-500'),
        (NUM_PEOPLE_THOUSAND, '501-1000'),
        (NUM_PEOPLE_LARGE, '>1000'),
    )

    company_name = models.CharField(max_length=250, unique=True)
    company_logo = models.ImageField(max_length=2000, null=True, blank=True, upload_to='logos')
    company_email = models.EmailField(max_length=250, null=True, blank=True)  # used for invoicing
    company_pitch = RichTextField(blank=True)
    description = RichTextField(blank=True)
    offices_locations = models.CharField(max_length=250, null=True, blank=True)
    enabled_flag = models.BooleanField(default=False, verbose_name='Published')
    pub_date = models.DateTimeField(verbose_name='Date created', auto_now_add=True)
    slug = models.SlugField(blank=True, max_length=255, unique=True)
    positions_url = models.URLField(blank=True)
    number_of_people = models.CharField(max_length=20, choices=NUM_PEOPLE, blank=True)
    edited_date = models.DateTimeField(verbose_name='Date edited', auto_now=True)
    funding = models.BooleanField(default=False)
    raised = models.CharField(max_length=50, blank=True)
    num_of_rounds = models.IntegerField(null=True, blank=True)
    last_round_announced_date = models.DateField(blank=True, null=True)
    domain_name = models.ManyToManyField(CompanyDomainsClassifier, blank=True)
    parced_source_id = models.CharField(max_length=100, blank=True)  # link to the parced company id
    founded_year = models.IntegerField(null=True, blank=True)
    other_info = RichTextField(blank=True)

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.company_name)
        super(Company, self).save(*args, **kwargs)

    def company_logo_tag(self):
        if self.company_logo:
            logo = mark_safe('<img src="%s" width="40" alt="%s logo"/>' % (self.company_logo.url, self.company_name))
        else:
            logo = mark_safe('<img src="' + staticfiles_storage.url('mycatalog/nologo.png') + '" width="40" />')
        return logo

    company_logo_tag.short_description = 'Logo'

    @property
    def sorted_positions_set(self):
        return self.position_set.filter(enabled_flag=True, archive_flag=False).order_by('pub_date')

    @property
    def get_number_of_people_value(self):
        return self.get_number_of_people_display()

    @property
    def get_crunchbase_object(self):
        return self.companyurl_set.get(url_type=URL_CRUNCHBASE)

    @property
    def get_website_object(self):
        return self.companyurl_set.get(url_type=URL_MAINSITE)

    def get_absolute_url(self):
        return reverse('mycatalog:company_detail', args=[self.slug])


class CompanyUrl(models.Model):
    url_text = models.URLField(blank=False, null=False, max_length=500)
    url_type = models.CharField(max_length=50, choices=URL_TYPES, default=URL_OTHER, blank=False)
    company_name_ref = models.ForeignKey(Company, null=False, on_delete=models.CASCADE, blank=False)

    @property
    def get_url_type_value(self):
        return self.get_url_type_display()


class CompanyPositionParsingRule(models.Model):
    PARSING_RULE_USE_SELENIUM = 'USE_SELENIUM'
    PARSING_RULE_POSITIONS_LIST = 'POSITIONS_LIST'
    PARSING_RULE_POSITIONS_LIST_IFRAME = 'POSITIONS_LIST_IFRAME'
    PARSING_RULE_POSITIONS_LIST_EXCLUDE = 'POSITIONS_LIST_EXCLUDE'
    PARSING_RULE_POSITIONS_LIST_URL_PREFIX = 'POSITIONS_LIST_URL_PREFIX'
    PARSING_RULE_POSITION_IFRAME = 'POSITION_IFRAME'
    PARSING_RULE_POSITION_NAME = 'POSITION_NAME'
    PARSING_RULE_POSITION_LOCATION = 'POSITION_LOCATION'
    PARSING_RULE_POSITION_DESCRIPTION = 'POSITION_DESCRIPTION'
    PARSING_RULE_POSITION_DESCRIPTION_EXCLUDE = 'POSITION_DESCRIPTION_EXCLUDE'

    PARSING_RULES = (
        (PARSING_RULE_USE_SELENIUM, 'Use selenuim for parsing'),
        (PARSING_RULE_POSITIONS_LIST, 'Positions list'),
        (PARSING_RULE_POSITIONS_LIST_IFRAME, 'Positions list inside IFRAME'),
        (PARSING_RULE_POSITIONS_LIST_EXCLUDE, 'Positions list exclude'),
        (PARSING_RULE_POSITIONS_LIST_URL_PREFIX, 'Positions list URL prefix'),
        (PARSING_RULE_POSITION_IFRAME, 'Position IFRAME path'),
        (PARSING_RULE_POSITION_NAME, 'Title'),
        (PARSING_RULE_POSITION_LOCATION, 'Location'),
        (PARSING_RULE_POSITION_DESCRIPTION, 'Description'),
        (PARSING_RULE_POSITION_DESCRIPTION_EXCLUDE, 'Description exclude'),
    )

    parsing_rule = models.CharField(max_length=100, choices=PARSING_RULES, blank=False)
    parsing_path = models.CharField(max_length=1024, blank=False)
    company_name_ref = models.ForeignKey(Company, null=False, on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return self.parsing_rule


class CompanyPositionUrlIgnore(models.Model):
    position_url = models.URLField(blank=False)
    position_name = models.CharField(max_length=250, blank=True, null=True)
    company_name_ref = models.ForeignKey(Company, null=False, on_delete=models.CASCADE, blank=False)
    creation_date = models.DateTimeField(verbose_name='Date created', auto_now_add=True)

    def __str__(self):
        return self.position_url


class Category(models.Model):
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    category_name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(blank=True, max_length=255, unique=True)

    def __str__(self):
        return self.category_name

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('mycatalog:index_category_filtered', args=[self.slug])


class CategoryKeyword(models.Model):  # keywords to assign category automatically during positions parsing
    keyword = models.CharField(max_length=100, unique=True)
    category_name_ref = models.ForeignKey(Category, null=False, on_delete=models.CASCADE, blank=False,
                                          verbose_name='Category')


class Keyword(models.Model):  # keywords to search positions
    keyword = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, max_length=255, unique=True)
    parced_source_id = models.CharField(max_length=100, blank=True)  # link to the parced tag id

    def __str__(self):
        return self.keyword

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.keyword)
        super(Keyword, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('mycatalog:index_keyword_filtered', args=[self.slug])


class KeywordSynonym(models.Model):
    synonym = models.CharField(max_length=100, unique=True)
    keyword_ref = models.ForeignKey(Keyword, null=False, on_delete=models.CASCADE, blank=False, verbose_name='Keyword')

    def __str__(self):
        return self.synonym


class Position(models.Model):
    SALARY_CURRENCY_USD = 'USD'
    SALARY_CURRENCY_EUR = 'EUR'
    SALARY_CURRENCY_GBP = 'GBP'

    SALARY_CURRENCIES = (
        (SALARY_CURRENCY_USD, 'USD'),
        (SALARY_CURRENCY_EUR, 'EUR'),
        (SALARY_CURRENCY_GBP, 'GBP'),
    )

    SALARY_FREQUENCY_HOUR = 'HOUR'
    SALARY_FREQUENCY_MONTH = 'MONTH'
    SALARY_FREQUENCY_YEAR = 'YEAR'

    SALARY_FREQUENCIES = (
        (SALARY_FREQUENCY_HOUR, 'per hour'),
        (SALARY_FREQUENCY_MONTH, 'per month'),
        (SALARY_FREQUENCY_YEAR, 'per year'),
    )

    EMPLOYMENT_TYPE_FULLTIME = 'FULLTIME'
    EMPLOYMENT_TYPE_PARTTIME = 'PARTTIME'
    EMPLOYMENT_TYPE_CONTRACT = 'CONTRACT'
    EMPLOYMENT_TYPE_INTERNSHIP = 'INTERNSHIP'
    EMPLOYMENT_TYPE_ENTRYLEVEL = 'ENTRYLEVEL'

    EMPLOYMENT_TYPES = (
        (EMPLOYMENT_TYPE_FULLTIME, 'Full-time'),
        (EMPLOYMENT_TYPE_PARTTIME, 'Part-time'),
        (EMPLOYMENT_TYPE_CONTRACT, 'Contract'),
        (EMPLOYMENT_TYPE_INTERNSHIP, 'Internship'),
        (EMPLOYMENT_TYPE_ENTRYLEVEL, 'Entry level'),
    )

    position_name = models.CharField(max_length=250)
    company_name_ref = models.ForeignKey(Company, null=False, on_delete=models.CASCADE, blank=False,
                                         verbose_name='Company')
    category_name_ref = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL, blank=True,
                                          verbose_name='Category')
    job_description = RichTextField(blank=False, verbose_name='Job Description')
    responsibilities = RichTextField(blank=True)
    requirements = RichTextField(blank=True)
    salary_from = models.PositiveIntegerField(blank=True, null=True)
    salary_to = models.PositiveIntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=10, choices=SALARY_CURRENCIES, default=SALARY_CURRENCY_USD,
                                       blank=True)
    salary_frequency = models.CharField(max_length=20, choices=SALARY_FREQUENCIES, default=SALARY_FREQUENCY_YEAR,
                                        blank=True)
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_TYPES, default=EMPLOYMENT_TYPE_FULLTIME,
                                       blank=True)
    how_to_apply = RichTextField(blank=True)
    apply_url = models.URLField(blank=True)
    apply_email = models.EmailField(blank=True, max_length=250)
    locations = models.CharField(max_length=250, blank=True)
    language = models.CharField(max_length=250, blank=True)
    enabled_flag = models.BooleanField(default=False, verbose_name='Published')
    archive_flag = models.BooleanField(default=False, verbose_name='Archived')
    pub_date = models.DateTimeField(verbose_name='Date created', default=timezone.now)
    edited_date = models.DateTimeField(verbose_name='Date edited', auto_now=True)
    slug = models.SlugField(blank=True, max_length=255)
    visa_sponsorship = models.BooleanField(default=False)
    work_worldwide = models.BooleanField(default=False, verbose_name='WWwide')
    keyword_ref = models.ManyToManyField(Keyword, verbose_name='Keywords', blank=True)

    source = models.CharField(max_length=100, blank=True)  # source of the position. For example remoteok
    source_url = models.URLField(blank=True)  # url to the source of the position. For example remoteok.io/856434
    parced_source_id = models.CharField(max_length=100, blank=True)  # link to the parced position id
    position_id_redirect_to = models.PositiveIntegerField(blank=True, null=True, verbose_name='ID redirect to')
    count_view = models.PositiveIntegerField(blank=True, null=True, default=0, verbose_name='Views')
    count_apply = models.PositiveIntegerField(blank=True, null=True, default=0, verbose_name='Applies')

    def __str__(self):
        return self.position_name

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.position_name)
        super(Position, self).save(*args, **kwargs)

    def days_passed(self):
        return (timezone.now() - self.pub_date).days

    def published_ago(self):
        d = self.days_passed()
        if d <= 1:
            return "Today"
        elif 1 < d <= 2:
            return "Yesterday"
        elif 2 < d <= 7:
            return "This week"
        elif 7 < d <= 30:
            return "This month"
        elif 30 < d <= 60:
            return "Last month"
        else:
            return "Long time ago"

    def get_absolute_url(self):
        return reverse('mycatalog:position_detail', args=[self.id, self.slug])

    @property
    def get_employment_type_value(self):
        if self.employment_type == self.EMPLOYMENT_TYPE_FULLTIME:
            return ''
        else:
            return self.get_employment_type_display()

    def get_salary(self):
        measures = self.salary_currency
        if self.salary_frequency != self.SALARY_FREQUENCY_YEAR:
            measures += ' %s' % self.get_salary_frequency_display()

        if self.salary_from and self.salary_to:
            return '%s-%s %s' % (self.salary_from, self.salary_to, measures)
        elif self.salary_from and not self.salary_to:
            return 'From %s %s' % (self.salary_from, measures)
        elif not self.salary_from and self.salary_to:
            return 'Up to %s %s' % (self.salary_to, measures)
        else:
            return ''

    def has_keywords(self):
        if self.keyword_ref.all():
            return True
        else:
            return False

    def has_responsibilities(self):
        if self.responsibilities:
            return True
        else:
            return False

    def has_requirements(self):
        if self.requirements:
            return True
        else:
            return False

    def has_how_to_apply(self):
        if self.how_to_apply:
            return True
        else:
            return False

    def has_apply_email_or_url(self):
        if self.apply_email or self.apply_url:
            return True
        else:
            return False

    def increment_view_counter(self):
        self.count_view = F('count_view') + 1
        self.save()

    def increment_apply_counter(self):
        self.count_apply = F('count_apply') + 1
        self.save()

    has_keywords.boolean = True
    has_keywords.short_description = 'Kwds'
    has_responsibilities.boolean = True
    has_responsibilities.short_description = 'Resps'
    has_requirements.boolean = True
    has_requirements.short_description = 'Reqs'
    has_how_to_apply.boolean = True
    has_how_to_apply.short_description = 'H-To-Ap'
    has_apply_email_or_url.boolean = True
    has_apply_email_or_url.short_description = 'ML-URL'


class CompanyBenefit(models.Model):  # бенефиты компании для всех вакансий
    benefit_name = models.CharField(max_length=250)
    company_name_ref = models.ForeignKey(Company, null=False, on_delete=models.CASCADE, blank=False)
