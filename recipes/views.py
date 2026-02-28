from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, CookLog
from .forms import CookLogForm

def recipe_list(request):
    # ① 画面から送られてきた条件を受け取る
    query = request.GET.get('q')
    tool_query = request.GET.get('tool')
    poster_query = request.GET.get('poster')
    category_query = request.GET.get('category')
    difficulty_query = request.GET.get('difficulty')

    # ② ベースのレシピ一覧
    recipes = Recipe.objects.all().order_by('-created_at')

    # ③ フィルターの重ねがけ！
    if query:
        recipes = recipes.filter(title__icontains=query)
    if tool_query:
        recipes = recipes.filter(tool=tool_query)
    if poster_query:
        recipes = recipes.filter(poster=poster_query)
    if category_query:
        recipes = recipes.filter(category=category_query)
    if difficulty_query:
        recipes = recipes.filter(difficulty=difficulty_query)

    # ④ プルダウンの選択肢を用意する
    tools = Recipe.objects.values_list('tool', flat=True).distinct()
    posters = Recipe.objects.values_list('poster', flat=True).distinct()
    
    # 🌟 新規：models.pyで設定した「★☆☆☆☆（...）」の選択肢をそのまま持ってくる！
    category_choices = Recipe.CATEGORY_CHOICES
    difficulty_choices = Recipe.DIFFICULTY_CHOICES

    context = {
        'recipes': recipes,
        'tools': tools,
        'posters': posters,
        'category_choices': category_choices,
        'difficulty_choices': difficulty_choices,
    }
    return render(request, 'recipes/recipe_list.html', context)

# --- 一番上の import 部分をこのように書き換えます ---
from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, CookLog
from .forms import CookLogForm

# --- (既存の recipe_list のコードはそのまま残しておいてください！) ---


# --- 以下を一番下に追加！(レシピ詳細＆写真アップロードの脳みそ) ---
def recipe_detail(request, pk):
    # ① どのレシピを開いたか特定する
    recipe = get_object_or_404(Recipe, pk=pk)
    
    # ② お父様が「記録する！」ボタンを押した時（POST送信された時）
    if request.method == 'POST':
        # 文字(POST)と写真ファイル(FILES)を両方受け取る！
        form = CookLogForm(request.POST, request.FILES)
        if form.is_valid():
            cook_log = form.save(commit=False) # まだ保存待て！
            cook_log.recipe = recipe           # 「このレシピの記録だよ」と紐付け！
            cook_log.save()                    # ここで本当に保存！
            return redirect('recipe_detail', pk=recipe.pk) # 保存したら同じ画面をリロード
    else:
        # 普通に画面を開いた時は、空っぽの入力枠を用意する
        form = CookLogForm()

    # ③ 過去にパパが作った記録一覧（新しい順に並べる）
    cook_logs = recipe.cook_logs.all().order_by('-created_at')

    context = {
        'recipe': recipe,
        'form': form,
        'cook_logs': cook_logs,
    }
    return render(request, 'recipes/recipe_detail.html', context)

# --- 一番下に追加！(買い物リスト作成の脳みそ) ---
def shopping_list(request):
    # ① 画面から「チェックされたレシピのID」を全部受け取る！
    recipe_ids = request.GET.getlist('recipe_ids')
    
    # ② 受け取ったIDに一致するレシピをデータベースから引っ張ってくる！
    selected_recipes = Recipe.objects.filter(id__in=recipe_ids)
    
    context = {
        'selected_recipes': selected_recipes,
    }
    return render(request, 'recipes/shopping_list.html', context)