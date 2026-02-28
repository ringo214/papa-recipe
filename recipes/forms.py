from django import forms
from .models import CookLog

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