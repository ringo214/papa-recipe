from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Recipe, CookLog, Comment, Budget, Inventory, CategoryBudget
from .forms import CookLogForm, CommentForm, RecipeForm, BudgetForm, CategoryBudgetForm, InventoryForm
import json
from google import genai
from google.genai import types
from django.contrib import messages  # 👈 追加
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Sum # 👈 合計を出すための魔法
from django.utils import timezone
import datetime
from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin  # 👈 これが足りてへんかった！
import os
from dotenv import load_dotenv

# ==========================================
# 1. Gemini AI の設定 (2026年最新Client方式)
# ==========================================

# .envファイルを読み込む
load_dotenv()
# APIキーを環境変数から取得
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))



# ==========================================
# 2. レシピ関連の機能
# ==========================================

@login_required
def recipe_list(request):
    query = request.GET.get('q')
    tool_query = request.GET.get('tool')
    author_query = request.GET.get('author')
    category_query = request.GET.get('category')
    difficulty_query = request.GET.get('difficulty')

    recipes = Recipe.objects.all().order_by('-created_at')

    # 🌟 冷蔵庫にある食材をリストで取得
    fridge_items = Inventory.objects.filter(user=request.user).values_list('name', flat=True)

    if query: recipes = recipes.filter(title__icontains=query)
    if tool_query: recipes = recipes.filter(tool=tool_query)
    if author_query: recipes = recipes.filter(author=author_query)
    if category_query: recipes = recipes.filter(category=category_query)
    if difficulty_query: recipes = recipes.filter(difficulty=difficulty_query)

    tools = Recipe.objects.values_list('tool', flat=True).distinct()
    authors = Recipe.objects.values_list('author', flat=True).distinct()
    category_choices = Recipe.CATEGORY_CHOICES
    difficulty_choices = Recipe.DIFFICULTY_CHOICES

    # 🌟 === ここから下の部分を書き換える === 🌟

    context = {
        'recipes': recipes,
        'tools': tools,
        'authors': authors,
        'category_choices': category_choices,
        'difficulty_choices': difficulty_choices,
        'fridge_items': fridge_items,
    }

    # 📚 AI謹製・めんどくさがり用「最強の表記ゆれ辞書」
    SYNONYMS = {
        # --- お肉系 ---
        '豚肉': ['豚肉', '豚バラ', '豚こま', '豚ロース', '豚', 'ぶた'],
        '牛肉': ['牛肉', '牛バラ', '牛こま', '牛', 'ぎゅう'],
        '鶏肉': ['鶏肉', '鳥肉', '鶏もも', '鶏むね', 'チキン', 'とり'],
        'ひき肉': ['ひき肉', '挽き肉', 'ミンチ', '合挽き'],
        # --- 卵・乳製品・大豆 ---
        'たまご': ['卵', 'たまご', '玉子', 'タマゴ'],
        '卵': ['卵', 'たまご', '玉子', 'タマゴ'], # どっちで登録されてもいいように！
        '牛乳': ['牛乳', 'ミルク'],
        '豆腐': ['豆腐', 'とうふ', 'トウフ', '木綿豆腐', '絹ごし豆腐'],
        '納豆': ['納豆', 'なっとう', 'ナットウ'],
        # --- 野菜系 ---
        '玉ねぎ': ['玉ねぎ', 'タマネギ', 'たまねぎ', '玉葱'],
        'ネギ': ['ネギ', 'ねぎ', '長ネギ', '白ネギ', '青ネギ', '万能ねぎ'],
        'キャベツ': ['キャベツ', 'きゃべつ'],
        'じゃがいも': ['じゃがいも', 'ジャガイモ', 'ポテト', '馬鈴薯'],
        'にんじん': ['にんじん', 'ニンジン', '人参'],
        'にんにく': ['にんにく', 'ニンニク', '大蒜', 'ガーリック'],
        'しょうが': ['しょうが', 'ショウガ', '生姜'],
        '大根': ['大根', 'だいこん', 'ダイコン'],
        'トマト': ['トマト', 'とまと', 'ミニトマト'],
        'きのこ': ['きのこ', 'キノコ', 'しめじ', 'えのき', 'エリンギ', 'しいたけ'],
        # --- 調味料 ---
        '醤油': ['醤油', 'しょうゆ', 'ショウユ'],
        '塩': ['塩', 'しお', 'ソルト'],
        '砂糖': ['砂糖', 'さとう', 'シュガー'],
    }

    # 🌟 各レシピに「作れるかどうか」のフラグを立てる
    for recipe in recipes:
        match_count = 0
        for item in fridge_items:
            # 冷蔵庫の食材名が辞書にあればそのリストを、なければ元の名前だけを使う
            search_terms = SYNONYMS.get(item, [item])
            
            # 辞書の中身を1つずつ、レシピの材料（ingredients）に含まれているかチェック！
            for term in search_terms:
                if recipe.ingredients and term in recipe.ingredients:
                    match_count += 1
                    break  # 1つでもヒットしたら、重複カウントを防ぐために次の食材へ
        
        # 🌟 「2つ以上」一致したらバッジを出すようにしておく！
        recipe.can_make = match_count >= 2

    return render(request, 'recipes/recipe_list.html', context)

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = CookLogForm(request.POST, request.FILES)
        if form.is_valid():
            cook_log = form.save(commit=False)
            cook_log.recipe = recipe
            cook_log.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = CookLogForm()
    
    cook_logs = recipe.cook_logs.all().order_by('-created_at')
    comment_form = CommentForm()
    context = {'recipe': recipe, 'form': form, 'cook_logs': cook_logs, 'comment_form': comment_form}
    return render(request, 'recipes/recipe_detail.html', context)

