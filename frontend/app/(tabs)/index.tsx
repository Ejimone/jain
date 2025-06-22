import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import CustomButton from '../../components/common/CustomButton';

interface DashboardStats {
  totalQuestionsAttempted: number;
  averageScore: number;
  studyTimeHours: number;
  achievements: string[];
}

const HomeScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // TODO: Implement API call to get dashboard data
      // const response = await dashboardService.getDashboardData();
      
      // Mock data for now
      setTimeout(() => {
        setStats({
          totalQuestionsAttempted: 150,
          averageScore: 85.5,
          studyTimeHours: 45,
          achievements: ['First Quiz', 'Week Streak', 'Top Performer'],
        });
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleLogout = async () => {
    await logout();
  };

  if (isLoading && !stats) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>
            Hello, {user?.first_name || 'Student'}! 👋
          </Text>
          <Text style={styles.subtitle}>Ready to ace your exams?</Text>
        </View>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
          <Ionicons name="log-out-outline" size={24} color="#666" />
        </TouchableOpacity>
      </View>

      {/* Quick Stats */}
      {stats && (
        <View style={styles.statsContainer}>
          <Text style={styles.sectionTitle}>Your Progress</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Ionicons name="help-circle" size={32} color="#0066cc" />
              <Text style={styles.statNumber}>{stats.totalQuestionsAttempted}</Text>
              <Text style={styles.statLabel}>Questions Attempted</Text>
            </View>
            
            <View style={styles.statCard}>
              <Ionicons name="trending-up" size={32} color="#28a745" />
              <Text style={styles.statNumber}>{stats.averageScore}%</Text>
              <Text style={styles.statLabel}>Average Score</Text>
            </View>
            
            <View style={styles.statCard}>
              <Ionicons name="time" size={32} color="#ffc107" />
              <Text style={styles.statNumber}>{stats.studyTimeHours}h</Text>
              <Text style={styles.statLabel}>Study Time</Text>
            </View>
            
            <View style={styles.statCard}>
              <Ionicons name="trophy" size={32} color="#dc3545" />
              <Text style={styles.statNumber}>{stats.achievements.length}</Text>
              <Text style={styles.statLabel}>Achievements</Text>
            </View>
          </View>
        </View>
      )}

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        
        <TouchableOpacity style={styles.actionCard}>
          <View style={styles.actionIcon}>
            <Ionicons name="flash" size={24} color="#0066cc" />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Quick Quiz</Text>
            <Text style={styles.actionSubtitle}>Take a 5-minute practice quiz</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#666" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionCard}>
          <View style={styles.actionIcon}>
            <Ionicons name="camera" size={24} color="#28a745" />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Upload Question</Text>
            <Text style={styles.actionSubtitle}>Get AI help with your questions</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#666" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionCard}>
          <View style={styles.actionIcon}>
            <Ionicons name="book" size={24} color="#ffc107" />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Browse Questions</Text>
            <Text style={styles.actionSubtitle}>Explore past exam questions</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#666" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionCard}>
          <View style={styles.actionIcon}>
            <Ionicons name="school" size={24} color="#dc3545" />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Mock Exam</Text>
            <Text style={styles.actionSubtitle}>Take a full-length practice exam</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#666" />
        </TouchableOpacity>
      </View>

      {/* Recent Activity or Recommendations could go here */}
      <View style={styles.recommendations}>
        <Text style={styles.sectionTitle}>Recommended for You</Text>
        <View style={styles.recommendationCard}>
          <Text style={styles.recommendationTitle}>
            Advanced Data Structures Practice
          </Text>
          <Text style={styles.recommendationSubtitle}>
            Based on your recent performance, we recommend practicing more advanced concepts.
          </Text>
          <CustomButton
            title="Start Practice"
            onPress={() => {}}
            variant="outline"
            size="small"
            style={styles.recommendationButton}
          />
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  logoutButton: {
    padding: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  statsContainer: {
    padding: 20,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
  },
  quickActions: {
    padding: 20,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f8f9fa',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  actionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  recommendations: {
    padding: 20,
  },
  recommendationCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  recommendationSubtitle: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  recommendationButton: {
    alignSelf: 'flex-start',
  },
});

export default HomeScreen; 