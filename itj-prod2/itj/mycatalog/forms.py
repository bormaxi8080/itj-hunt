from django import forms


class ParsingPositionsForm(forms.Form):
    hidden_positions_dict = forms.CharField(widget=forms.HiddenInput(), label='hidden_positions_dict')
    db_positions_to_archive = forms.CharField(widget=forms.HiddenInput(), label='db_positions_to_archive')
    parsing_rules_dict = forms.CharField(widget=forms.HiddenInput(), label='parsing_rules_dict')
