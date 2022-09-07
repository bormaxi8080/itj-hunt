from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from mycatalog.models import Position, Company, Keyword, Category


class CompanySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Company.objects.filter(enabled_flag=True)

    def lastmod(self, obj):
        return obj.pub_date


class PositionSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.5
    protocol = "https"

    def items(self):
        return Position.objects.filter(enabled_flag=True, archive_flag=False, company_name_ref__enabled_flag=True)

    def lastmod(self, obj):
        return obj.pub_date


class CategorySitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return Category.objects.filter(position__isnull=False, position__enabled_flag=True,
                                       position__archive_flag=False).distinct()


class KeywordSitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Keyword.objects.filter(position__isnull=False, position__enabled_flag=True,
                                      position__archive_flag=False).distinct()


class StaticViewSitemap(Sitemap):
    priority = 1
    changefreq = 'hourly'
    protocol = "https"

    def items(self):
        return ['mycatalog:index', 'mycatalog:companies']

    def location(self, item):
        return reverse(item)
