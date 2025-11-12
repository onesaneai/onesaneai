
#Custom User Model 
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.crypto import get_random_string

from django.db import models
import hashlib,random,string,pyotp

class CustomUserManager(BaseUserManager):
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        username = username or email.split('@')[0]

        # Ensure username is not passed twice
        extra_fields.pop('username', None)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username=username, email=email, password=password, **extra_fields)

class Profile(AbstractUser):
    email = models.EmailField(unique=True)
    objects = CustomUserManager()

    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    # auth_token = models.CharField(max_length=255, blank=True, null=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    # ... your existing fields ...
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name if self.last_name else ''}".strip()
        return self.username
    
    def generate_totp_secret(self):
        if not self.totp_secret:
            self.totp_secret = pyotp.random_base32()
            self.save()
        return self.totp_secret

    def get_totp_uri(self):
        self.generate_totp_secret()
        return f"otpauth://totp/Oneane AI:{self.get_full_name() if self.get_full_name() else self.username}?secret={self.totp_secret}&issuer=Onesane AI"
 
    def get_profile_image_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return '/static/images/default_profile.png'  # Default image path

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.is_2fa_enabled:
            self.generate_totp_secret()
        else:
            self.totp_secret = ""
        return super().save(force_insert, force_update, using, update_fields)


def generate_random_string(length):
    """
    Generates a random string of a specified length.

    Args:
        length (int): The desired length of the random string.

    Returns:
        str: The generated random string.
    """
    # Define the pool of characters to choose from
    # This includes lowercase and uppercase letters, and digits
    characters = string.ascii_letters + string.digits 

    # Use random.choices to select 'length' characters with replacement
    # Then, join them to form a single string
    random_string = ''.join(random.choices(characters, k=length))
    return random_string


def generate_deterministic_id(input_string):
  """
  Generates a unique and deterministic ID from a given string using SHA256.

  Args:
    input_string: The string to generate an ID from.

  Returns:
    A hexadecimal string representing the unique ID.
  """
  input_string+=generate_random_string(10)
  # Encode the string to bytes, as hash functions operate on bytes
  encoded_string = input_string.encode('utf-8')

  # Create a SHA256 hash object
  hasher = hashlib.sha256()

  # Update the hash object with the encoded string
  hasher.update(encoded_string)

  # Get the hexadecimal representation of the hash
  unique_id = hasher.hexdigest()

  return unique_id

class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    company = models.CharField(max_length=255)
    service = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    contact_id = models.CharField(max_length=255, unique=True, editable=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.contact_id:
            self.contact_id = generate_deterministic_id(f"{self.first_name}{self.last_name}")
        return super().save(force_insert, force_update, using, update_fields)


class APIKey(models.Model):
    PERMISSION_CHOICES = [
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
    ]

    name = models.CharField(max_length=100, unique=True)
    key = models.CharField(max_length=40, unique=True, editable=False)
    permission = models.CharField(max_length=5, choices=PERMISSION_CHOICES, default='read')
    rate_limit_per_minute = models.PositiveIntegerField(default=60)  # default 60 requests/min
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_request_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = get_random_string(length=40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.permission})"

