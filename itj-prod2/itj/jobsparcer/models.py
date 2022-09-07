from ckeditor.fields import RichTextField
from django.db import models

from django.core.files import File
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

import urllib.request

from django.utils.safestring import mark_safe
from django.contrib.staticfiles.storage import staticfiles_storage


class ParcedCompany(models.Model):
    class Meta:
        verbose_name = 'Parced Company'
        verbose_name_plural = 'Parced Companies'

    company_name = models.CharField(max_length=500, unique=True)
    company_logo_url = models.URLField(blank=True)
    edited_date = models.DateTimeField(verbose_name='Date edited', auto_now=True)
    created_date = models.DateTimeField(verbose_name='Date created', auto_now_add=True)
    moved_to_catalog = models.BooleanField(default=False)
    company_logo = models.ImageField(max_length=2000, null=True, blank=True, upload_to='logos')
    catalog_id = models.CharField(max_length=100, blank=True, null=True)
    company_pitch = RichTextField(blank=True)
    description = RichTextField(blank=True)
    offices_locations = models.CharField(max_length=250, null=True, blank=True)
    website = models.CharField(max_length=250, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    cb_name = models.CharField(max_length=500, null=True, blank=True)
    cb_web_path = models.CharField(max_length=500, null=True, blank=True)
    cb_short_description = RichTextField(blank=True)
    cb_profile_image_url = models.URLField(blank=True)
    cb_logo = models.ImageField(max_length=2000, null=True, blank=True, upload_to='logos')
    cb_facebook_url = models.URLField(blank=True)
    cb_twitter_url = models.URLField(blank=True)
    cb_linkedin_url = models.URLField(blank=True)
    cb_location = models.CharField(max_length=500, null=True, blank=True)
    cb_other = RichTextField(blank=True)
    cb_long_description = RichTextField(blank=True)
    cb_check = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(ParcedCompany, self).save(*args, **kwargs)
        if self.company_logo_url and not self.company_logo:
            req = urllib.request.Request(self.company_logo_url, headers={
                'User-Agent': 'Mozilla/5.0'})

            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(req).read())
            img_temp.flush()
            self.company_logo.save(f"image_{self.pk}.png", File(img_temp))

        if self.cb_profile_image_url and not self.cb_logo:
            req = urllib.request.Request(self.cb_profile_image_url, headers={
                'User-Agent': 'Mozilla/5.0'})

            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(req).read())
            img_temp.flush()
            self.cb_logo.save(f"image_c_{self.pk}.png", File(img_temp))

    def __str__(self):
        return self.company_name

    def company_logo_tag(self):
        if self.company_logo:
            logo = mark_safe('<img src="%s" width="40" />' % self.company_logo.url)
        else:
            logo = mark_safe('<img src="' + staticfiles_storage.url('mycatalog/nologo.png') + '" width="40" />')
        return logo

    def cb_logo_tag(self):
        if self.cb_logo:
            logo = mark_safe('<img src="%s" width="40" />' % self.cb_logo.url)
        else:
            logo = mark_safe('<img src="' + staticfiles_storage.url('mycatalog/nologo.png') + '" width="40" />')
        return logo

class ParcedTag(models.Model):
    class Meta:
        verbose_name = 'Parced Tag'
        verbose_name_plural = 'Parced Tags'

    tag = models.CharField(max_length=200, unique=True)
    moved_to_catalog = models.BooleanField(default=False)
    catalog_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.tag


class ParcedPosition(models.Model):
    class Meta:
        verbose_name = 'Parced Position'
        verbose_name_plural = 'Parced Positions'

    position_name = models.CharField(max_length=500)
    position_slug = models.CharField(max_length=500, blank=True)
    position_parced_id = models.CharField(max_length=100, unique=True)
    epoch = models.CharField(max_length=100, blank=True)
    position_datetime = models.DateTimeField()
    company_name_ref = models.ForeignKey(ParcedCompany, null=False, on_delete=models.CASCADE, blank=False,
                                         verbose_name='Company')
    job_description = RichTextField(verbose_name='Job Description')
    job_url = models.URLField(blank=True)
    edited_date = models.DateTimeField(verbose_name='Date edited', auto_now=True)
    created_date = models.DateTimeField(verbose_name='Date created', auto_now_add=True)
    keyword_ref = models.ManyToManyField(ParcedTag, verbose_name='Tags')
    verified = models.BooleanField(default=False)
    original = models.BooleanField(default=False)
    moved_to_catalog = models.BooleanField(default=False)
    catalog_id = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.position_name


class ParcingParam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=100, blank=True)
