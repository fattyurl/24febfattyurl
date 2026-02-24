from django import forms
from .utils import validate_url, validate_slug
from .models import Link


class ShortenerForm(forms.Form):
    url = forms.URLField(
        max_length=2048,
        widget=forms.URLInput(attrs={
            'placeholder': 'Paste your long URL here...',
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg',
            'autofocus': True,
        }),
    )
    custom_slug = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'custom-slug (optional)',
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
    )

    def clean_url(self):
        url = self.cleaned_data['url']
        valid, error = validate_url(url)
        if not valid:
            raise forms.ValidationError(error)
        return url

    def clean_custom_slug(self):
        slug = self.cleaned_data.get('custom_slug', '').strip()
        if not slug:
            return ''
        valid, error = validate_slug(slug)
        if not valid:
            raise forms.ValidationError(error)
        if Link.objects.filter(short_code=slug).exists() or Link.objects.filter(custom_slug=slug).exists():
            raise forms.ValidationError("This slug is already taken.")
        return slug


class LinkEditForm(forms.Form):
    original_url = forms.URLField(
        max_length=2048,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
    )
    title = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Link title (optional)',
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
    )

    def clean_original_url(self):
        url = self.cleaned_data['original_url']
        valid, error = validate_url(url)
        if not valid:
            raise forms.ValidationError(error)
        return url
