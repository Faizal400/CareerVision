from django import forms

class CareerExplorerForm(forms.Form):
    cv_file = forms.FileField(
        required=False,
        label="CV File",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.docx,.txt"})
    )
    cv_text = forms.CharField(required=False,label="CV Text", widget=forms.Textarea)
    experience_level = forms.ChoiceField(label="Experience Level",choices=[
        (0, "Intern / Placement"),
        (1, "Graduate / Junior"),
        (2, "Mid"),
        (3, "Senior"),
        (4, "Lead"),
    ])
    def clean(self):
        cleaned = super().clean()
        cv_file = cleaned.get("cv_file")
        cv_text = (cleaned.get("cv_text") or "").strip()
        if not cv_file and not cv_text:
            raise forms.ValidationError("Please upload a CV file or paste your CV text.")
        return cleaned
