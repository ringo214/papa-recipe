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

# ==========================================
# 1. Gemini AI の設定 (2026年最新Client方式)
# ==========================================
# ※APIキーはりえさんの最新のものに差し替えています
client = genai.Client(api_key='AIzaSyArWFvoeDALopyvh4pmkSKCMPfZvC_vHYk')

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

    context = {
        'recipes': recipes,
        'tools': tools,
        'authors': authors,
        'category_choices': category_choices,
        'difficulty_choices': difficulty_choices,
        'fridge_items': fridge_items, # 🌟 これも入れておくとデバッグしやすい
    }

    # 🌟 各レシピに「作れるかどうか」のフラグを立てる
    for recipe in recipes:
        # 材料欄（ingredients）の中に、冷蔵庫の食材がいくつ入っているかカウント
        match_count = 0
        for item in fridge_items:
            if item in recipe.ingredients: # 簡易的な文字列マッチング
                match_count += 1
        
        # 2つ以上一致したら「今すぐ作れる！」バッジを出すフラグ
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
    # --- A. 準備（まず現在の日付を確定させる） ---
    now = timezone.now()
    year = now.year
    month = now.month
    current_month_display = f"{year}年{month}月"

    # 🌟 URLパラメータから年・月を取得。なければ今月。
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    
    # --- 前後の月を計算する魔法 ---
    this_month_date = datetime.date(year, month, 1)
    # 前の月
    prev_month_date = this_month_date - datetime.timedelta(days=1)
    # 次の月（今月の1日に32日足せば必ず翌月になる）
    next_month_date = (this_month_date + datetime.timedelta(days=32)).replace(day=1)

    # --- B. 保存処理 (POSTの時だけ動く) ---
    if request.method == 'POST' and request.POST.get('save_from_scan') == 'true':
        budget_id = request.POST.get('budget_id')
        date = request.POST.get('date')
        item_name = request.POST.get('item_name')
        amount = request.POST.get('amount')
        category = request.POST.get('category')

        # 🌟 1. 強力な重複チェック（日付と金額で判定）
        if not budget_id:
            duplicate = Budget.objects.filter(
                user=request.user, 
                date=date, 
                amount=amount
            ).first()
            
            if duplicate:
                # 🌟 messages.error を warning に変更！
                messages.warning(request, f"それ、もう登録済みちゃう？（既にある項目：{duplicate.item_name}）")
                
                # 🛑 【重要】ここで処理を止めてリダイレクトする！
                # これがないと、下の「Budget.objects.create」まで進んでしまいます
                return redirect('budget_list')

        # 2. 家計簿データの保存/更新
        if budget_id:
            budget = get_object_or_404(Budget, pk=budget_id, user=request.user)
            budget.date, budget.item_name = date, item_name
            budget.amount, budget.category = amount, category
            budget.save()
            messages.success(request, "データを修正したで！✨")
        else:
            # 1. 家計簿に登録（店名と合計金額）
            Budget.objects.create(
                user=request.user, date=date, item_name=item_name,
                amount=amount, category=category
            )

            # 🌟 2. チェックされた商品を一括で冷蔵庫に入れる
            selected_items = request.POST.getlist('selected_items')
            
            if category == 'food' and selected_items:
                for product_name in selected_items:
                    # 🌟 購入日（date）も一緒に保存する
                    Inventory.objects.create(
                        user=request.user,
                        name=product_name,
                        purchase_date=date, # レシートの日付を入れる！
                        quantity=1,
                        unit="個"
                    )
                messages.success(request, f"家計簿と、冷蔵庫に食材を入れといたで！❄️")
            else:
                messages.success(request, "家計簿に登録したで！💰")
        
        return redirect('budget_list')

    # --- C. 表示用データの計算 (POSTでもGETでも、最後は必ずここを通る) ---

    # 1. 今月のリスト取得 (カンマ忘れ修正済み！)
    # 🌟 指定された年・月でフィルタリング
    budgets = Budget.objects.filter(
        user=request.user, 
        date__year=year, 
        date__month=month
    ).order_by('-date')

    # 2. カテゴリ別の「予算 vs 実績」計算
    actual_data = budgets.values('category').annotate(total=Sum('amount'))
    actual_dict = {item['category']: item['total'] for item in actual_data}
    category_budgets = CategoryBudget.objects.filter(user=request.user)
    
    category_status = []
    for cb in category_budgets:
        spent = actual_dict.get(cb.category, 0)
        percent = (spent / cb.amount * 100) if cb.amount > 0 else 0
        category_status.append({
            'display_name': cb.get_category_display(),
            'budget': cb.amount, 'spent': spent,
            'remaining': cb.amount - spent,
            'percent': min(percent, 100),
            'is_over': spent > cb.amount
        })

    # 3. グラフ用データの作成
    category_map = dict(Budget.CATEGORY_CHOICES)
    labels = [category_map.get(item['category'], item['category']) for item in actual_data]
    graph_data = [item['total'] for item in actual_data]

    # --- D. まとめて画面に送る ---
    context = {
        'budgets': budgets,
        'current_month': current_month_display, # 👈 これで () が埋まる！
        'category_status': category_status,
        'labels': json.dumps(labels),
        'data': json.dumps(graph_data),
        'current_month_display': f"{year}年{month}月",
        'prev_year': prev_month_date.year,
        'prev_month': prev_month_date.month,
        'next_year': next_month_date.year,
        'next_month': next_month_date.month,
    }
    return render(request, 'recipes/budget_list.html', context)

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

