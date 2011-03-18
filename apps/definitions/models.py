from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import BaseModel

pypi_url_help_text = settings.PACKAGINATOR_HELP_TEXT['PYPI_URL']

    
class PythonPackage(models.Model):
    
    pypi_url        = models.URLField(_("PyPI slug"), help_text=pypi_url_help_text, blank=True, default='')
    pypi_downloads  = models.IntegerField(_("Pypi downloads"), default=0)
    pypi_home_page  = models.URLField(_("homepage on PyPI for a project"), blank=True, null=True)
    
    class Meta:
        abstract = True    
    
    
class VersionManager(models.Manager):
    def by_version(self, *args, **kwargs):
        qs = self.get_query_set().filter(*args, **kwargs)
        return sorted(qs,key=lambda v: versioner(v.number))

class Version(BaseModel):

    package = models.ForeignKey(Package, blank=True, null=True)
    number = models.CharField(_("Version"), max_length="100", default="", blank="")
    downloads = models.IntegerField(_("downloads"), default=0)
    license = models.CharField(_("license"), max_length="100")
    hidden = models.BooleanField(_("hidden"), default=False)    

    objects = VersionManager()

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']

    def __unicode__(self):
        return "%s: %s" % (self.package.title, self.number)
        
    @property
    def pypi_version(self):
        string_ver_list = self.version_set.values_list('number', flat=True)
        if string_ver_list:
            vers_list = [versioner(v) for v in string_ver_list]
            latest = sorted(vers_list)[-1]
            return str(latest)
        return ''

    @property     
    def pypi_name(self):
        """ return the pypi name of a package"""

        if not self.pypi_url.strip():
            return ""

        name = self.pypi_url.replace("http://pypi.python.org/pypi/","")
        if "/" in name:
            return name[:name.index("/")]
        return name        

    
repo_url_help_text = settings.PACKAGINATOR_HELP_TEXT['REPO_URL']
class RepoPackage(models.Model):
    repo_description= models.TextField(_("Repo Description"), blank=True)
    repo_url        = models.URLField(_("repo URL"), help_text=repo_url_help_text, blank=True,unique=True)
    repo_watchers   = models.IntegerField(_("repo watchers"), default=0)
    repo_forks      = models.IntegerField(_("repo forks"), default=0)
    repo_commits    = models.IntegerField(_("repo commits"), default=0)
    participants    = models.TextField(_("Participants"),
                        help_text="List of collaborats/participants on the project", blank=True)
                        
    class Meta:
        abstract = True                        
                        
    def commits_over_52(self):
        from package.templatetags.package_tags import commits_over_52
        return commits_over_52(self)
        
    def repo_name(self):
        return self.repo_url.replace(self.repo.url + '/','')

    def participant_list(self):

        return self.participants.split(',')

    @property
    def last_updated(self):
        last_commit = self.commit_set.latest('commit_date')
        if last_commit: 
            return last_commit.commit_date
        return None

    @property
    def repo(self):
        handler = get_repo_for_repo_url(self.repo_url)
        return handler                