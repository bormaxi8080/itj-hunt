from django.urls import path

from . import views

app_name = 'mycatalog'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('companies', views.CompanyListView.as_view(), name='companies'),
    path('keyword/<slug:slug>', views.IndexViewKeywordsFiltered.as_view(), name='index_keyword_filtered'),
    path('category/<slug:slug>', views.IndexViewCategoryFiltered.as_view(), name='index_category_filtered'),
    path('search', views.IndexViewSearchFiltered.as_view(), name='index_search_filtered'),
    path('remote-job/<int:pk>-<slug:slug>', views.PositionDetailView.as_view(), name='position_detail'),
    path('company/<slug:slug>', views.CompanyDetailView.as_view(), name='company_detail'),
    path('apply/<int:pk>', views.ExternalCounterURLRedirectView.as_view(), name='position-counter-redirect'),
]