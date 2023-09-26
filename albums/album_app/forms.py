from django import forms

from album_app.models import UserChoice

class UserChoiceForm(forms.ModelForm):
    class Meta:
        model = UserChoice
        fields = ['choice']

class YearFilterForm(forms.Form):
    min_year = forms.IntegerField(required=False, label='Minimum')
    max_year = forms.IntegerField(required=False, label='Maximum')

class SearchForm(forms.Form):
    search_input = forms.CharField(required=False, label='Search')

class AcousticnessForm(forms.Form):
    OPTIONS = (
        ('option1', "when the party's over - Billie Eilish"),
        ('option2', "American Idiot - Green Day"),
        ('option3', 'Me & You Together Song - The 1975'),
        ('option4', 'Option 4'),
        ('option5', 'Option 5'),
    )
    
    selected_ac_options = forms.MultipleChoiceField(
        choices=OPTIONS,
        widget=forms.CheckboxSelectMultiple,
    )

class DanceabilityForm(forms.Form):
    OPTIONS = (
        ('option1', "Anaconda - Nicki Minaj"),
        ('option2', "Fake Love - Drake"),
        ('option3', 'Around The World - Daft Punk'),
        ('option4', 'Born To Die - Lana Del Rey'),
        ('option5', 'Option 5'),
    )
    
    selected_da_options = forms.MultipleChoiceField(
        choices=OPTIONS,
        widget=forms.CheckboxSelectMultiple,
    )

class LoudnessForm(forms.Form):
    OPTIONS = (
        ('option1', "Levitating - Dua Lipa"),
        ('option2', "Azul - J Balvin"),
        ('option3', 'Shivers - Ed Sheeran'),
        ('option4', 'Option 4'),
        ('option5', 'Option 5'),
    )
    
    selected_da_options = forms.MultipleChoiceField(
        choices=OPTIONS,
        widget=forms.CheckboxSelectMultiple,
    )

class SpeechinessForm(forms.Form):
    OPTIONS = (
        ('option1', "All Too Well - Taylor Swift"),
        ('option2', "I Wanna Be Yours - Arctic Monkeys"),
        ('option3', 'Perfect - Ed Sheeran'),
        ('option4', 'Option 4'),
        ('option5', 'Option 5'),
    )
    
    selected_da_options = forms.MultipleChoiceField(
        choices=OPTIONS,
        widget=forms.CheckboxSelectMultiple,
    )

class ValenceForm(forms.Form):
    OPTIONS = (
        ('option1', "There's Nothing Holdin' Me Back - Shawn Mendes"),
        ('option2', "The Lazy Song - Bruno Mars"),
        ('option3', 'Perfect - Ed Sheeran'),
        ('option4', 'Born To Die - Lana Del Rey'),
        ('option5', 'Option 5'),
    )
    
    selected_da_options = forms.MultipleChoiceField(
        choices=OPTIONS,
        widget=forms.CheckboxSelectMultiple,
    )