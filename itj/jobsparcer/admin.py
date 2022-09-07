import time
import requests

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.db import models
from django.forms import TextInput
from django.urls import path, reverse
from django.utils.safestring import mark_safe

from jobsparcer.models import ParcedTag, ParcedCompany, ParcedPosition, ParcingParam

from itj import settings
import json
import urllib.request
from bs4 import BeautifulSoup

from mycatalog.models import Keyword, Position, Company, CompanyUrl, URL_MAINSITE, URL_LINKEDIN, URL_CRUNCHBASE, \
    URL_FACEBOOK, URL_TWITTER
from mycatalog.utils import create_beautiful_soup_object


class ParcedPositionInline(admin.TabularInline):
    model = ParcedPosition
    extra = 1
    fields = ['position_name', 'position_parced_id', 'position_datetime', 'job_description', ]
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
    }


class ParcedPositionInlineForTags(admin.TabularInline):
    model = ParcedPosition.keyword_ref.through
    extra = 1


@admin.register(ParcingParam)
class ParcingParamAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'value',)
    list_editable = ('value',)
    list_display_links = ('name',)


@admin.register(ParcedTag)
class ParcedTagAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['tag', 'id', ]
    actions = ['copy_to_catalog', ]
    list_display = ('moved_to_catalog', 'tag', 'catalog_id')
    list_display_links = ('moved_to_catalog',)
    list_editable = ('tag',)
    list_filter = ('moved_to_catalog',)
    inlines = [
        ParcedPositionInlineForTags,
    ]

    def copy_to_catalog(self, request, queryset):
        for parced_tag in queryset:
            if not parced_tag.moved_to_catalog:
                catalog_keyword, created = Keyword.objects.get_or_create(keyword=parced_tag.tag,
                                                                         defaults={'parced_source_id': parced_tag.id})
                parced_tag.catalog_id = catalog_keyword.id
                parced_tag.moved_to_catalog = True
                parced_tag.save()

        if queryset.count() == 1:
            message_bit = "1 tag was"
        else:
            message_bit = "%s tags were" % queryset.count()
        self.message_user(request, "%s successfully copied to the main catalog." % message_bit)

    copy_to_catalog.short_description = 'Copy selected tags to the main catalog'


def get_or_create_catalog_company(parced_company):
    catalog_company, created = Company.objects.get_or_create(company_name=parced_company.company_name,
                                                             defaults={
                                                                 'parced_source_id': parced_company.id,
                                                                 'company_logo': parced_company.company_logo,
                                                                 'company_pitch': parced_company.company_pitch + '<br /><br />' + parced_company.cb_short_description,
                                                                 'description': parced_company.description + '<br /><br />' + parced_company.cb_long_description,
                                                                 'offices_locations': parced_company.offices_locations,
                                                                 'other_info': parced_company.cb_other})
    if not parced_company.moved_to_catalog:
        parced_company.catalog_id = catalog_company.id
        parced_company.moved_to_catalog = True
        parced_company.save()

    if parced_company.website:
        CompanyUrl.objects.get_or_create(company_name_ref=catalog_company, url_type=URL_MAINSITE,
                                         defaults={'url_text': parced_company.website})
    if parced_company.cb_web_path:
        CompanyUrl.objects.get_or_create(company_name_ref=catalog_company, url_type=URL_CRUNCHBASE,
                                         defaults={
                                             'url_text': 'https://www.crunchbase.com/' + parced_company.cb_web_path})
    if parced_company.cb_facebook_url:
        CompanyUrl.objects.get_or_create(company_name_ref=catalog_company, url_type=URL_FACEBOOK,
                                         defaults={'url_text': parced_company.cb_facebook_url})
    if parced_company.cb_twitter_url:
        CompanyUrl.objects.get_or_create(company_name_ref=catalog_company, url_type=URL_TWITTER,
                                         defaults={'url_text': parced_company.cb_twitter_url})
    if parced_company.cb_linkedin_url:
        CompanyUrl.objects.get_or_create(company_name_ref=catalog_company, url_type=URL_LINKEDIN,
                                         defaults={'url_text': parced_company.cb_linkedin_url})
    return catalog_company


