import ast
from django.contrib import admin
from django.contrib.postgres.search import SearchVector
from django.db import models
from django.db.models import Q
from django.forms import TextInput
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.storage import staticfiles_storage
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
import requests
from urllib.parse import urlparse

from mycatalog.models import Company, CompanyUrl, Category, Position, CompanyBenefit, Keyword, KeywordSynonym, \
    CompanyDomainsClassifier, CompanyPositionParsingRule, CompanyPositionUrlIgnore, CategoryKeyword
from mycatalog.utils import create_beautiful_soup_object, create_beautiful_soup_object_using_selenium, \
    cleanup_beautifulsoup_object
from mycatalog.forms import ParsingPositionsForm


class PositionInline(admin.TabularInline):
    model = Position
    fields = ['archive_flag', 'enabled_flag', 'position_name', 'category_name_ref', 'apply_url']
    extra = 1


class PositionInlineForKeywords(admin.TabularInline):
    model = Position.keyword_ref.through
    extra = 1


class CompanyBenefitInline(admin.TabularInline):
    model = CompanyBenefit
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '100'})},
    }
    extra = 1


class CompanyUrlInline(admin.TabularInline):
    model = CompanyUrl
    fields = ('url_type', 'url_text')
    formfield_overrides = {
        models.URLField: {'widget': TextInput(attrs={'size': '100'})},
    }
    extra = 1


class CompanyPositionParsingRuleInline(admin.TabularInline):
    model = CompanyPositionParsingRule
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
    }
    extra = 4


class CompanyPositionUrlIgnoreInline(admin.TabularInline):
    model = CompanyPositionUrlIgnore
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
    }
    extra = 1


class CategoryKeywordInline(admin.TabularInline):
    model = CategoryKeyword
    extra = 1


class KeywordSynonymInline(admin.TabularInline):
    model = KeywordSynonym
    extra = 4


