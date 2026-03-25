from django import forms
from .models import Recipe, CookLog, Comment, CategoryBudget, Inventory, Budget # 🌟 まとめてインポート

class CookLogForm(forms.ModelForm):
    class Meta:
        model = CookLog
        fields = ['photo', 'memo']
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
        fields = ['title', 'tool', 'image', 'ingredients', 'instructions', 'category', 'difficulty']

# 🌟 これが足りなかった「家計簿手動入力用」のフォーム！
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['date', 'item_name', 'amount', 'category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
            'item_name': forms.TextInput(attrs={'placeholder': '品目名', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
            'amount': forms.NumberInput(attrs={'placeholder': '金額', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
            'category': forms.Select(attrs={'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
        }

class CategoryBudgetForm(forms.ModelForm):
    class Meta:
        model = CategoryBudget
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'budget-input', 'placeholder': '金額を入力'}),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'quantity', 'unit', 'expiration_date']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
            'name': forms.TextInput(attrs={'placeholder': '食材名', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
            'quantity': forms.NumberInput(attrs={'placeholder': '数量', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
            'unit': forms.TextInput(attrs={'placeholder': '単位', 'style': 'padding: 10px; border-radius: 10px; border: 1px solid #ddd;'}),
        }