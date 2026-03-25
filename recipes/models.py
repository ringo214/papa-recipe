from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Recipe(models.Model):
    # --- 新しく追加：選べる選択肢のリスト ---
    CATEGORY_CHOICES = [
        ('メイン', 'メインのおかず'),
        ('副菜', '副菜・おつまみ'),
        ('ご飯・麺', 'ご飯・麺類'),
        ('スープ', 'スープ・汁物'),
        ('sweets', 'スイーツ'),  # ← これを追加！🍰
    ]

    DIFFICULTY_CHOICES = [
        (1, '★☆☆☆☆（レンジで3ステップ以内！）'),
        (2, '★★☆☆☆（レンジor炊飯器で放置！）'),
        (3, '★★★☆☆（ちょっとステップ多め）'),
        (4, '★★★★☆（フライパン使ってみよう）'),
        (5, '★★★★★（気合の本格派！）'),
    ]

    # --- 今までの箱 ---
    title = models.CharField('料理名', max_length=100)
    tool = models.CharField('調理器具（レンジ・炊飯器など）', max_length=50)
    author = models.CharField("旧・追加者名", max_length=100, null=True, blank=True)
    author_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="追加者(User)", null=True, blank=True)
    image = models.ImageField('完成写真', upload_to='recipes/', null=True, blank=True)
    ingredients = models.TextField('材料')
    instructions = models.TextField('作り方（3ステップ！）')

    # --- 新しく追加した箱！ ---
    category = models.CharField('カテゴリ', max_length=50, choices=CATEGORY_CHOICES, default='メイン')
    difficulty = models.IntegerField('難易度', choices=DIFFICULTY_CHOICES, default=1)

    # --- いつもの ---
    created_at = models.DateTimeField('作成日', auto_now_add=True)

    def __str__(self):
        return self.title

# --- （上のRecipeクラスはそのまま残す） ---

class CookLog(models.Model):
    # ① どのレシピを作ったか？（Recipeの箱とヒモ付ける魔法のコード！）
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='cook_logs', verbose_name='作ったレシピ')

    # ② C案：スマホで撮った写真！
    photo = models.ImageField('完成写真', upload_to='cook_logs/', null=True, blank=True)

    # ③ A案：パパの味付けメモ！
    memo = models.TextField('味付けメモ（アレンジ内容など）', blank=True, null=True)

    # ④ 作った日付
    created_at = models.DateTimeField('作った日', auto_now_add=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="投稿者", null=True) # 👈 追加

    def __str__(self):
        # 管理画面で「カレーの記録 (2026-03-01)」みたいに見やすくする設定
        return f"{self.recipe.title} の記録 ({self.created_at.strftime('%Y-%m-%d')})"

# --- （既存のRecipeとCookLogクラスはそのまま残す） ---

class Comment(models.Model):
    # ① どの料理記録に対するコメントか？（CookLogとヒモ付ける魔法）
    cook_log = models.ForeignKey(CookLog, on_delete=models.CASCADE, related_name='comments', verbose_name='対象の記録')

    # ② 誰が書いたか（ログイン不要にするためのシンプルな文字入力）
    author = models.CharField('お名前', max_length=50, default='')

    # ③ コメントの内容
    text = models.TextField('コメント')

    # ④ コメントした日時
    created_at = models.DateTimeField('投稿日時', auto_now_add=True)

    def __str__(self):
        return f"{self.author}さんからのコメント"
    
# 家計簿：いつ、何を、いくらで買ったか
class Budget(models.Model):
    # 🌟 ユーザー（持ち主）を追加
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="持ち主", null=True, blank=True)
    
    CATEGORY_CHOICES = [
        ('food', '食費（自炊）'),
        ('dining', '外食費'),
        ('daily', '日用品'),
        ('beauty', '美容・健康'),
        ('transport', '交通費'),
        ('education', '自己研鑽・趣味'),
        ('utilities', '固定費（光熱費・通信費）'),
        ('other', 'その他'),
    ]
    date = models.DateField(verbose_name="購入日")
    item_name = models.CharField(max_length=100, verbose_name="品目")
    amount = models.IntegerField(verbose_name="金額")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='food', verbose_name="カテゴリー")

    def __str__(self):
        return f"{self.date} - {self.item_name}"

# recipes/models.py

class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name="食材名")
    
    # 🌟 購入日（レシートから来る日付）
    purchase_date = models.DateField(default=timezone.now, verbose_name="購入日")
    
    # 賞味期限（任意入力用）
    expiration_date = models.DateField(null=True, blank=True, verbose_name="賞味期限")
    
    # 数量と単位（画面には出さないけど、内部データとして持っておく）
    quantity = models.IntegerField(default=1, verbose_name="数量")
    unit = models.CharField(max_length=20, default="個", verbose_name="単位")

    def __str__(self):
        # 購入日を付けて管理しやすくする
        return f"{self.purchase_date} - {self.name}"
    
class CategoryBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    # Budgetモデルと同じCATEGORY_CHOICESを使う
    category = models.CharField(
        max_length=20, 
        choices=Budget.CATEGORY_CHOICES, 
        verbose_name="カテゴリー"
    )
    amount = models.IntegerField(verbose_name="予算額", default=0)

    class Meta:
        # 同じユーザーが同じカテゴリを2回登録できないようにする（QA的整合性チェック）
        unique_together = ('user', 'category')

    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()}: ¥{self.amount}"