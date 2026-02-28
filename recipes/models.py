from django.db import models

class Recipe(models.Model):
    # --- 新しく追加：選べる選択肢のリスト ---
    CATEGORY_CHOICES = [
        ('メイン', 'メインのおかず'),
        ('副菜', '副菜・おつまみ'),
        ('ご飯・麺', 'ご飯・麺類'),
        ('スープ', 'スープ・汁物'),
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
    poster = models.CharField('投稿者', max_length=50, default='Rie')
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
    memo = models.TextField('パパの味付けメモ（次回への改善点など）', blank=True, null=True)
    
    # ④ 作った日付
    created_at = models.DateTimeField('作った日', auto_now_add=True)

    def __str__(self):
        # 管理画面で「カレーの記録 (2026-03-01)」みたいに見やすくする設定
        return f"{self.recipe.title} の記録 ({self.created_at.strftime('%Y-%m-%d')})"