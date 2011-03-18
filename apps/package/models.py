# TODO - cleanup regex to do proper string subs

import logging
import os
import re
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from distutils.version import LooseVersion as versioner
from github2.client import Github

from core.models import BaseModel
from package.repos import github
from package.pypi import fetch_releases
from package.repos import get_repo_for_repo_url

# replace with smart import
from definitions.models import *

category_help_text = settings.PACKAGINATOR_HELP_TEXT['CATEGORY']

class NoPyPiVersionFound(Exception):
    pass


class Category(BaseModel):
    
    title = models.CharField(_("Title"), max_length="50")
    slug  = models.SlugField(_("slug"))
    description = models.TextField(_("description"), blank=True)
    title_plural = models.CharField(_("Title Plural"), max_length="50", blank=True) 
    show_pypi = models.BooleanField(_("Show pypi stats & version"), default=True)
    
    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Categories'
    
    def __unicode__(self):
        return self.title
        
class Package(BaseModel):
    
    title           = models.CharField(_("Title"), max_length="100")
    slug            = models.SlugField(_("Slug"), help_text="Slugs will be lowercased", unique=True)
    category        = models.ForeignKey(Category, verbose_name="Installation", help_text=category_help_text)
    related_packages    = models.ManyToManyField("self", blank=True)
    usage           = models.ManyToManyField(User, blank=True)
    created_by = models.ForeignKey(User, blank=True, null=True, related_name="creator")    
    last_modified_by = models.ForeignKey(User, blank=True, null=True, related_name="modifier")

    def active_examples(self):
        return self.packageexample_set.filter(active=True)
    
    def grids(self):
        
        return (x.grid for x in self.gridpackage_set.all())
    
    
    def fetch_metadata(self, *args, **kwargs):
        """ currently does both repo and pypi stuff """
        
        
        # Get the downloads from pypi
        if self.pypi_url.strip() and self.pypi_url != "http://pypi.python.org/pypi/":
            
            total_downloads = 0
            
            for release in fetch_releases(self.pypi_name):
            
                version, created = Version.objects.get_or_create(
                    package = self,
                    number = release.version
                )

                # add to total downloads
                total_downloads += release.downloads

                # add to versions
                version.downloads = release.downloads
                version.license = release.license
                version.hidden = release._pypi_hidden                
                version.save()
            
            self.pypi_downloads = total_downloads
        
        self.repo.fetch_metadata(self)
        self.save()

    def fetch_commits(self):
        self.repo.fetch_commits(self)

    class Meta:
        ordering = ['title']
    
    def __unicode__(self):
        
        return self.title
        
    @models.permalink
    def get_absolute_url(self):
        return ("package", [self.slug])
        

class PackageExample(BaseModel):
    
    package = models.ForeignKey(Package)
    title = models.CharField(_("Title"), max_length="100")
    url = models.URLField(_("URL"))
    active = models.BooleanField(_("Active"), default=True, help_text="Moderators have to approve links before they are provided")
    
    class Meta:
        ordering = ['title']
    
    def __unicode__(self):
        return self.title