@admin.register(ParcedCompany)
class ParcedCompanyAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['company_name', 'id', 'source', ]
    list_filter = ('edited_date', 'moved_to_catalog', 'cb_check',)
    list_display = (
        'id', 'moved_to_catalog', 'company_logo_tag', 'cb_logo_tag', 'company_name', 'cb_name', 'website',
        'edited_date', 'get_company_edit_url', 'source', 'cb_check',)
    list_display_links = ('company_name', 'edited_date',)
    list_editable = ['website', ]
    inlines = [
        ParcedPositionInline,
    ]
    fields = (('moved_to_catalog', 'company_name', 'offices_locations', 'website',),
              ('company_logo_tag', 'company_logo', 'company_logo_url',),
              ('company_pitch', 'description',),
              ('cb_short_description', 'cb_name', 'cb_web_path', 'cb_profile_image_url', 'cb_logo_tag', 'cb_logo',
               'cb_facebook_url', 'cb_twitter_url', 'cb_linkedin_url', 'cb_location', 'cb_long_description',
               'cb_other', 'cb_check',),
              ('edited_date', 'created_date',), 'catalog_id', 'source',)
    readonly_fields = ('company_logo_tag', 'edited_date', 'created_date', 'cb_logo_tag',)
    actions = ['copy_to_catalog', 'get_from_cb', ]

    def response_change(self, request, obj):
        if "_copy-cb-logo" in request.POST:
            obj.company_logo = obj.cb_logo
            obj.save()
            self.message_user(request, "CB logo is copied to main logo")
            return HttpResponseRedirect(".")
        if '_copy-cb-logo_to_main_catalog' in request.POST and obj.cb_logo and obj.catalog_id:
            catalog_company = Company.objects.get(id=obj.catalog_id)
            catalog_company.company_logo = obj.cb_logo
            catalog_company.save()
            self.message_user(request, "CB logo is copied to the corresponding company (ID=%s) in main catalog" % obj.catalog_id)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def get_company_edit_url(self, obj):
        if obj.catalog_id:
            company_edit_url = reverse('admin:mycatalog_company_change', args=(obj.catalog_id,))
            return mark_safe('<a href="%s" target="_blank">%s</a>' % (company_edit_url, obj.catalog_id))
        else:
            return '-'

    get_company_edit_url.short_description = 'Catalog ID'

    def get_from_cb_api(self, request, queryset):
        message_bit = ''
        for company in queryset:
            if company.website and (not company.source or company.source.find('CBAPI') == -1):
                try:
                    website = ("").join(
                        company.website.strip().replace("http://", "").replace("https://", "").replace("www.", "").rsplit(
                            "/", 1))
                    url = 'https://api.crunchbase.com/v3.1/odm-organizations?domain_name=' + website + '&user_key=2a31f88541fe8fff738f9cebe7653967'
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    r = urllib.request.urlopen(req).read()
                    json_content = json.loads(r.decode('utf-8'))
                    if json_content['data']['paging']['total_items'] != 0:
                        item = json_content['data']['items'][0]['properties']
                        cb_web_path = ''
                        if item['web_path']:
                            cb_web_path = item['web_path']

                        cb_name = ''
                        if item['name']:
                            cb_name = item['name']

                        cb_short_description = ''
                        if item['short_description']:
                            cb_short_description = item['short_description']

                        cb_profile_image_url = ''
                        if item['profile_image_url']:
                            cb_profile_image_url = item['profile_image_url']

                        cb_facebook_url = ''
                        if item['facebook_url']:
                            cb_facebook_url = item['facebook_url']

                        cb_twitter_url = ''
                        if item['twitter_url']:
                            cb_twitter_url = item['twitter_url']

                        cb_linkedin_url = ''
                        if item['linkedin_url']:
                            cb_linkedin_url = item['linkedin_url']

                        cb_location = ''
                        if item['city_name']:
                            cb_location = cb_location + item['city_name']
                        if item['region_name']:
                            cb_location = cb_location + ' ' + item['region_name']
                        if item['country_code']:
                            cb_location = cb_location + ' ' + item['country_code']

                        company.__dict__.update(source=str(company.source or '') + '+CBAPI', cb_web_path=cb_web_path,
                                                cb_name=cb_name,
                                                cb_short_description=cb_short_description,
                                                cb_profile_image_url=cb_profile_image_url,
                                                cb_facebook_url=cb_facebook_url,
                                                cb_twitter_url=cb_twitter_url, cb_linkedin_url=cb_linkedin_url,
                                                cb_location=cb_location, cb_check=True)
                        company.save()
                    else:
                        company.__dict__.update(source=str(company.source or '') + '+noCBAPI', cb_check=True)
                        company.save()
                    time.sleep(2)
                except Exception as err:
                    message_bit = 'Exception occurred: %s' % err
                    break
        self.message_user(request, "Number of processed companies: %s. %s" % (queryset.count(), message_bit))

    get_from_cb_api.short_description = 'Get data from CB API for selected companies'

    def get_from_cb_site2(self, request, queryset):
        message_bit = ''
        for company in queryset:
            if company.cb_web_path and (not company.source or company.source.find('CBsite') == -1):
                try:
                    bs_obj = create_beautiful_soup_object('https://www.crunchbase.com/' + company.cb_web_path)

                    cb_info = bs_obj.find('section-layout', {'id': 'section-overview'}).findAll('span', {
                        'class': 'field-value'})

                    plain_text = ''
                    for cb in cb_info:
                        plain_text = plain_text + '<br />' + cb.text
                    if bs_obj.find('section-layout', {'id': 'section-funding-rounds'}):
                        cb_info = bs_obj.find('section-layout', {'id': 'section-funding-rounds'}).findAll(
                            'phrase-list-card', {'class': 'ng-star-inserted'})
                        plain_text = plain_text + '<h2>Funding rounds</h2>'
                        for cb in cb_info:
                            plain_text = plain_text + '<p>' + cb.text + '</p>'

                    cb_long_description = ''
                    if bs_obj.find('description-card'):
                        cb_long_description = bs_obj.find('description-card').find('p').text

                    company.__dict__.update(source=str(company.source or '') + '+CBsite', cb_other=plain_text,
                                            cb_long_description=cb_long_description)
                    company.save()

                    time.sleep(5)

                except Exception as err:
                    message_bit = 'Exception occurred: %s' % err
                    break
        self.message_user(request, "Number of processed companies: %s. %s" % (queryset.count(), message_bit))

    get_from_cb_site2.short_description = 'Get data from CB site for selected companies - method2'

    def get_from_cb(self, request, queryset):
        self.get_from_cb_api(request, queryset)
        self.get_from_cb_site2(request, queryset)
        self.copy_to_catalog(request, queryset)
        if queryset.count() == 1:
            message_bit = "1 company was"
        else:
            message_bit = "%s companies were" % queryset.count()
        self.message_user(request, "%s processed." % message_bit)

    get_from_cb.short_description = 'Get data from CB API/Website and copy to the main catalog'

    def copy_to_catalog(self, request, queryset):
        for parced_company in queryset:
            if not parced_company.moved_to_catalog:
                get_or_create_catalog_company(parced_company)

        if queryset.count() == 1:
            message_bit = "1 company was"
        else:
            message_bit = "%s companies were" % queryset.count()
        self.message_user(request, "%s successfully copied to the main catalog." % message_bit)

    copy_to_catalog.short_description = 'Copy selected companies to the main catalog'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('load_companies_from_weworkremotely/',
                 self.admin_site.admin_view(self.load_companies_from_weworkremotely),
                 name="load_companies_from_weworkremotely"),
        ]
        return my_urls + urls

    @staticmethod
    def load_companies_from_weworkremotely(request):
        open_url = 'https://weworkremotely.com/remote-companies?page=' + ParcingParam.objects.get(
            name='wwr_companies_page_start').value

        # here we will scrap remote-companies pages until 'next' link is available on the page or ofset param is over
        for i in range(int(ParcingParam.objects.get(name='wwr_companies_page_ofset').value)):
            html = urllib.request.urlopen(open_url)
            bs_obj = BeautifulSoup(html, features="html.parser")
            companies_list = bs_obj.article.findAll('ul')

            for company in companies_list:
                company_name = company.li.find('span', {'class': 'company'}).text

                pitch = ''
                if company.li.find('span', {'class': 'company-title'}):
                    pitch = company.li.find('span', {'class': 'company-title'}).text
                wwr_company_url = company.li.find('a')['href']

                logo_url = ''
                if company.li.find('div', {'class': 'flag-logo'}):
                    logo_url = company.li.find('div', {'class': 'flag-logo'})['style'].split("url(")[1].split(")")[0]

                # open directly company page on WWR in order to scrap detailed description, location and website
                bs_company_obj = BeautifulSoup(urllib.request.urlopen('https://weworkremotely.com' + wwr_company_url),
                                               features="html.parser")
                description = ''
                if bs_company_obj.find('div', {'class': 'listing-container'}).findAll('div'):
                    description_parts = bs_company_obj.find('div', {'class': 'listing-container'}).findAll('div')
                    for description_part in description_parts:
                        description = description + description_part.prettify()

                website = ''
                if bs_company_obj.find('div', {'class': 'listing-tools'}).findAll('a', recursive=False):
                    website = bs_company_obj.find('div', {'class': 'listing-tools'}).findAll('a', recursive=False)[
                        -1].get('href')

                location = ''
                if bs_company_obj.find('div', {'class': 'listing-header-container'}).find('h3'):
                    location = bs_company_obj.find('div', {'class': 'listing-header-container'}).find('h3').text

                ParcedCompany.objects.update_or_create(company_name=company_name, defaults={
                    'company_logo_url': logo_url, 'company_pitch': pitch, 'description': description,
                    'offices_locations': location, 'website': website, 'source': 'WWR', })

                time.sleep(15)  # wait for 15 seconds in order to not DDos WWR website

            next_url_tag = bs_obj.article.find('nav', {'class': 'pagination'}).find('span', {'class': 'next'})
            if not next_url_tag:
                break
            else:
                open_url = 'https://weworkremotely.com' + next_url_tag.find('a')['href']

        return redirect('/' + settings.ADMIN_URL + 'jobsparcer/parcedcompany/')


