from django.core.paginator import Paginator


def get_page_paginator(post_list, request, num_art):
    paginator = Paginator(post_list, num_art)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
