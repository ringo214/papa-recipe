from django.shortcuts import render
from .models import Recipe

def recipe_list(request):
    # ① 画面から送られてきた検索・絞り込みの条件を受け取る
    query = request.GET.get('q')
    tool_query = request.GET.get('tool')
    poster_query = request.GET.get('poster')