@admin.register(CompanyDomainsClassifier)
class CompanyDomainsClassifierAdmin(admin.ModelAdmin):
    save_on_top = True
    prepopulated_fields = {"slug": ("domain_name",)}
    list_display = ('domain_name', 'slug',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    inlines = [
        CompanyBenefitInline, CompanyUrlInline, CompanyPositionParsingRuleInline, CompanyPositionUrlIgnoreInline,
        PositionInline
    ]
    save_on_top = True
    list_display = (
        'id', 'enabled_flag', 'company_logo_tag', 'company_name', 'slug', 'positions_url', 'edited_date',
        'get_positions_list_url', 'get_positions_parsing_url')
    list_display_links = ('company_logo_tag', 'company_name',)
    readonly_fields = ('company_logo_tag', 'pub_date', 'edited_date',)
    list_editable = ('enabled_flag',)
    list_filter = ('enabled_flag', 'edited_date',)
    fields = (
        ('enabled_flag', 'pub_date', 'edited_date'), ('company_name', 'slug'), ('company_logo_tag', 'company_logo'),
        ('offices_locations', 'company_email', 'positions_url', 'number_of_people', 'founded_year'),
        ('other_info', 'company_pitch', 'description',),
        ('funding', 'raised', 'num_of_rounds', 'last_round_announced_date'),
        'domain_name', 'parced_source_id',)
    search_fields = ['company_name', 'offices_locations', 'id', ]
    prepopulated_fields = {"slug": ("company_name",)}
    filter_horizontal = ('domain_name',)
    actions = ['make_published', ]

    def get_positions_list_url(self, obj):
        positions_list_url = reverse('admin:mycatalog_position_changelist') + '?q=' + obj.company_name
        return mark_safe('<a href="%s" target="_blank">%s</a>' % (positions_list_url, 'positions'))

    get_positions_list_url.short_description = 'Positions list'

    def make_published(self, request, queryset):
        rows_updated = queryset.update(enabled_flag=True)
        if rows_updated == 1:
            message_bit = "1 company was"
        else:
            message_bit = "%s companies were" % rows_updated
        self.message_user(request, "%s successfully marked as published." % message_bit)

    make_published.short_description = "Mark selected companies as published"

    def get_positions_parsing_url(self, obj):
        check_and_get_new_positions_url = reverse('admin:check_and_get_new_positions', args=(obj.id,))
        latest_pub_date = Position.objects.filter(company_name_ref=obj).latest('pub_date').pub_date.strftime(
            "%d.%m.%Y %H:%M")
        if CompanyPositionParsingRule.objects.filter(company_name_ref=obj).count() > 0:
            return mark_safe('<a href="%s" target="_blank">%s</a>' % (check_and_get_new_positions_url, latest_pub_date))
        return latest_pub_date

    get_positions_parsing_url.short_description = 'Latest position pub date'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('check_and_get_new_positions/<int:pk>', self.admin_site.admin_view(self.check_and_get_new_positions),
                 name="check_and_get_new_positions"),
        ]
        return my_urls + urls

    def check_and_get_new_positions(self, request, pk):
        company = Company.objects.get(id=pk)
        positions_dict = {}
        position_dict = {}
        db_positions_to_archive = {}

        if request.method == 'POST':
            form = ParsingPositionsForm(request.POST)

            if form.is_valid():
                positions_dict = ast.literal_eval(form.cleaned_data['hidden_positions_dict'])
                db_positions_to_archive = ast.literal_eval(form.cleaned_data['db_positions_to_archive'])
                parsing_rules_dict = ast.literal_eval(form.cleaned_data['parsing_rules_dict'])
                positions_to_add = request.POST.copy()
                del positions_to_add['csrfmiddlewaretoken']
                del positions_to_add['hidden_positions_dict']
                del positions_to_add['db_positions_to_archive']
                del positions_to_add['parsing_rules_dict']

                self.save_chosen_positions_to_db(positions_to_add, parsing_rules_dict, company)
                self.cleanup_company_positions_ignore_list(positions_to_add, company)
                self.fulfill_company_positions_ignore_list(positions_dict, positions_to_add, company)
                self.archive_old_positions(db_positions_to_archive)

                return HttpResponseRedirect(
                    reverse('admin:mycatalog_position_changelist') + '?q=' + company.company_name)
            return HttpResponse('Form is not valid')
        else:
            try:
                parsing_rules = CompanyPositionParsingRule.objects.filter(company_name_ref=company)
                parsing_rules_dict = {}
                for rule in parsing_rules:
                    parsing_rules_dict[rule.parsing_rule] = rule.parsing_path

                positions_raw, bs_obj = self.parse_positions_list(parsing_rules_dict, company)
                if positions_raw == 'message':
                    return HttpResponse(bs_obj)
                positions_list = positions_raw.findAll('a', href=True)
                if positions_list:
                    positions_dict = self.fill_positions_dict(company.positions_url, positions_list, parsing_rules_dict)

                    # checking if position already exists in DB, so we don't have to process it again
                    for db_position in Position.objects.filter(company_name_ref=company, archive_flag=False):
                        arch = True
                        for key, value in positions_dict.items():
                            if key == db_position.apply_url:
                                value[1] = 'db'
                                value[2] = db_position.position_name
                                arch = False
                                break
                        if arch:
                            db_positions_to_archive[db_position.id] = [db_position.position_name, db_position.apply_url]

                    # checking if position exists in ignore list, like one not remote or not of IT profile
                    for ignore_position in CompanyPositionUrlIgnore.objects.filter(company_name_ref=company):
                        for key, value in positions_dict.items():
                            if key == ignore_position.position_url:
                                if value[1] != 'db':  # won't ignore 'db' positions as we already have them in DB
                                    value[1] = 'ignore'
                                    value[2] = ignore_position.position_name

                    positions_html = self.color_bs_object_links(positions_dict, positions_raw, bs_obj).prettify()

                    # here we parse single position as example
                    position_dict = self.parse_position_page(positions_list[0]['href'], parsing_rules_dict, company)
                    if 'message' in position_dict:
                        return HttpResponse(position_dict['message'])
                else:
                    positions_html = 'no URLs found in the positions page'

                form = ParsingPositionsForm(initial={'hidden_positions_dict': positions_dict,
                                                     'db_positions_to_archive': db_positions_to_archive,
                                                     'parsing_rules_dict': parsing_rules_dict})
            except Exception as err:
                return HttpResponse(err)

        return render(request, 'admin/mycatalog/check_and_get_new_positions.html',
                      {'form': form,
                       'company': company,
                       'positions_html': positions_html,
                       'positions_dict': positions_dict,
                       'db_positions_to_archive': db_positions_to_archive,
                       'position_dict': position_dict})

    def parse_positions_list(self, parsing_rules_dict, company):
        if CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST not in parsing_rules_dict:
            return 'message', "No positions rule set"

        if CompanyPositionParsingRule.PARSING_RULE_USE_SELENIUM in parsing_rules_dict:
            bs_obj = create_beautiful_soup_object_using_selenium(company.positions_url)
        else:
            bs_obj = create_beautiful_soup_object(company.positions_url)

        positions_raw = bs_obj.select(parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST])
        if not positions_raw:
            return 'message', "Positions list rule is wrong. Can't parse it"

        positions_raw = positions_raw[0]
        if positions_raw.name == 'iframe':
            if CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST_IFRAME not in parsing_rules_dict:
                return 'message', "No positions rule FOR IFRAME set"

            if CompanyPositionParsingRule.PARSING_RULE_USE_SELENIUM in parsing_rules_dict:
                bs_obj = create_beautiful_soup_object_using_selenium(positions_raw.attrs['src'])
            else:
                bs_obj = create_beautiful_soup_object(positions_raw.attrs['src'])

            positions_raw = bs_obj.select(
                parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST_IFRAME])
            if not positions_raw:
                return 'message', "Positions list rule FOR IFRAME is wrong. Can't parse it"
            positions_raw = positions_raw[0]

        positions_exclude_rules = CompanyPositionParsingRule.objects.filter(
            company_name_ref=company,
            parsing_rule=CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST_EXCLUDE)
        for exclude_rule in positions_exclude_rules:
            unwanted_content = positions_raw.select(exclude_rule.parsing_path)
            for unwanted in unwanted_content:
                unwanted.extract()
        return positions_raw, bs_obj

    def fill_positions_dict(self, positions_url, positions_list, parsing_rules_dict):
        company_website = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(positions_url))
        positions_dict = {}
        for a in positions_list:
            if CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST_URL_PREFIX in parsing_rules_dict:
                a['href'] = parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITIONS_LIST_URL_PREFIX] + a['href']
            if a['href'].startswith('/'):
                a['href'] = ("").join(company_website.rsplit("/", 1)) + a['href']
            positions_dict[a['href']] = [str(a.get_text().strip()), 'new', '']
        return positions_dict

    def color_bs_object_links(self, positions_dict, positions_raw, bs_obj):
        for key, value in positions_dict.items():
            css_selector = 'a[href="%s"]' % key
            tag = positions_raw.select(css_selector)[0]

            if value[1] == 'db':
                tag['class'] = 'text-secondary'
            else:
                new_tag_checkbox = bs_obj.new_tag("input", attrs={'type': 'checkbox', 'name': key, 'value': 'add'})
                if value[1] == 'new':
                    tag['class'] = 'text-success'
                    new_tag_checkbox['checked'] = 'checked'
                else:  # value[1] == 'ignore'
                    tag['class'] = 'text-secondary'
                tag.insert_before(new_tag_checkbox)
        return positions_raw

    def parse_position_page(self, url, parsing_rules_dict, company):
        position_dict = {'position_url_to_parse': url}

        if CompanyPositionParsingRule.PARSING_RULE_USE_SELENIUM in parsing_rules_dict:
            bs_obj_position = create_beautiful_soup_object_using_selenium(position_dict['position_url_to_parse'])
        else:
            bs_obj_position = create_beautiful_soup_object(position_dict['position_url_to_parse'])

        if CompanyPositionParsingRule.PARSING_RULE_POSITION_IFRAME in parsing_rules_dict:
            bs_obj_position = bs_obj_position.select(
                parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITION_IFRAME])
            if not bs_obj_position:
                return {'message': "Position rule FOR IFRAME is wrong. Can't parse it"}

            bs_obj_position = bs_obj_position[0]

            if CompanyPositionParsingRule.PARSING_RULE_USE_SELENIUM in parsing_rules_dict:
                bs_obj_position = create_beautiful_soup_object_using_selenium(bs_obj_position.attrs['src'])
            else:
                bs_obj_position = create_beautiful_soup_object(bs_obj_position.attrs['src'])

        if CompanyPositionParsingRule.PARSING_RULE_POSITION_NAME in parsing_rules_dict:
            title_raw = bs_obj_position.select(
                parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITION_NAME])
            if title_raw:
                position_dict['title_html'] = title_raw[0].text.strip()
            else:
                return {'message': "Can't parse title"}

        if CompanyPositionParsingRule.PARSING_RULE_POSITION_LOCATION in parsing_rules_dict:
            location_raw = bs_obj_position.select(
                parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITION_LOCATION])
            if location_raw:
                position_dict['location_html'] = location_raw[0].text.strip()

        if CompanyPositionParsingRule.PARSING_RULE_POSITION_DESCRIPTION in parsing_rules_dict:
            description_raw = bs_obj_position.select(
                parsing_rules_dict[CompanyPositionParsingRule.PARSING_RULE_POSITION_DESCRIPTION])
            if description_raw:
                description_raw = description_raw[0]
                description_exclude_rules = CompanyPositionParsingRule.objects.filter(
                    company_name_ref=company,
                    parsing_rule=CompanyPositionParsingRule.PARSING_RULE_POSITION_DESCRIPTION_EXCLUDE)

                for exclude_rule in description_exclude_rules:
                    unwanted_content = description_raw.select(exclude_rule.parsing_path)
                    for unwanted in unwanted_content:
                        unwanted.extract()
                cleanup_beautifulsoup_object(bs_obj_position, unwrap_a=True)

                position_dict['keywords'] = self.get_keywords_from_text(description_raw.text)
                position_dict['description_html'] = description_raw.prettify()
            else:
                return {'message': "Can't parse description"}
        return position_dict

    def get_keywords_from_text(self, description_text):
        parsed_keywords = {}
        desc = description_text.replace('\n', ' ').replace('.', ' ').replace(',', ' ').\
            replace('(', ' ').replace(')', ' ').replace('/', ' ').lower()

        keywords = Keyword.objects.all()
        for keyword in keywords:
            cnt = desc.count(' ' + keyword.keyword.replace('/', ' ').lower() + ' ')
            if cnt:
                parsed_keywords[keyword.keyword] = [keyword.id, cnt]
        synonyms = KeywordSynonym.objects.all()
        for synonym in synonyms:
            cnt = desc.count(' ' + synonym.synonym.lower() + ' ')
            if cnt:
                if synonym.keyword_ref.keyword in parsed_keywords:
                    parsed_keywords[synonym.keyword_ref.keyword] = [synonym.keyword_ref.id,
                                                                    parsed_keywords[synonym.keyword_ref.keyword][
                                                                        1] + cnt]
                else:
                    parsed_keywords[synonym.keyword_ref.keyword] = [synonym.keyword_ref.id, cnt]
        for key, value in list(parsed_keywords.items()):
            if value[1] == 1:
                del parsed_keywords[key]

        return parsed_keywords

    def save_chosen_positions_to_db(self, positions_to_add, parsing_rules_dict, company):
        publish_datetime = timezone.now()
        for position_url in positions_to_add:
            position_dict = self.parse_position_page(position_url, parsing_rules_dict, company)
            if 'message' not in position_dict:  # i.e. parsing was successful
                new_position = Position()
                new_position.position_name = position_dict['title_html']
                new_position.company_name_ref = company
                if 'location_html' in position_dict:
                    new_position.locations = position_dict['location_html']
                new_position.apply_url = position_dict['position_url_to_parse']
                new_position.job_description = position_dict['description_html']
                new_position.pub_date = publish_datetime
                # shift 15 minutes in order to shuffle positions of different companies on index page
                publish_datetime = publish_datetime + timedelta(minutes=15)

                category_id = self.find_category_by_keyword(position_dict['title_html'])
                if category_id != 0:
                    new_position.category_name_ref_id = category_id
                new_position.save()

                if 'keywords' in position_dict:
                    for key, value in position_dict['keywords'].items():
                        new_position.keyword_ref.add(value[0])

    def find_category_by_keyword(self, position_name):
        categories_list = ()
        for search_word in position_name.split():
            suggested_categories = CategoryKeyword.objects.annotate(search=SearchVector('keyword', )).filter(
                Q(search__icontains=search_word) | Q(search=search_word)).distinct('category_name_ref')
            categories_count = suggested_categories.count()
            if categories_count > 1:
                return 0
            if categories_count == 1:
                categories_list += (suggested_categories[0].category_name_ref_id,)
        if len(categories_list) == 0:
            return 0
        else:
            for i in range(len(categories_list)):
                for j in range(i + 1, len(categories_list)):
                    if categories_list[i] != categories_list[j]:
                        return 0
        return categories_list[0]

    def cleanup_company_positions_ignore_list(self, positions_to_add, company):
        for position_url in positions_to_add:
            CompanyPositionUrlIgnore.objects.filter(position_url=position_url, company_name_ref=company).delete()

    def fulfill_company_positions_ignore_list(self, positions_dict, positions_to_add, company):
        for key, value in list(positions_dict.items()):  # iterating to keep only 'ignore' positions
            if value[1] == 'db':  # i.e. not 'ignore' or 'new'
                del positions_dict[key]
            for position in positions_to_add:
                if position == key:  # if URL exists in the list of positions to add, delete it from ignore list
                    del positions_dict[key]
        for key, value in positions_dict.items():
            new_ignore_url = CompanyPositionUrlIgnore()
            new_ignore_url.position_url = key
            new_ignore_url.position_name = value[0]
            new_ignore_url.company_name_ref = company
            new_ignore_url.save()

    def archive_old_positions(self, db_positions_to_archive):
        for key in db_positions_to_archive:
            Position.objects.filter(id=key).update(archive_flag=True)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['category_name', 'categorykeyword__keyword', ]
    prepopulated_fields = {"slug": ("category_name",)}
    list_display = ('id', 'category_name', 'slug', 'get_keywords',)
    list_display_links = ('id', 'category_name',)
    inlines = [CategoryKeywordInline, ]

    def get_keywords(self, obj):
        return ", ".join([k.keyword for k in obj.categorykeyword_set.all()])

    get_keywords.short_description = 'Keywords'


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['keyword', 'id', 'keywordsynonym__synonym']
    prepopulated_fields = {"slug": ("keyword",)}
    list_display = ('keyword', 'slug', 'get_synonyms',)
    list_editable = ('keyword',)
    list_display_links = ('slug',)
    inlines = [
        KeywordSynonymInline, PositionInlineForKeywords,
    ]

    def get_synonyms(self, obj):
        return ", ".join([s.synonym for s in obj.keywordsynonym_set.all()])

    get_synonyms.short_description = 'Synonyms'


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display_links = ('position_name', 'get_company_edit_url',)
    list_display = ('archive_flag', 'enabled_flag', 'position_name', 'get_company_logo', 'get_company_edit_url',
                    'category_name_ref', 'locations', 'work_worldwide', 'get_creation_date',
                    # 'has_responsibilities', 'has_requirements', 'has_how_to_apply',
                    'has_apply_email_or_url', 'get_description', 'get_keywords', 'count_view', 'count_apply',)
    list_editable = ('enabled_flag', 'category_name_ref', 'locations', 'work_worldwide')
    list_filter = ('enabled_flag', 'archive_flag', 'pub_date')
    save_on_top = True
    readonly_fields = ('edited_date', 'count_view', 'count_apply', 'id',)
    search_fields = ['company_name_ref__company_name', 'category_name_ref__category_name', 'position_name', 'id', ]
    autocomplete_fields = ['category_name_ref', 'company_name_ref', ]
    prepopulated_fields = {"slug": ("position_name",)}
    # date_hierarchy = 'pub_date'
    fieldsets = (
        (None, {
            'fields': (('enabled_flag', 'archive_flag', 'pub_date', 'edited_date', 'id',),
                       ('position_name', 'company_name_ref', 'category_name_ref'),)
        }),
        ('Locations, language, visa and employment type', {
            'fields': (('employment_type', 'locations', 'work_worldwide', 'language', 'visa_sponsorship',),)
        }),
        ('Descriptions', {
            'fields': ('apply_url', 'job_description', 'keyword_ref', 'responsibilities', 'requirements')
        }),
        ('Apply', {
            'fields': ('how_to_apply', 'apply_email',)
        }),
        ('Salary', {
            'classes': ('collapse',),
            'fields': (('salary_from', 'salary_to', 'salary_currency', 'salary_frequency',),)
        }),
        ('Other', {
            'classes': ('collapse',),
            'fields': ('position_id_redirect_to', 'slug', 'count_view', 'count_apply',)
        }),
        ('Parced', {
            'classes': ('collapse',),
            'fields': ('source', 'source_url', 'parced_source_id',)
        }),
    )
    filter_horizontal = ('keyword_ref',)
    actions = ['make_published', ]
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
    }

    def get_creation_date(self, obj):
        return str(obj.pub_date.strftime("%d.%m.%Y %H:%M")) + ' (' + str((timezone.now() - obj.pub_date).days) + ')'

    get_creation_date.short_description = 'Date created'

    def get_company_edit_url(self, obj):
        company_edit_url = reverse('admin:mycatalog_company_change', args=(obj.company_name_ref.id,))
        return mark_safe('<a href="%s" target="_blank">%s</a>' % (company_edit_url, obj.company_name_ref.company_name))

    get_company_edit_url.short_description = 'Company'

    def get_company_logo(self, obj):
        if obj.company_name_ref.company_logo:
            logo = mark_safe(
                '<img src="%s" width="30" />' % obj.company_name_ref.company_logo.url)
        else:
            logo = mark_safe('<img src="' + staticfiles_storage.url('mycatalog/nologo.png') + '" width="30" />')
        return logo

    get_company_logo.short_description = 'Logo'

    def get_keywords(self, obj):
        return ", ".join([k.keyword for k in obj.keyword_ref.all()])

    get_keywords.short_description = 'Keywords'

    def get_description(self, obj):
        desc = obj.job_description.replace('"', ' ').replace("'", ' ')
        return mark_safe("<a tabindex='0' data-toggle='popover' data-content='%s'>desc</a>" % desc)
    get_description.short_description = 'Desc'

    def make_published(self, request, queryset):
        rows_updated = queryset.update(enabled_flag=True)
        if rows_updated == 1:
            message_bit = "1 position was"
        else:
            message_bit = "%s positions were" % rows_updated
        self.message_user(request, "%s successfully marked as published." % message_bit)

    make_published.short_description = "Mark selected positions as published"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('archive_too_old_positions/', self.admin_site.admin_view(self.archive_too_old_positions),
                 name="archive_too_old_positions"),
        ]
        return my_urls + urls

    @staticmethod
    def archive_too_old_positions(request):
        d_to_filter = 80
        days_to_filter = timezone.now() - timedelta(days=d_to_filter)
        positions_archived = Position.objects.filter(pub_date__lt=days_to_filter, archive_flag=False).update(
            archive_flag=True)
        positions_to_check = Position.objects.filter(archive_flag=False, enabled_flag=True)
        archive_str = '<strong>Automatically archived positions</strong><br>--------------------<br>'
        ok_str = '<strong>Actual positions</strong><br>--------------------<br>'
        manual_check_str = '<strong>Please check these positions manually</strong><br>--------------------<br>'
        for position in positions_to_check:
            if position.apply_url:
                ur = ''
                try:
                    req = requests.get(position.apply_url)
                    s_code = req.status_code
                    ur = req.url
                except:
                    s_code = 'broken link'

                position_line = str(s_code) + ' || <a href="' + reverse('admin:mycatalog_position_change',
                                                                        args=(position.id,)) + '">' + str(
                    position.id) + '</a> || ' + position.position_name + ' || <a href="' + position.apply_url + '">' + position.apply_url + '</a> || '
                if s_code == 200:
                    if ur == position.apply_url:
                        ok_str += position_line + '<br>'
                    else:
                        manual_check_str += position_line + ur + '<br>'
                else:
                    archive_str += position_line + ur + '<br>'
                    position.archive_flag = True
                    position.save()

        return HttpResponse("%s positions were archived due to age more than %s days<br><br>%s<br><br>%s<br><br>%s" % (
            positions_archived, str(d_to_filter), archive_str, manual_check_str, ok_str))
