import React, { useState } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  TextInputProps,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface CustomInputProps extends TextInputProps {
  label?: string;
  error?: string;
  leftIcon?: keyof typeof Ionicons.glyphMap;
  rightIcon?: keyof typeof Ionicons.glyphMap;
  onRightIconPress?: () => void;
  containerStyle?: ViewStyle;
  required?: boolean;
}

const CustomInput: React.FC<CustomInputProps> = ({
  label,
  error,
  leftIcon,
  rightIcon,
  onRightIconPress,
  containerStyle,
  required = false,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);

  const handleFocus = (e: any) => {
    setIsFocused(true);
    if (props.onFocus) {
      props.onFocus(e);
    }
  };

  const handleBlur = (e: any) => {
    setIsFocused(false);
    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const inputContainerStyle = [
    styles.inputContainer,
    isFocused && styles.inputContainerFocused,
    error && styles.inputContainerError,
  ];

  return (
    <View style={[styles.container, containerStyle]}>
      {label && (
        <Text style={styles.label}>
          {label}
          {required && <Text style={styles.required}> *</Text>}
        </Text>
      )}
      
      <View style={inputContainerStyle}>
        {leftIcon && (
          <Ionicons
            name={leftIcon}
            size={20}
            color={isFocused ? '#0066cc' : '#666'}
            style={styles.leftIcon}
          />
        )}
        
        <TextInput
          {...props}
          style={[styles.input, props.style]}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholderTextColor="#999"
        />
        
        {rightIcon && (
          <Ionicons
            name={rightIcon}
            size={20}
            color={isFocused ? '#0066cc' : '#666'}
            style={styles.rightIcon}
            onPress={onRightIconPress}
          />
        )}
      </View>
      
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 8,
  },
  required: {
    color: '#dc3545',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#fff',
    paddingHorizontal: 12,
    minHeight: 48,
  },
  inputContainerFocused: {
    borderColor: '#0066cc',
    shadowColor: '#0066cc',
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  inputContainerError: {
    borderColor: '#dc3545',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    paddingVertical: 12,
  },
  leftIcon: {
    marginRight: 12,
  },
  rightIcon: {
    marginLeft: 12,
  },
  errorText: {
    fontSize: 14,
    color: '#dc3545',
    marginTop: 4,
  },
});

export default CustomInput; 