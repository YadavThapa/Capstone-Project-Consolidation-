"""Django forms for the news app - ContactForm and CustomUserCreationForm."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import ContactMessage

User = get_user_model()


class ContactForm(forms.ModelForm):
    """Contact message form used on the site contact page."""

    class Meta:
        """Model metadata for ContactForm."""
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with role selection for CustomUser model."""

    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address.",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    # Role selection field with descriptions
    role = forms.ChoiceField(
        choices=[
            ('reader',
             'Reader - Browse and read articles, subscribe to publishers '
             'and journalists'),
            ('journalist',
             'Journalist - Write and publish articles, create newsletters'),
            ('editor',
             'Editor - Review and approve articles, manage content'),
        ],
        initial='reader',
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text="Select your intended role. This determines your "
                  "permissions and features."
    )

    # Additional fields for specific roles
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        help_text="Your first name (recommended for journalists and editors)"
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text="Your last name (recommended for journalists and editors)"
    )

    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tell us about yourself, your interests, or '
                           'professional background...'
        }),
        required=False,
        max_length=500,
        help_text="Brief bio (optional, but recommended for journalists "
                  "and editors)"
    )

    class Meta:
        """Meta configuration for CustomUserCreationForm."""
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role',
                  'bio', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes to form fields
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'

        # Update field help texts and labels
        self.fields['username'].help_text = (
            "Required. 150 characters or fewer. Letters, digits and "
            "@/./+/-/_ only."
        )
        self.fields['password1'].help_text = (
            "Your password must contain at least 8 characters."
        )
        self.fields['password2'].help_text = (
            "Enter the same password as before, for verification."
        )

        # Customize username placeholder
        self.fields['username'].widget.attrs['placeholder'] = (
            'Choose a unique username'
        )

    def clean_role(self):
        """Validate role selection."""
        role = self.cleaned_data.get('role')
        valid_roles = ['reader', 'journalist', 'editor']

        if role not in valid_roles:
            raise forms.ValidationError("Please select a valid role.")

        return role

    def clean(self):
        """Additional validation for role-specific requirements."""
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        # Recommend names for journalists and editors
        if role in ['journalist', 'editor']:
            if not first_name and not last_name:
                # Don't make it required, but add a helpful message
                self.add_error(
                    'first_name',
                    f"First and last names are recommended for {role}s "
                    f"to build credibility with readers."
                )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.bio = self.cleaned_data.get('bio', '')

        if commit:
            user.save()
            # Assign appropriate permissions based on role
            user.assign_group()

        return user


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information."""

    class Meta:
        """Meta configuration for ProfileEditForm."""
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'profile_picture': 'Profile Picture',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].help_text = ("We'll never share your email "
                                          "with anyone else.")
        self.fields['profile_picture'].help_text = (
            "Upload a professional profile photo (JPG, PNG). Max size: 5MB"
        )
