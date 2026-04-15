from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from products.models import Product


class RegisterForm(forms.Form):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')

        UserModel = get_user_model()
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError('Username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        UserModel = get_user_model()
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError('Email is already in use.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Password and confirm password must match.')

        if role not in {'user', 'admin'}:
            self.add_error('role', 'Role must be either "user" or "admin".')

        return cleaned_data


class LoginForm(forms.Form):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    identifier = forms.CharField(max_length=254, label='Username or Email')
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        identifier = (cleaned_data.get('identifier') or '').strip()
        role = cleaned_data.get('role')
        password = cleaned_data.get('password')

        if not identifier or not password or not role:
            return cleaned_data

        if role not in {'user', 'admin'}:
            raise forms.ValidationError('Please choose a valid role.')

        UserModel = get_user_model()
        if '@' in identifier:
            user_obj = UserModel.objects.filter(email__iexact=identifier).first()
        else:
            user_obj = UserModel.objects.filter(username=identifier).first()

        if not user_obj:
            raise forms.ValidationError('Invalid credentials.')

        user = authenticate(username=user_obj.username, password=password)
        if user is None:
            raise forms.ValidationError('Invalid credentials.')

        is_admin = (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'is_staff', False)
            or getattr(user, 'is_admin', False)
        )

        if role == 'admin' and not is_admin:
            raise forms.ValidationError('This account does not have admin access.')

        if role == 'user' and is_admin:
            raise forms.ValidationError('Please select Admin role for this account.')

        self.user = user

        return cleaned_data


class AdminRegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')

        UserModel = get_user_model()
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError('Username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        UserModel = get_user_model()
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError('Email is already in use.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Password and confirm password must match.')

        return cleaned_data

    def save(self):
        UserModel = get_user_model()
        user = UserModel.objects.create_user(
            username=self.cleaned_data['username'].strip(),
            email=self.cleaned_data['email'].strip().lower(),
            password=self.cleaned_data['password'],
            phone='',
            address='',
        )
        if hasattr(user, 'is_staff'):
            user.is_staff = True
        if hasattr(user, 'is_admin'):
            user.is_admin = True
        user.save()
        return user


class AdminLoginForm(forms.Form):
    identifier = forms.CharField(max_length=254, label='Username or Email')
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        identifier = (cleaned_data.get('identifier') or '').strip()
        password = cleaned_data.get('password')

        if not identifier or not password:
            return cleaned_data

        UserModel = get_user_model()
        if '@' in identifier:
            user_obj = UserModel.objects.filter(email__iexact=identifier).first()
        else:
            user_obj = UserModel.objects.filter(username=identifier).first()

        if not user_obj:
            raise forms.ValidationError('Invalid admin credentials.')

        user = authenticate(username=user_obj.username, password=password)
        if user is None:
            raise forms.ValidationError('Invalid admin credentials.')

        self.user = user
        return cleaned_data


class ProfileEditForm(forms.Form):
    full_name = forms.CharField(label='Full Name', max_length=150, widget=forms.TextInput(attrs={'class': 'profile-input', 'placeholder': 'Your full name'}))
    email = forms.EmailField(label='Email Address', widget=forms.EmailInput(attrs={'class': 'profile-input', 'placeholder': 'you@example.com'}))
    phone = forms.CharField(label='Phone Number', max_length=20, widget=forms.TextInput(attrs={'class': 'profile-input', 'placeholder': 'Phone number'}))
    address = forms.CharField(label='Address', widget=forms.Textarea(attrs={'class': 'profile-textarea', 'rows': 4, 'placeholder': 'Street address, city, country'}))

    def clean_full_name(self):
        full_name = self.cleaned_data['full_name'].strip()
        if len(full_name) < 2:
            raise forms.ValidationError('Please enter your full name.')
        return full_name

    def save(self, user):
        full_name = self.cleaned_data['full_name'].split()
        user.first_name = full_name[0]
        user.last_name = ' '.join(full_name[1:]) if len(full_name) > 1 else ''
        user.email = self.cleaned_data['email'].strip().lower()
        user.phone = self.cleaned_data['phone'].strip()
        user.address = self.cleaned_data['address'].strip()
        user.save(update_fields=['first_name', 'last_name', 'email', 'phone', 'address'])
        return user


class PaymentMethodForm(forms.Form):
    PAYMENT_METHOD_CHOICES = (
        ('esewa', 'eSewa'),
        ('cod', 'Cash on Delivery'),
    )

    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect(attrs={'class': 'payment-radio'}))


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label='Old Password', widget=forms.PasswordInput(attrs={'class': 'profile-input', 'placeholder': 'Current password'}))
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput(attrs={'class': 'profile-input', 'placeholder': 'New password'}))
    new_password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'profile-input', 'placeholder': 'Confirm new password'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data['old_password']
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Old password is incorrect.')
        return old_password

    def clean_new_password1(self):
        new_password1 = self.cleaned_data['new_password1']
        validate_password(new_password1, user=self.user)
        return new_password1

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', 'The new passwords do not match.')

        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save(update_fields=['password'])
        return self.user


class AdminProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'base_price',
            'option_type',
            'options',
            'description',
            'image',
            'is_available',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'Product name'}),
            'category': forms.Select(attrs={'class': 'admin-input'}),
            'base_price': forms.NumberInput(attrs={'class': 'admin-input', 'step': '0.01', 'min': '0'}),
            'option_type': forms.Select(attrs={'class': 'admin-input'}),
            'options': forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'e.g. 6pcs:500,12pcs:900'}),
            'description': forms.Textarea(attrs={'class': 'admin-textarea', 'rows': 4, 'placeholder': 'Product description'}),
            'image': forms.ClearableFileInput(attrs={'class': 'admin-file-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'admin-checkbox'}),
        }

    def clean_base_price(self):
        base_price = self.cleaned_data.get('base_price')
        if base_price is None:
            raise forms.ValidationError('Base price is required.')
        if base_price < 0:
            raise forms.ValidationError('Base price cannot be negative.')
        return base_price


class AdminUserCreateForm(forms.Form):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'admin-input', 'placeholder': 'Email address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'admin-input', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'admin-input', 'placeholder': 'Confirm password'}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'admin-input'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')

        UserModel = get_user_model()
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError('Username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        UserModel = get_user_model()
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError('Email is already in use.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Password and confirm password must match.')

        if role not in {'user', 'admin'}:
            self.add_error('role', 'Role must be either "user" or "admin".')

        return cleaned_data

    def save(self):
        UserModel = get_user_model()
        role = self.cleaned_data['role']

        user = UserModel.objects.create_user(
            username=self.cleaned_data['username'].strip(),
            email=self.cleaned_data['email'].strip().lower(),
            password=self.cleaned_data['password'],
            phone='',
            address='',
        )

        if hasattr(user, 'is_staff'):
            user.is_staff = role == 'admin'
        if hasattr(user, 'is_admin'):
            user.is_admin = role == 'admin'
        if hasattr(user, 'is_superuser'):
            user.is_superuser = False

        user.save()
        return user


class AdminUserEditForm(forms.Form):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'admin-input', 'placeholder': 'Email address'}))
    phone = forms.CharField(required=False, max_length=15, widget=forms.TextInput(attrs={'class': 'admin-input', 'placeholder': 'Phone number'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'admin-textarea', 'rows': 3, 'placeholder': 'Address'}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'admin-input'}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'admin-input', 'placeholder': 'New password (optional)'}))
    confirm_new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'admin-input', 'placeholder': 'Confirm new password'}))

    def __init__(self, *args, user_instance=None, **kwargs):
        self.user_instance = user_instance
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')

        UserModel = get_user_model()
        qs = UserModel.objects.filter(username=username)
        if self.user_instance is not None:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise forms.ValidationError('Username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        UserModel = get_user_model()
        qs = UserModel.objects.filter(email=email)
        if self.user_instance is not None:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise forms.ValidationError('Email is already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')

        if role not in {'user', 'admin'}:
            self.add_error('role', 'Role must be either "user" or "admin".')

        if new_password:
            if len(new_password) < 8:
                self.add_error('new_password', 'Password must be at least 8 characters.')
            if new_password != confirm_new_password:
                self.add_error('confirm_new_password', 'Password and confirm password must match.')
        elif confirm_new_password:
            self.add_error('new_password', 'Please enter a new password first.')

        return cleaned_data

    def save(self):
        if self.user_instance is None:
            raise ValueError('AdminUserEditForm.save() requires a user_instance.')

        user = self.user_instance
        role = self.cleaned_data['role']

        user.username = self.cleaned_data['username'].strip()
        user.email = self.cleaned_data['email'].strip().lower()
        if hasattr(user, 'phone'):
            user.phone = (self.cleaned_data.get('phone') or '').strip()
        if hasattr(user, 'address'):
            user.address = (self.cleaned_data.get('address') or '').strip()
        if hasattr(user, 'is_staff'):
            user.is_staff = role == 'admin'
        if hasattr(user, 'is_admin'):
            user.is_admin = role == 'admin'

        new_password = (self.cleaned_data.get('new_password') or '').strip()
        if new_password:
            user.set_password(new_password)

        user.save()
        return user