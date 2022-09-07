from django.contrib.postgres.search import SearchVector
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import generic

from mycatalog.models import Position, Company, Category, Keyword

from el_pagination.views import AjaxListView


def error_404_view(request, exception):
    return render(request, 'mycatalog/404.html')


categories_list = Category.objects.filter(position__isnull=False, position__enabled_flag=True,
                                          position__archive_flag=False).distinct().order_by('-category_name')


class ExternalCounterURLRedirectView(generic.DetailView):
    model = Position

    def get(self, request, *args, **kwargs):
        position = self.get_object()
        position.increment_apply_counter()
        if position.apply_url:
            return HttpResponseRedirect(position.apply_url)
        elif position.apply_email:
            return HttpResponse('<meta http-equiv="refresh" content="0;url=mailto:%s" />' % position.apply_email)
        elif position.company_name_ref.positions_url:
            return HttpResponseRedirect(position.company_name_ref.positions_url)
        else:
            raise Http404


class IndexView(AjaxListView):
    template_name = 'mycatalog/index.html'
    context_object_name = 'latest_positions_list'
    page_template = 'mycatalog/index_page.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context.update({
            'categories_list': categories_list,
            'page_title': 'Remote jobs: development, testing, design and more | IT Careers',
            'meta_descr': 'IT Careers helps you to find remote IT jobs worldwide. Software development, testing, design, management, marketing and many other different jobs available to you at one click.',
            'page_h1': 'IT CAREERS - REMOTE WORK',
        })
        return context

    def get_queryset(self):
        return Position.objects.filter(enabled_flag=True, company_name_ref__enabled_flag=True,
                                       archive_flag=False).order_by('-pub_date', 'category_name_ref')


class IndexViewKeywordsFiltered(AjaxListView):
    template_name = 'mycatalog/index.html'
    context_object_name = 'latest_positions_list'
    page_template = 'mycatalog/index_page.html'

    def get_context_data(self, **kwargs):
        kwd = Keyword.objects.get(slug=self.kwargs['slug']).keyword
        context = super(IndexViewKeywordsFiltered, self).get_context_data(**kwargs)
        context.update({
            'categories_list': categories_list,
            'search_string': kwd,
            'page_title': "Remote %s Jobs | IT Careers" % kwd.upper(),
            'meta_descr': "Are you a professional in %s? You could find remote job using your skills in this area. Just apply for a job you like on IT Careers" % kwd.upper(),
            'page_h1': "Remote %s Jobs" % kwd.upper(),
        })
        return context

    def get_queryset(self):
        return Position.objects.filter(enabled_flag=True, company_name_ref__enabled_flag=True,
                                       keyword_ref=Keyword.objects.get(slug=self.kwargs['slug']),
                                       archive_flag=False).order_by('-pub_date', 'category_name_ref')

    def dispatch(self, request, *args, **kwargs):
        try:
            Keyword.objects.get(slug=self.kwargs['slug'])
            return super(IndexViewKeywordsFiltered, self).get(request, *args, **kwargs)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise Http404


class IndexViewCategoryFiltered(AjaxListView):
    template_name = 'mycatalog/index.html'
    context_object_name = 'latest_positions_list'
    page_template = 'mycatalog/index_page.html'

    def get_context_data(self, **kwargs):
        category_name = Category.objects.get(slug=self.kwargs['slug']).category_name
        context = super(IndexViewCategoryFiltered, self).get_context_data(**kwargs)
        context.update({
            'categories_list': categories_list,
            'search_string': category_name,
            'page_title': "Remote %s Jobs | IT Careers" % category_name,
            'meta_descr': "You could find remote %s jobs here. Just apply for an opportunity you like on IT Careers" % category_name,
            'page_h1': 'Remote %s Jobs' % category_name,
        })
        return context

    def get_queryset(self):
        return Position.objects.filter(enabled_flag=True, company_name_ref__enabled_flag=True,
                                       category_name_ref=Category.objects.get(slug=self.kwargs['slug']),
                                       archive_flag=False).order_by('-pub_date', 'category_name_ref')

    def dispatch(self, request, *args, **kwargs):
        try:
            Category.objects.get(slug=self.kwargs['slug'])
            return super(IndexViewCategoryFiltered, self).get(request, *args, **kwargs)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise Http404