# 🌟 【重要】明日APIが復活したら、ここを False に戻すだけ！
USE_MOCK = True

# recipes/views.py

@login_required
def receipt_scan(request):
    if request.method == 'POST' and request.FILES.get('receipt_image'):
        
        # 🌟 ここでモック用のデータを「リスト形式」で作る
        if USE_MOCK:
            # 1. カンマ区切りの文字列を用意
            raw_string = 'たまご,牛乳,豚バラ肉,小松菜,豆腐,納豆'
            
            # 2. 文字列を [リスト] に変換する
            # split(',') でバラバラにして、strip() で余計な空白を取る
            item_list = [i.strip() for i in raw_string.split(',') if i.strip()]
            
            scan_data = {
                'date': timezone.now().strftime('%Y-%m-%d'),
                'item_name': 'イオンフードスタイル守口店',
                'amount': 2450,
                'category': 'food',
                # 🌟 【最重要】ここ！HTMLの {% for item in scan_data.item_list_raw %} と名前を合わせる
                'item_list_raw': item_list 
            }
            messages.info(request, "⚠️ モックモード：たまごリスト出現準備完了！")
        else:
            # (APIが復活した時の処理：今はコメントアウト中のはず)
            scan_data = {} 

        # 🌟 第二引数として scan_data を渡す
        return render(request, 'recipes/receipt_confirm.html', {
            'scan_data': scan_data,
        })

    return redirect('budget_list')

# @login_required
# def receipt_scan(request):
#     if request.method == 'POST' and request.FILES.get('receipt_image'):
#         try:
#             img_file = request.FILES['receipt_image']
#             img_data = img_file.read()

#             # 🌟 修正：プロンプトのカテゴリーをりえさんのモデル(Budget.CATEGORY_CHOICES)のキーに合わせる
#             prompt = """
#             レシート画像を解析し、以下のJSON形式で返してください。
#             categoryは (food, dining, daily, beauty, transport, education, utilities, other) から選んでください。
            
#             {"date": "YYYY-MM-DD", "item_name": "店舗名", "amount": 0, "category": "category_key"}
#             """

#             response = client.models.generate_content(
#                 model='gemini-2.5-flash',
#                 contents=[
#                     prompt,
#                     types.Part.from_bytes(data=img_data, mime_type=img_file.content_type)
#                 ]
#             )

#             res_text = response.text.replace('```json', '').replace('```', '').strip()
#             data = json.loads(res_text)
#             if isinstance(data, list): data = data[0]

#             # 🌟 ここが重要！モデルの選択肢をまるごと画面に送る
#             category_choices = Budget.CATEGORY_CHOICES

#             return render(request, 'recipes/receipt_confirm.html', {
#                 'data': data,
#                 'category_choices': category_choices, # 👈 これで8種類全部届く！
#             })

#         except Exception as e:
#             return HttpResponse(f"エラー発生：{e}")

#     return redirect('budget_list')

class SignUpView(SuccessMessageMixin, generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')  # 登録できたらログイン画面へ
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