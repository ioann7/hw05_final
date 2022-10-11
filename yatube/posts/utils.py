from django.core.paginator import Paginator, Page
from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings
from django.db.models.query import QuerySet


def get_posts_page_obj(request: WSGIRequest,
                       posts: QuerySet) -> Page:
    """Return posts page object."""
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