class IndexViewSearchFiltered(AjaxListView):
    template_name = 'mycatalog/index.html'
    context_object_name = 'latest_positions_list'
    page_template = 'mycatalog/index_page.html'

    def get_context_data(self, **kwargs):
        context = super(IndexViewSearchFiltered, self).get_context_data(**kwargs)
        context.update({
            'categories_list': categories_list,
            'search_string': self.request.GET.get('search_string'),
            'page_title': "Remote Jobs Search Result | IT Careers",
            'meta_descr': "Search for remote job you dream about. Just apply for the job on IT Careers",
            'meta_noindex': '1',
            'page_h1': 'Remote Jobs Search Result',
        })
        return context

    def get_queryset(self):
        search_string = self.request.GET.get('search_string')
        return Position.objects.annotate(
            search=SearchVector('position_name', 'company_name_ref__company_name', 'keyword_ref__keyword'), ).filter(
            enabled_flag=True, company_name_ref__enabled_flag=True, archive_flag=False).filter(
            Q(search__icontains=search_string) | Q(search=search_string)
        ).order_by('-pub_date', 'category_name_ref').distinct('pub_date', 'category_name_ref')

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get('search_string'):
            return super(IndexViewSearchFiltered, self).get(request, *args, **kwargs)
        else:
            raise Http404


class PositionDetailView(generic.DetailView):
    model = Position
    template_name = 'mycatalog/position_detail.html'

    def dispatch(self, request, *args, **kwargs):
        position = self.get_object()
        position.increment_view_counter()
        if position.position_id_redirect_to:
            try:
                redirect_id = self.get_object().position_id_redirect_to
                redirect_slug = Position.objects.get(pk=redirect_id).slug
                return redirect(reverse('mycatalog:position_detail', args=(redirect_id, redirect_slug)), permanent=True)
            except:
                return super(PositionDetailView, self).get(request, *args, **kwargs)
        return super(PositionDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PositionDetailView, self).get_context_data(**kwargs)
        keywords = Keyword.objects.filter(position__id=self.kwargs['pk'])
        context.update({
            'categories_list': categories_list,
            'related_jobs_list': Position.objects.filter(enabled_flag=True, company_name_ref__enabled_flag=True,
                                                         archive_flag=False,
                                                         category_name_ref=self.get_object().category_name_ref,
                                                         keyword_ref__in=keywords).exclude(
                id=self.kwargs['pk']).distinct().order_by('-pub_date')[:10]
        })
        return context

    def get_queryset(self):
        """
        Excludes any positions that aren't published yet.
        """
        return Position.objects.filter(enabled_flag=True, company_name_ref__enabled_flag=True)


class CompanyDetailView(generic.DetailView):
    model = Company
    template_name = 'mycatalog/company_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CompanyDetailView, self).get_context_data(**kwargs)
        context.update({
            'categories_list': categories_list,
        })
        return context

    def get_queryset(self):
        """
        Excludes any companies that aren't published yet.
        """
        return Company.objects.filter(enabled_flag=True)


class CompanyListView(generic.ListView):
    template_name = 'mycatalog/company_list.html'
    context_object_name = 'companies_list'

    def get_context_data(self, **kwargs):
        context = super(CompanyListView, self).get_context_data(**kwargs)
        context.update({
            'categories_list': categories_list,
        })
        return context

    def get_queryset(self):
        """
        Excludes any companies that aren't published yet.
        """
        return Company.objects.filter(enabled_flag=True).order_by('company_name')
