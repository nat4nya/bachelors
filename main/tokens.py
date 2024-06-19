from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

# token pentru resetarea parolei si activarea contului, facut manual
class CustomTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + 
            six.text_type(user.is_active) + six.text_type(user.password)
        )
    
account_activation_token = CustomTokenGenerator()
reset_password_token = CustomTokenGenerator()