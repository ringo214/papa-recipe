from django.shortcuts import render
from .models import Recipe

def recipe_list(request):
    # ① 画面から送られてきた検索・絞り込みの条件を受け取る
    query = request.GET.get('q')
    tool_query = request.GET.get('tool')
    poster_query = request.GET.get('poster')
    recipes = Recipe.objects.all().order_by('-created_at')
    if query:
        recipes = recipes.filter(title__icontains=query)
    if tool_query:
        recipes = recipes.filter(tool=tool_query)
    if poster_query:
        recipes = recipes.filter(poster=poster_query)
    tools = Recipe.objects.values_list('tool', flat=True).distinct()
    posters = Recipe.objects.values_list('poster', flat=True).distinct()
    context = {'recipes': recipes, 'tools': tools, 'posters': posters}
    return render(request, 'recipes/recipe_list.html', context)