from django.db import models

class Recipe(models.Model):
    title = models.CharField('料理名', max_length=100)
    tool = models.CharField('調理器具（レンジ・炊飯器など）', max_length=50)
    poster = models.CharField('投稿者', max_length=50, default='りえ')
    image = models.ImageField('完成写真', upload_to='recipes/', null=True, blank=True)
    ingredients = models.TextField('材料')
    instructions = models.TextField('作り方（3ステップ！）')
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    def str(self):
        return self.title