def shopping_list(request):
    recipe_ids = request.GET.getlist('recipe_ids')
    selected_recipes = Recipe.objects.filter(id__in=recipe_ids)
    return render(request, 'recipes/shopping_list.html', {'selected_recipes': selected_recipes})

def add_comment(request, pk):
    cook_log = get_object_or_404(CookLog, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.cook_log = cook_log
            comment.save()
    return redirect('recipe_detail', pk=cook_log.recipe.pk)

@login_required # 👈 ログイン必須にする
def recipe_new(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            # 🌟 ここが魔法のコード！ログイン中の「自分」を追加者にセット
            recipe.author_user = request.user 
            recipe.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, 'recipes/recipe_form.html', {'form': form})

def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            recipe = form.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'recipes/recipe_form.html', {'form': form})

# ==========================================
# 3. 家計簿・AIスキャン機能 (大改造版)
# ==========================================
@login_required
def budget_list(request):
    # --- 日付計算ロジック（そのまま保持） ---
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    this_month_date = datetime.date(year, month, 1)
    prev_month_date = this_month_date - datetime.timedelta(days=1)
    next_month_date = (this_month_date + datetime.timedelta(days=32)).replace(day=1)

    # --- 保存処理（手動入力もここで受ける） ---
    if request.method == 'POST':
        date = request.POST.get('date')
        item_name = request.POST.get('item_name')
        amount = request.POST.get('amount')
        category = request.POST.get('category')

        # 重複チェックロジック（これもRieさんのこだわり）
        duplicate = Budget.objects.filter(user=request.user, date=date, amount=amount).first()
        if duplicate:
            messages.warning(request, f"それ、もう登録済みちゃう？（{duplicate.item_name}）")
        else:
            Budget.objects.create(user=request.user, date=date, item_name=item_name, amount=amount, category=category)
            messages.success(request, "家計簿に登録したで！💰")
        return redirect('budget_list')

    # --- 表示データ計算 ---
    budgets = Budget.objects.filter(user=request.user, date__year=year, date__month=month).order_by('-date')
    actual_data = budgets.order_by().values('category').annotate(total=Sum('amount'))
    actual_dict = {item['category']: item['total'] for item in actual_data}
    category_budgets = CategoryBudget.objects.filter(user=request.user)
    
    category_status = []
    for cb in category_budgets:
        spent = actual_dict.get(cb.category, 0) or 0
        percent = (spent / cb.amount * 100) if cb.amount > 0 else 0
        category_status.append({
            'display_name': cb.get_category_display(),
            'budget': cb.amount, 'spent': spent,
            'remaining': float(cb.amount - spent),
            'percent': min(float(percent), 100.0),
            'is_over': spent > cb.amount
        })

    # 📊 グラフ用のJSON変換（ここでfloatにするのがQA的正解）
    category_map = dict(Budget.CATEGORY_CHOICES)
    labels = [category_map.get(item['category'], item['category']) for item in actual_data]
    graph_data = [float(item['total'] or 0) for item in actual_data]

    context = {
        'budgets': budgets,
        'category_status': category_status,
        'labels': json.dumps(labels),
        'data': json.dumps(graph_data),
        'current_month_display': f"{year}年{month}月",
        'prev_year': prev_month_date.year, 'prev_month': prev_month_date.month,
        'next_year': next_month_date.year, 'next_month': next_month_date.month,
        'category_choices': Budget.CATEGORY_CHOICES, # フォーム用
    }
    return render(request, 'recipes/budget_list.html', context)

