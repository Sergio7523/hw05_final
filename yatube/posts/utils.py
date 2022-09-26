from django.core.paginator import Paginator
from .constants import POSTS_AMOUNT


def get_page_context(queryset, request):
    paginator = Paginator(queryset, POSTS_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
