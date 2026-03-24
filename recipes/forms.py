from django import forms
from .models import CookLog
from .models import CookLog, Comment
from .models import Recipe, CookLog, Comment

class CookLogForm(forms.ModelForm):
    class Meta:
        model = CookLog
        # お父様に入力してもらう項目（写真とメモ）だけを指定！
        fields = ['photo', 'memo']

        # お父様がスマホで押しやすいように、デザインや枠の大きさを設定！
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'style': 'padding: 10px; font-size: 16px;'}),
            'memo': forms.Textarea(attrs={'rows': 3, 'placeholder': '例：醤油を少し多めにしたら美味しかった！', 'style': 'width: 100%; border-radius: 10px; padding: 10px; border: 1px solid #ddd;'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['author', 'text']
        widgets = {
            'author': forms.TextInput(attrs={'placeholder': 'お名前（例：ママ）', 'style': 'padding: 8px; border-radius: 5px; border: 1px solid #ccc; width: 100%; box-sizing: border-box;'}),
            'text': forms.Textarea(attrs={'rows': 2, 'placeholder': '美味しそう！今度作って！', 'style': 'padding: 8px; border-radius: 5px; border: 1px solid #ccc; width: 100%; box-sizing: border-box; margin-top: 5px;'}),
        }

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'category', 'difficulty', 'tool', 'image', 'ingredients', 'instructions', 'author']
        # ※スマホから入力しやすいように、少しだけデザインを当てます
        widgets = {
            'author': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px;'}),
            'title': forms.TextInput(attrs={'style': 'width: 100%; padding: 8px;'}),
            'ingredients': forms.Textarea(attrs={'rows': 5, 'style': 'width: 100%; padding: 8px;'}),
            'instructions': forms.Textarea(attrs={'rows': 5, 'style': 'width: 100%; padding: 8px;'}),
        }