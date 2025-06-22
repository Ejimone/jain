import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ViewStyle,
  TextStyle,
  ActivityIndicator,
} from 'react-native';

interface CustomButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

const CustomButton: React.FC<CustomButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  style,
  textStyle,
}) => {
  const getButtonStyle = () => {
    const variantStyle = variant === 'primary' ? styles.primaryButton :
                        variant === 'secondary' ? styles.secondaryButton :
                        variant === 'outline' ? styles.outlineButton :
                        styles.dangerButton;
    
    const sizeStyle = size === 'small' ? styles.smallButton :
                     size === 'large' ? styles.largeButton :
                     styles.mediumButton;
    
    const styleArray: any[] = [
      styles.button,
      variantStyle,
      sizeStyle,
    ];
    
    if (disabled || loading) {
      styleArray.push(styles.disabledButton);
    }
    
    if (style) {
      styleArray.push(style);
    }
    
    return styleArray;
  };

  const getTextStyle = () => {
    const variantTextStyle = variant === 'primary' ? styles.primaryText :
                            variant === 'secondary' ? styles.secondaryText :
                            variant === 'outline' ? styles.outlineText :
                            styles.dangerText;
    
    const sizeTextStyle = size === 'small' ? styles.smallText :
                         size === 'large' ? styles.largeText :
                         styles.mediumText;
    
    const styleArray: any[] = [
      styles.text,
      variantTextStyle,
      sizeTextStyle,
    ];
    
    if (disabled || loading) {
      styleArray.push(styles.disabledText);
    }
    
    if (textStyle) {
      styleArray.push(textStyle);
    }
    
    return styleArray;
  };

  return (
    <TouchableOpacity
      style={getButtonStyle()}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'outline' ? '#0066cc' : '#fff'}
          size="small"
        />
      ) : (
        <Text style={getTextStyle()}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  
  // Variants
  primaryButton: {
    backgroundColor: '#0066cc',
  },
  secondaryButton: {
    backgroundColor: '#6c757d',
  },
  outlineButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#0066cc',
  },
  dangerButton: {
    backgroundColor: '#dc3545',
  },
  
  // Sizes
  smallButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    minHeight: 36,
  },
  mediumButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 44,
  },
  largeButton: {
    paddingHorizontal: 24,
    paddingVertical: 16,
    minHeight: 52,
  },
  
  // Text styles
  text: {
    fontWeight: '600',
  },
  primaryText: {
    color: '#fff',
  },
  secondaryText: {
    color: '#fff',
  },
  outlineText: {
    color: '#0066cc',
  },
  dangerText: {
    color: '#fff',
  },
  
  // Text sizes
  smallText: {
    fontSize: 14,
  },
  mediumText: {
    fontSize: 16,
  },
  largeText: {
    fontSize: 18,
  },
  
  // Disabled states
  disabledButton: {
    opacity: 0.6,
  },
  disabledText: {
    opacity: 0.7,
  },
});

export default CustomButton; 