@admin.register(ParcedPosition)
class ParcedPositionAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['company_name_ref__company_name', 'position_name', 'position_parced_id']
    list_filter = ('edited_date', 'position_datetime', 'moved_to_catalog')
    list_display = (
        'moved_to_catalog', 'company_name_ref', 'position_parced_id', 'position_name', 'position_datetime',
        'edited_date', 'created_date', 'source',)
    list_display_links = (
        'company_name_ref', 'position_parced_id', 'position_name',)
    filter_horizontal = ('keyword_ref',)
    actions = ['copy_to_catalog', ]
    ordering = ('-position_datetime',)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('load_from_remoteok/', self.admin_site.admin_view(self.load_from_remoteok), name="load_from_remoteok"),
        ]
        return my_urls + urls

    @staticmethod
    def load_from_remoteok(request):
        url = 'https://remoteok.io/api'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req).read()
        json_content = json.loads(r.decode('utf-8'))

        for item in json_content[1:]:  # [1:] is to skip the first element in json_content
            verified = False
            original = False
            if 'verified' in item:
                verified = True
            if 'original' in item:
                original = True
            if item['company'] != '':
                company, created = ParcedCompany.objects.update_or_create(company_name=item['company'], defaults={
                    'company_logo_url': item['company_logo'], 'source': 'Remote OK', })

                if item['position'] != '':
                    position, created = ParcedPosition.objects.update_or_create(position_parced_id=item['id'],
                                                                                defaults={
                                                                                    'position_name': item['position'],
                                                                                    'position_slug': item['slug'],
                                                                                    'epoch': item['epoch'],
                                                                                    'position_datetime': item['date'],
                                                                                    'company_name_ref': company,
                                                                                    'job_description': item[
                                                                                        'description'],
                                                                                    'verified': verified,
                                                                                    'original': original,
                                                                                    'job_url': item['url'],
                                                                                    'source': 'Remote OK', })

                    for tag in item['tags']:
                        tg, created = ParcedTag.objects.get_or_create(tag=tag)
                        position.keyword_ref.add(tg)

        return redirect('/' + settings.ADMIN_URL + 'jobsparcer/parcedposition/')

    def copy_to_catalog(self, request, queryset):
        for parced_position in queryset:
            if not parced_position.moved_to_catalog:
                catalog_company = get_or_create_catalog_company(parced_position.company_name_ref)

                catalog_position, created = Position.objects.get_or_create(parced_source_id=parced_position.id,
                                                                           defaults={
                                                                               'position_name': parced_position.position_name,
                                                                               'source': parced_position.source,
                                                                               'source_url': parced_position.job_url,
                                                                               'job_description': parced_position.job_description,
                                                                               'company_name_ref': catalog_company})
                parced_position.catalog_id = catalog_position.id
                parced_position.moved_to_catalog = True
                parced_position.save()

                for parced_tag in parced_position.keyword_ref.all():
                    catalog_keyword, created = Keyword.objects.get_or_create(keyword=parced_tag.tag,
                                                                             defaults={
                                                                                 'parced_source_id': parced_tag.id})
                    if not parced_tag.moved_to_catalog:
                        parced_tag.catalog_id = catalog_keyword.id
                        parced_tag.moved_to_catalog = True
                        parced_tag.save()

                    catalog_position.keyword_ref.add(catalog_keyword)

        if queryset.count() == 1:
            message_bit = "1 position was"
        else:
            message_bit = "%s positions were" % queryset.count()
        self.message_user(request, "%s successfully copied to the main catalog." % message_bit)

    copy_to_catalog.short_description = 'Copy selected positions and its companies to the main catalog'
