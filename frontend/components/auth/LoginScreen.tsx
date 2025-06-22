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

interface LoginFormData {
  email: string;
  password: string;
}

interface LoginFormErrors {
  email?: string;
  password?: string;
}

const LoginScreen: React.FC = () => {
  const { login, isLoading } = useAuth();
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [showPassword, setShowPassword] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: LoginFormErrors = {};

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof LoginFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleLogin = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      const response = await login(formData);
      
      if (response.success) {
        console.log('LoginScreen: Login successful, navigating to home');
        // Navigation will be handled by the auth context changes
        router.replace('/(tabs)' as any);
      } else {
        Alert.alert(
          'Login Failed',
          response.error || 'Invalid email or password. Please try again.'
        );
      }
    } catch (error) {
      Alert.alert(
        'Error',
        'An unexpected error occurred. Please try again.'
      );
    }
  };

  const handleForgotPassword = () => {
    Alert.alert(
      'Reset Password',
      'Password reset functionality will be implemented soon.',
      [{ text: 'OK' }]
    );
  };

  const handleSignUp = () => {
    router.push('/register' as any);
  };

  if (isLoading) {
    return <LoadingSpinner message="Signing in..." />;
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Welcome Back!</Text>
            <Text style={styles.subtitle}>
              Sign in to continue your learning journey
            </Text>
          </View>

          {/* Login Form */}
          <View style={styles.form}>
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
              placeholder="Enter your password"
              value={formData.password}
              onChangeText={(value) => handleInputChange('password', value)}
              error={errors.password}
              leftIcon="lock-closed-outline"
              rightIcon={showPassword ? 'eye-off-outline' : 'eye-outline'}
              onRightIconPress={() => setShowPassword(!showPassword)}
              secureTextEntry={!showPassword}
              autoComplete="password"
              required
            />

            <CustomButton
              title="Sign In"
              onPress={handleLogin}
              variant="primary"
              size="large"
              style={styles.loginButton}
            />

            <CustomButton
              title="Forgot Password?"
              onPress={handleForgotPassword}
              variant="outline"
              size="medium"
              style={styles.forgotButton}
            />
          </View>

          {/* Sign Up Link */}
          <View style={styles.signUpContainer}>
            <Text style={styles.signUpText}>Don't have an account? </Text>
            <CustomButton
              title="Sign Up"
              onPress={handleSignUp}
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
    justifyContent: 'center',
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
  loginButton: {
    marginTop: 8,
    marginBottom: 16,
  },
  forgotButton: {
    marginTop: 8,
  },
  signUpContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 'auto',
  },
  signUpText: {
    fontSize: 16,
    color: '#666',
    marginRight: 8,
  },
});

export default LoginScreen; 