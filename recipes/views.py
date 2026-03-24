from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, CookLog
from .forms import CookLogForm
from .models import Recipe, CookLog, Comment
# ↓ CommentForm を追加
from .forms import CookLogForm, CommentForm
# 一番上の import に RecipeForm を追加！
from .forms import CookLogForm, CommentForm, RecipeForm

def recipe_list(request):
    # ① 画面から送られてきた条件を受け取る
    query = request.GET.get('q')
    tool_query = request.GET.get('tool')
    author_query = request.GET.get('author')
    category_query = request.GET.get('category')
    difficulty_query = request.GET.get('difficulty')

    # ② ベースのレシピ一覧
    recipes = Recipe.objects.all().order_by('-created_at')

    # ③ フィルターの重ねがけ！
    if query:
        recipes = recipes.filter(title__icontains=query)
    if tool_query:
        recipes = recipes.filter(tool=tool_query)
    if author_query:
        recipes = recipes.filter(auther=author_query)
    if category_query:
        recipes = recipes.filter(category=category_query)
    if difficulty_query:
        recipes = recipes.filter(difficulty=difficulty_query)

    # ④ プルダウンの選択肢を用意する
    tools = Recipe.objects.values_list('tool', flat=True).distinct()
    authors = Recipe.objects.values_list('author', flat=True).distinct()

    # 🌟 新規：models.pyで設定した「★☆☆☆☆（...）」の選択肢をそのまま持ってくる！
    category_choices = Recipe.CATEGORY_CHOICES
    difficulty_choices = Recipe.DIFFICULTY_CHOICES

    context = {
        'recipes': recipes,
        'tools': tools,
        'authors': authors,
        'category_choices': category_choices,
        'difficulty_choices': difficulty_choices,
    }
    return render(request, 'recipes/recipe_list.html', context)



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

    comment_form = CommentForm()

    context = {
        'recipe': recipe,
        'form': form,
        'cook_logs': cook_logs,
        'comment_form': comment_form,
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

def add_comment(request, pk):
    # どのパパの料理記録（CookLog）に対するコメントかを探す！
    cook_log = get_object_or_404(CookLog, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.cook_log = cook_log # 「この写真へのコメントだよ」と紐付け！
            comment.save()              # データベースに保存！

    # 保存が終わったら、元のレシピ詳細画面に自動で戻る！
    return redirect('recipe_detail', pk=cook_log.recipe.pk)

def recipe_new(request):
    if request.method == "POST":
        # ⚠️画像のアップロードがある場合、「request.FILES」が絶対に必要です！（超重要トラップ）
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save()
            # 保存できたら、新しく作ったレシピの詳細画面へワープ！
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        # 最初の画面表示の時は空っぽのフォームを渡す
        form = RecipeForm()

    return render(request, 'recipes/recipe_form.html', {'form': form})

def recipe_edit(request, pk):
    # 編集したいレシピを探してくる
    recipe = get_object_or_404(Recipe, pk=pk)

    if request.method == "POST":
        # ⚠️ instance=recipe を入れることで「上書き保存」になります！
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            recipe = form.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        # 最初からレシピのデータが入った状態のフォームを渡す
        form = RecipeForm(instance=recipe)

    # 画面は新規作成と同じ「recipe_form.html」を使い回せます！エコ！
    return render(request, 'recipes/recipe_form.html', {'form': form})