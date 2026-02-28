from django.shortcuts import render
from .models import Recipe

def recipe_list(request):
    # ① 検索バーに入力された文字（q）を受け取る
    query = request.GET.get('q')

    # ② もし検索キーワードがあったら…
    if query:
        # タイトルにキーワードが含まれるレシピだけを探す！
        recipes = Recipe.objects.filter(title__icontains=query).order_by('-created_at')
    # ③ キーワードがなかったら（最初の画面）…
    else:
        # 今まで通り全部のレシピを新しい順に出す！
        recipes = Recipe.objects.all().order_by('-created_at')

    # 結果をHTMLに渡す
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})