# --- A. 新規作成用のViewを追加 ---
@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, "家計簿に手動で追加したで！💰")
            return redirect('budget_list')
    else:
        form = BudgetForm()
    
    return render(request, 'recipes/budget_form.html', {
        'form': form,
        'title': "家計簿の手動入力"
    })

# 🌟 削除機能
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    budget.delete()
    messages.info(request, "データを削除したで。")
    return redirect('budget_list')

# 🌟 編集機能（既存のデータを読み込んで確認画面に飛ばすイメージ）
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        budget.date = request.POST.get('date')
        budget.item_name = request.POST.get('item_name')
        budget.amount = request.POST.get('amount')
        budget.category = request.POST.get('category')
        budget.save()
        messages.success(request, "修正完了や！")
        return redirect('budget_list')
    
    return render(request, 'recipes/receipt_confirm.html', {
        'data': budget, 
        'category_choices': Budget.CATEGORY_CHOICES,
        'is_edit': True # 編集モード判定用
    })

@login_required
def receipt_scan(request):
    if request.method == 'POST' and request.FILES.get('receipt_image'):
        try:
            img_file = request.FILES['receipt_image']
            img_data = img_file.read()

            # 🌟 指示（プロンプト）：JSONで返せ！と強く念押し
            prompt = """
            レシート画像を解析し、以下のJSON形式で1つだけ返してください。
            Markdownの枠（```json）などは含めず、純粋なJSONテキストのみ出力してください。

            {
                "date": "YYYY-MM-DD",
                "item_name": "店舗名",
                "amount": 0,
                "category": "food",
                "item_list_raw": ["たまご", "牛乳", "豚肉"]
            }
            """

            # 🌟 修正：リストで確認できた「models/gemini-2.5-flash」をフルネームで指定！
            response = client.models.generate_content(
                model='models/gemini-2.5-flash', 
                contents=[
                    prompt,
                    types.Part.from_bytes(data=img_data, mime_type=img_file.content_type)
                ]
            )

            # 🌟 AIの回答テキストをJSONデータに変換
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            scan_data = json.loads(res_text)

            # カテゴリの選択肢（food, daily...）を準備
            category_choices = Budget.CATEGORY_CHOICES

            # 🌟 HTML（receipt_confirm.html）にデータを送る！
            return render(request, 'recipes/receipt_confirm.html', {
                'scan_data': scan_data, # 👈 変数名を scan_data にしてHTMLと合わせる
                'category_choices': category_choices,
            })

        except Exception as e:
            # 何かあったらエラーメッセージを表示（QA的デバッグ）
            messages.error(request, f"AIスキャン失敗：{e}")
            return redirect('budget_list')

    return redirect('budget_list')

class SignUpView(SuccessMessageMixin, generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login') # 登録成功したらログイン画面へ
    template_name = 'recipes/signup.html'
    success_message = "ユーザー登録が完了したで！さっそくログインしてみてな。"

# recipes/views.py
@login_required
def budget_config(request):
    # カテゴリの選択肢を取得
    categories = Budget.CATEGORY_CHOICES
    
    if request.method == 'POST':
        for category_code, category_name in categories:
            amount = request.POST.get(f'budget_{category_code}', 0)
            if amount:
                # ユーザーとカテゴリが一致するものを更新、なければ作成
                CategoryBudget.objects.update_or_create(
                    user=request.user,
                    category=category_code,
                    defaults={'amount': int(amount)}
                )
        messages.success(request, "予算設定を更新したで！✨")
        return redirect('budget_list')

    # 現在の設定値を取得して辞書にする { 'food': 30000, ... }
    current_budgets = {
        cb.category: cb.amount 
        for cb in CategoryBudget.objects.filter(user=request.user)
    }

    # 画面表示用に「カテゴリ名、コード、現在の予算額」のリストを作る
    config_list = [
        {'code': code, 'name': name, 'amount': current_budgets.get(code, 0)}
        for code, name in categories
    ]

    return render(request, 'recipes/budget_config.html', {'config_list': config_list})

@login_required
def inventory_list(request):
    items = Inventory.objects.filter(user=request.user).order_by('expiration_date')
    
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.user = request.user
            inventory.save()
            return redirect('inventory_list')
    else:
        form = InventoryForm()
        
    return render(request, 'recipes/inventory_list.html', {'items': items, 'form': form})

# recipes/views.py

@login_required
def inventory_delete(request, pk):
    # 他人の食材を勝手に消せないように、user=request.user を入れるのがQA的お約束！
    item = get_object_or_404(Inventory, pk=pk, user=request.user)
    item.delete()
    return redirect('inventory_list')