from rest_framework import serializers
from django.contrib.auth import authenticate
from core.models import AdminUser
from hr.models import Employee


# -------------------------------
# Admin Login Serializer
# -------------------------------

class AdminLoginSerializer(serializers.Serializer):
    """Serializer for admin user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, data):
        """Validate and authenticate admin user"""
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Email ou mot de passe incorrect',
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'Ce compte est desactive',
                    code='authorization'
                )

            data['user'] = user
            return data
        else:
            raise serializers.ValidationError(
                'Email et mot de passe sont requis',
                code='authorization'
            )


# -------------------------------
# Employee Login Serializer
# -------------------------------

class EmployeeLoginSerializer(serializers.Serializer):
    """Serializer for employee login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Get employee by email (there should be only one active employee with this email)
        try:
            employee = Employee.objects.select_related('organization').get(email=email, is_active=True)
        except Employee.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'Identifiants invalides.'
            })
        except Employee.MultipleObjectsReturned:
            # If multiple employees with same email exist (rare case), take the first active one
            employee = Employee.objects.select_related('organization').filter(
                email=email,
                is_active=True
            ).first()
            if not employee:
                raise serializers.ValidationError({
                    'email': 'Identifiants invalides.'
                })

        # Check password
        if not employee.check_password(password):
            raise serializers.ValidationError({
                'password': 'Identifiants invalides.'
            })

        # Check if organization is active
        if not employee.organization.is_active:
            raise serializers.ValidationError({
                'non_field_errors': "Votre organisation n'est pas active."
            })

        attrs['employee'] = employee
        return attrs
