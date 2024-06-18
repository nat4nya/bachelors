from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

# token pentru activarea contului, facut manual
class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active))
    
account_activation_token = AccountActivationTokenGenerator()

# token pentru resetarea parolei, facut manual
class ResetPasswordTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + 
            six.text_type(user.is_active) + six.text_type(user.password)
        )

reset_password_token = ResetPasswordTokenGenerator()