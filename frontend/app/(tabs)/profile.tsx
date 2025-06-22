import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';
import CustomButton from '../../components/common/CustomButton';

const ProfileScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          onPress: logout,
          style: 'destructive',
        },
      ]
    );
  };

  const handleEditProfile = () => {
    // TODO: Navigate to edit profile screen
    Alert.alert('Edit Profile', 'Profile editing will be implemented soon.');
  };

  const handleChangePassword = () => {
    // TODO: Navigate to change password screen
    Alert.alert('Change Password', 'Password change will be implemented soon.');
  };

  const profileSections = [
    {
      title: 'Account',
      items: [
        {
          icon: 'person-outline',
          title: 'Edit Profile',
          subtitle: 'Update your personal information',
          onPress: handleEditProfile,
        },
        {
          icon: 'lock-closed-outline',
          title: 'Change Password',
          subtitle: 'Update your account password',
          onPress: handleChangePassword,
        },
        {
          icon: 'shield-checkmark-outline',
          title: 'Privacy Settings',
          subtitle: 'Manage your privacy preferences',
          onPress: () => Alert.alert('Privacy', 'Privacy settings coming soon.'),
        },
      ],
    },
    {
      title: 'Preferences',
      items: [
        {
          icon: 'notifications-outline',
          title: 'Notifications',
          subtitle: 'Manage notification preferences',
          hasSwitch: true,
          switchValue: notificationsEnabled,
          onSwitchChange: setNotificationsEnabled,
        },
        {
          icon: 'moon-outline',
          title: 'Dark Mode',
          subtitle: 'Toggle dark theme',
          hasSwitch: true,
          switchValue: darkModeEnabled,
          onSwitchChange: setDarkModeEnabled,
        },
        {
          icon: 'language-outline',
          title: 'Language',
          subtitle: 'English',
          onPress: () => Alert.alert('Language', 'Language settings coming soon.'),
        },
      ],
    },
    {
      title: 'Study Data',
      items: [
        {
          icon: 'download-outline',
          title: 'Export Data',
          subtitle: 'Download your study progress',
          onPress: () => Alert.alert('Export', 'Data export coming soon.'),
        },
        {
          icon: 'sync-outline',
          title: 'Sync Settings',
          subtitle: 'Backup and sync preferences',
          onPress: () => Alert.alert('Sync', 'Sync settings coming soon.'),
        },
      ],
    },
    {
      title: 'Support',
      items: [
        {
          icon: 'help-circle-outline',
          title: 'Help & Support',
          subtitle: 'Get help and contact support',
          onPress: () => Alert.alert('Support', 'Support page coming soon.'),
        },
        {
          icon: 'document-text-outline',
          title: 'Terms of Service',
          subtitle: 'Read our terms and conditions',
          onPress: () => Alert.alert('Terms', 'Terms of service coming soon.'),
        },
        {
          icon: 'shield-outline',
          title: 'Privacy Policy',
          subtitle: 'Read our privacy policy',
          onPress: () => Alert.alert('Privacy Policy', 'Privacy policy coming soon.'),
        },
      ],
    },
  ];

  const renderProfileItem = (item: any, index: number) => (
    <TouchableOpacity
      key={index}
      style={styles.profileItem}
      onPress={item.onPress}
      disabled={item.hasSwitch}
    >
      <View style={styles.itemLeft}>
        <View style={styles.itemIcon}>
          <Ionicons name={item.icon} size={24} color="#0066cc" />
        </View>
        <View style={styles.itemContent}>
          <Text style={styles.itemTitle}>{item.title}</Text>
          <Text style={styles.itemSubtitle}>{item.subtitle}</Text>
        </View>
      </View>
      <View style={styles.itemRight}>
        {item.hasSwitch ? (
          <Switch
            value={item.switchValue}
            onValueChange={item.onSwitchChange}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={item.switchValue ? '#0066cc' : '#f4f3f4'}
          />
        ) : (
          <Ionicons name="chevron-forward" size={20} color="#666" />
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container}>
      {/* Profile Header */}
      <View style={styles.profileHeader}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.first_name?.charAt(0) || 'U'}
              {user?.last_name?.charAt(0) || ''}
            </Text>
          </View>
        </View>
        <Text style={styles.userName}>
          {user?.first_name} {user?.last_name}
        </Text>
        <Text style={styles.userEmail}>{user?.email}</Text>
        {user?.student_profile && (
          <View style={styles.studentInfo}>
            <Text style={styles.studentId}>
              ID: {user.student_profile.student_id}
            </Text>
            <Text style={styles.semester}>
              Semester {user.student_profile.current_semester}
            </Text>
          </View>
        )}
      </View>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Ionicons name="trophy" size={24} color="#ffc107" />
          <Text style={styles.statNumber}>85%</Text>
          <Text style={styles.statLabel}>Avg Score</Text>
        </View>
        <View style={styles.statCard}>
          <Ionicons name="flame" size={24} color="#dc3545" />
          <Text style={styles.statNumber}>7</Text>
          <Text style={styles.statLabel}>Day Streak</Text>
        </View>
        <View style={styles.statCard}>
          <Ionicons name="checkmark-circle" size={24} color="#28a745" />
          <Text style={styles.statNumber}>142</Text>
          <Text style={styles.statLabel}>Completed</Text>
        </View>
      </View>

      {/* Profile Sections */}
      {profileSections.map((section, sectionIndex) => (
        <View key={sectionIndex} style={styles.section}>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          <View style={styles.sectionContent}>
            {section.items.map((item, itemIndex) =>
              renderProfileItem(item, itemIndex)
            )}
          </View>
        </View>
      ))}

      {/* Logout Button */}
      <View style={styles.logoutContainer}>
        <CustomButton
          title="Logout"
          onPress={handleLogout}
          variant="danger"
          size="large"
          style={styles.logoutButton}
        />
      </View>

      {/* App Version */}
      <View style={styles.versionContainer}>
        <Text style={styles.versionText}>Examify v1.0.0</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  profileHeader: {
    backgroundColor: '#fff',
    paddingVertical: 32,
    paddingHorizontal: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#0066cc',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 16,
    color: '#666',
    marginBottom: 12,
  },
  studentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  studentId: {
    fontSize: 14,
    color: '#666',
    marginRight: 16,
  },
  semester: {
    fontSize: 14,
    color: '#666',
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 20,
    backgroundColor: '#fff',
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  statCard: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    paddingHorizontal: 24,
    marginBottom: 12,
  },
  sectionContent: {
    backgroundColor: '#fff',
  },
  profileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  itemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  itemIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  itemContent: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  itemSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  itemRight: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoutContainer: {
    paddingHorizontal: 24,
    paddingVertical: 20,
  },
  logoutButton: {
    marginBottom: 16,
  },
  versionContainer: {
    alignItems: 'center',
    paddingBottom: 32,
  },
  versionText: {
    fontSize: 12,
    color: '#999',
  },
});

export default ProfileScreen; 