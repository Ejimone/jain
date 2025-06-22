import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import CustomInput from '../common/CustomInput';
import CustomButton from '../common/CustomButton';
import LoadingSpinner from '../common/LoadingSpinner';

interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
}

interface RegisterFormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  firstName?: string;
  lastName?: string;
}

const RegisterScreen: React.FC = () => {
  const { register, isLoading } = useAuth();
  const [formData, setFormData] = useState<RegisterFormData>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
  });
  const [errors, setErrors] = useState<RegisterFormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: RegisterFormErrors = {};

    // First name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }

    // Last name validation
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, and underscores';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter, one lowercase letter, and one number';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof RegisterFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleRegister = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      const registerData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
      };

      const response = await register(registerData);
      
      if (response.success) {
        console.log('RegisterScreen: Registration successful, navigating to home');
        Alert.alert(
          'Registration Successful!',
          'Welcome to Examify! Your account has been created successfully.',
          [
            {
              text: 'Continue',
              onPress: () => router.replace('/(tabs)' as any),
            },
          ]
        );
      } else {
        Alert.alert(
          'Registration Failed',
          response.error || 'Unable to create account. Please try again.'
        );
      }
    } catch (error) {
      Alert.alert(
        'Error',
        'An unexpected error occurred. Please try again.'
      );
    }
  };

  const handleSignIn = () => {
    router.back();
  };

  if (isLoading) {
    return <LoadingSpinner message="Creating your account..." />;
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={styles.title}>Create Account</Text>
            <Text style={styles.subtitle}>
              Join thousands of students preparing for success
            </Text>
          </View>

          <View style={styles.form}>
            <View style={styles.row}>
              <CustomInput
                label="First Name"
                placeholder="Enter your first name"
                value={formData.firstName}
                onChangeText={(value) => handleInputChange('firstName', value)}
                error={errors.firstName}
                containerStyle={styles.halfInput}
                autoCapitalize="words"
                required
              />

              <CustomInput
                label="Last Name"
                placeholder="Enter your last name"
                value={formData.lastName}
                onChangeText={(value) => handleInputChange('lastName', value)}
                error={errors.lastName}
                containerStyle={styles.halfInput}
                autoCapitalize="words"
                required
              />
            </View>

            <CustomInput
              label="Username"
              placeholder="Choose a username"
              value={formData.username}
              onChangeText={(value) => handleInputChange('username', value)}
              error={errors.username}
              leftIcon="person-outline"
              autoCapitalize="none"
              required
            />

            <CustomInput
              label="Email Address"
              placeholder="Enter your email"
              value={formData.email}
              onChangeText={(value) => handleInputChange('email', value)}
              error={errors.email}
              leftIcon="mail-outline"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              required
            />

            <CustomInput
              label="Password"
              placeholder="Create a strong password"
              value={formData.password}
              onChangeText={(value) => handleInputChange('password', value)}
              error={errors.password}
              leftIcon="lock-closed-outline"
              rightIcon={showPassword ? 'eye-off-outline' : 'eye-outline'}
              onRightIconPress={() => setShowPassword(!showPassword)}
              secureTextEntry={!showPassword}
              required
            />

            <CustomInput
              label="Confirm Password"
              placeholder="Confirm your password"
              value={formData.confirmPassword}
              onChangeText={(value) => handleInputChange('confirmPassword', value)}
              error={errors.confirmPassword}
              leftIcon="lock-closed-outline"
              rightIcon={showConfirmPassword ? 'eye-off-outline' : 'eye-outline'}
              onRightIconPress={() => setShowConfirmPassword(!showConfirmPassword)}
              secureTextEntry={!showConfirmPassword}
              required
            />

            <CustomButton
              title="Create Account"
              onPress={handleRegister}
              variant="primary"
              size="large"
              style={styles.registerButton}
            />
          </View>

          <View style={styles.signInContainer}>
            <Text style={styles.signInText}>Already have an account? </Text>
            <CustomButton
              title="Sign In"
              onPress={handleSignIn}
              variant="outline"
              size="small"
            />
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContainer: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 22,
  },
  form: {
    marginBottom: 32,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  halfInput: {
    flex: 0.48,
  },
  registerButton: {
    marginTop: 8,
  },
  signInContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 'auto',
  },
  signInText: {
    fontSize: 16,
    color: '#666',
    marginRight: 8,
  },
});

export default RegisterScreen; 