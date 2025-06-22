import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import CustomButton from '../../components/common/CustomButton';

interface MockExam {
  id: string;
  title: string;
  description: string;
  duration: number;
  totalQuestions: number;
  difficulty: string;
  subjects: string[];
  scheduledDate?: string;
  status: 'available' | 'completed' | 'scheduled';
  score?: number;
}

const MockExamsScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'available' | 'scheduled' | 'history'>('available');

  const mockExams: MockExam[] = [
    {
      id: '1',
      title: 'Computer Science Fundamentals',
      description: 'Comprehensive exam covering data structures, algorithms, and programming concepts',
      duration: 120,
      totalQuestions: 50,
      difficulty: 'intermediate',
      subjects: ['Data Structures', 'Algorithms', 'Programming'],
      status: 'available',
    },
    {
      id: '2',
      title: 'Advanced Programming Assessment',
      description: 'In-depth examination of advanced programming paradigms and system design',
      duration: 180,
      totalQuestions: 75,
      difficulty: 'hard',
      subjects: ['System Design', 'Databases', 'Networks'],
      status: 'scheduled',
      scheduledDate: '2025-06-25T10:00:00Z',
    },
    {
      id: '3',
      title: 'Quick Concepts Review',
      description: 'Fast-paced review of key computer science concepts',
      duration: 60,
      totalQuestions: 30,
      difficulty: 'easy',
      subjects: ['Basics', 'Theory'],
      status: 'completed',
      score: 87,
    },
  ];

  const getFilteredExams = () => {
    return mockExams.filter(exam => {
      if (activeTab === 'available') return exam.status === 'available';
      if (activeTab === 'scheduled') return exam.status === 'scheduled';
      if (activeTab === 'history') return exam.status === 'completed';
      return true;
    });
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '#28a745';
      case 'intermediate': return '#ffc107';
      case 'hard': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const renderExam = ({ item }: { item: MockExam }) => (
    <View style={styles.examCard}>
      <View style={styles.examHeader}>
        <View style={styles.examMeta}>
          <View style={[
            styles.difficultyTag,
            { backgroundColor: getDifficultyColor(item.difficulty) }
          ]}>
            <Text style={styles.difficultyText}>
              {item.difficulty.toUpperCase()}
            </Text>
          </View>
          {item.status === 'scheduled' && (
            <View style={styles.statusTag}>
              <Ionicons name="calendar" size={12} color="#0066cc" />
              <Text style={styles.statusText}>Scheduled</Text>
            </View>
          )}
          {item.status === 'completed' && (
            <View style={[styles.statusTag, { backgroundColor: '#d4edda' }]}>
              <Ionicons name="checkmark-circle" size={12} color="#28a745" />
              <Text style={[styles.statusText, { color: '#28a745' }]}>Completed</Text>
            </View>
          )}
        </View>
        {item.score && (
          <View style={styles.scoreContainer}>
            <Text style={styles.scoreText}>{item.score}%</Text>
          </View>
        )}
      </View>

      <Text style={styles.examTitle}>{item.title}</Text>
      <Text style={styles.examDescription}>{item.description}</Text>

      <View style={styles.examStats}>
        <View style={styles.statItem}>
          <Ionicons name="time-outline" size={16} color="#666" />
          <Text style={styles.statText}>{item.duration} min</Text>
        </View>
        <View style={styles.statItem}>
          <Ionicons name="help-circle-outline" size={16} color="#666" />
          <Text style={styles.statText}>{item.totalQuestions} questions</Text>
        </View>
      </View>

      <View style={styles.subjectsContainer}>
        {item.subjects.slice(0, 3).map((subject, index) => (
          <View key={index} style={styles.subjectTag}>
            <Text style={styles.subjectText}>{subject}</Text>
          </View>
        ))}
        {item.subjects.length > 3 && (
          <Text style={styles.moreSubjects}>+{item.subjects.length - 3} more</Text>
        )}
      </View>

      {item.scheduledDate && (
        <View style={styles.scheduledInfo}>
          <Ionicons name="calendar-outline" size={16} color="#0066cc" />
          <Text style={styles.scheduledText}>
            Scheduled for {new Date(item.scheduledDate).toLocaleDateString()} at{' '}
            {new Date(item.scheduledDate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </View>
      )}

      <View style={styles.examFooter}>
        {item.status === 'available' && (
          <View style={styles.actionButtons}>
            <CustomButton
              title="Schedule"
              onPress={() => {}}
              variant="outline"
              size="small"
              style={styles.actionButton}
            />
            <CustomButton
              title="Start Now"
              onPress={() => {}}
              variant="primary"
              size="small"
            />
          </View>
        )}
        {item.status === 'scheduled' && (
          <CustomButton
            title="View Details"
            onPress={() => {}}
            variant="outline"
            size="small"
          />
        )}
        {item.status === 'completed' && (
          <View style={styles.actionButtons}>
            <CustomButton
              title="View Report"
              onPress={() => {}}
              variant="outline"
              size="small"
              style={styles.actionButton}
            />
            <CustomButton
              title="Retake"
              onPress={() => {}}
              variant="primary"
              size="small"
            />
          </View>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'available' && styles.activeTab]}
          onPress={() => setActiveTab('available')}
        >
          <Text style={[styles.tabText, activeTab === 'available' && styles.activeTabText]}>
            Available
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'scheduled' && styles.activeTab]}
          onPress={() => setActiveTab('scheduled')}
        >
          <Text style={[styles.tabText, activeTab === 'scheduled' && styles.activeTabText]}>
            Scheduled
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'history' && styles.activeTab]}
          onPress={() => setActiveTab('history')}
        >
          <Text style={[styles.tabText, activeTab === 'history' && styles.activeTabText]}>
            History
          </Text>
        </TouchableOpacity>
      </View>

      {/* Header Info */}
      <View style={styles.headerInfo}>
        <View style={styles.infoCard}>
          <Ionicons name="trophy" size={24} color="#ffc107" />
          <Text style={styles.infoText}>Best Score: 94%</Text>
        </View>
        <View style={styles.infoCard}>
          <Ionicons name="checkmark-circle" size={24} color="#28a745" />
          <Text style={styles.infoText}>Completed: 12</Text>
        </View>
        <View style={styles.infoCard}>
          <Ionicons name="time" size={24} color="#0066cc" />
          <Text style={styles.infoText}>Avg Time: 98 min</Text>
        </View>
      </View>

      {/* Exams List */}
      <FlatList
        data={getFilteredExams()}
        renderItem={renderExam}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="school-outline" size={64} color="#ccc" />
            <Text style={styles.emptyTitle}>
              {activeTab === 'available' && 'No Available Exams'}
              {activeTab === 'scheduled' && 'No Scheduled Exams'}
              {activeTab === 'history' && 'No Exam History'}
            </Text>
            <Text style={styles.emptySubtitle}>
              {activeTab === 'available' && 'Check back later for new mock exams'}
              {activeTab === 'scheduled' && 'Schedule an exam to see it here'}
              {activeTab === 'history' && 'Complete an exam to view your history'}
            </Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#0066cc',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#0066cc',
    fontWeight: '600',
  },
  headerInfo: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  infoCard: {
    alignItems: 'center',
  },
  infoText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontWeight: '500',
  },
  listContainer: {
    padding: 16,
  },
  examCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  examHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  examMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  difficultyTag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#fff',
  },
  statusTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#e3f2fd',
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    color: '#0066cc',
    marginLeft: 4,
    fontWeight: '500',
  },
  scoreContainer: {
    backgroundColor: '#28a745',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#fff',
  },
  examTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  examDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    lineHeight: 20,
  },
  examStats: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  subjectsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  subjectTag: {
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 4,
  },
  subjectText: {
    fontSize: 10,
    color: '#666',
  },
  moreSubjects: {
    fontSize: 10,
    color: '#0066cc',
    fontStyle: 'italic',
    alignSelf: 'center',
  },
  scheduledInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e3f2fd',
    padding: 8,
    borderRadius: 8,
    marginBottom: 12,
  },
  scheduledText: {
    fontSize: 12,
    color: '#0066cc',
    marginLeft: 8,
    fontWeight: '500',
  },
  examFooter: {
    alignItems: 'flex-end',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    paddingHorizontal: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});

export default MockExamsScreen; 