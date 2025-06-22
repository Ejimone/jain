import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import CustomButton from '../../components/common/CustomButton';

interface Quiz {
  id: string;
  title: string;
  description: string;
  quiz_type: string;
  total_questions: number;
  time_limit: number;
  difficulty_range: { min: number; max: number };
  topics: string[];
  ai_generated: boolean;
  created_at: string;
}

const QuizScreen: React.FC = () => {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'available' | 'create'>('available');

  const loadQuizzes = async () => {
    setIsLoading(true);
    try {
      // TODO: Implement API call
      // const response = await quizService.getQuizzes();

      // Mock data for now
      setTimeout(() => {
        const mockQuizzes: Quiz[] = [
          {
            id: '1',
            title: 'Data Structures Quick Quiz',
            description: 'Test your knowledge of basic data structures',
            quiz_type: 'practice',
            total_questions: 10,
            time_limit: 15,
            difficulty_range: { min: 0.3, max: 0.7 },
            topics: ['arrays', 'linked lists', 'stacks'],
            ai_generated: true,
            created_at: '2025-06-22T10:00:00Z',
          },
          {
            id: '2',
            title: 'Algorithm Complexity Assessment',
            description: 'Advanced quiz on time and space complexity',
            quiz_type: 'assessment',
            total_questions: 20,
            time_limit: 45,
            difficulty_range: { min: 0.6, max: 0.9 },
            topics: ['algorithms', 'complexity', 'optimization'],
            ai_generated: false,
            created_at: '2025-06-22T09:00:00Z',
          },
        ];

        setQuizzes(mockQuizzes);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load quizzes:', error);
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadQuizzes();
    setRefreshing(false);
  };

  useEffect(() => {
    loadQuizzes();
  }, []);

  const renderQuiz = ({ item }: { item: Quiz }) => (
    <View style={styles.quizCard}>
      <View style={styles.quizHeader}>
        <View style={styles.quizMeta}>
          <View style={[
            styles.typeTag,
            { backgroundColor: item.quiz_type === 'practice' ? '#28a745' : '#0066cc' }
          ]}>
            <Text style={styles.typeText}>
              {item.quiz_type.toUpperCase()}
            </Text>
          </View>
          {item.ai_generated && (
            <View style={styles.aiTag}>
              <Ionicons name="sparkles" size={12} color="#ffc107" />
              <Text style={styles.aiText}>AI Generated</Text>
            </View>
          )}
        </View>
        <TouchableOpacity style={styles.favoriteButton}>
          <Ionicons name="bookmark-outline" size={20} color="#666" />
        </TouchableOpacity>
      </View>

      <Text style={styles.quizTitle}>{item.title}</Text>
      <Text style={styles.quizDescription}>{item.description}</Text>

      <View style={styles.quizStats}>
        <View style={styles.statItem}>
          <Ionicons name="help-circle-outline" size={16} color="#666" />
          <Text style={styles.statText}>{item.total_questions} questions</Text>
        </View>
        <View style={styles.statItem}>
          <Ionicons name="time-outline" size={16} color="#666" />
          <Text style={styles.statText}>{item.time_limit} min</Text>
        </View>
        <View style={styles.statItem}>
          <Ionicons name="trending-up-outline" size={16} color="#666" />
          <Text style={styles.statText}>
            {Math.round(item.difficulty_range.min * 100)}-{Math.round(item.difficulty_range.max * 100)}%
          </Text>
        </View>
      </View>

      <View style={styles.topicsContainer}>
        {item.topics.slice(0, 3).map((topic, index) => (
          <View key={index} style={styles.topicTag}>
            <Text style={styles.topicText}>{topic}</Text>
          </View>
        ))}
        {item.topics.length > 3 && (
          <Text style={styles.moreTopics}>+{item.topics.length - 3} more</Text>
        )}
      </View>

      <View style={styles.quizFooter}>
        <Text style={styles.dateText}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
        <CustomButton
          title="Start Quiz"
          onPress={() => {}}
          variant="primary"
          size="small"
        />
      </View>
    </View>
  );

  const renderCreateQuizForm = () => (
    <ScrollView style={styles.createForm}>
      <Text style={styles.createTitle}>Create Custom Quiz</Text>
      <Text style={styles.createSubtitle}>
        Generate a personalized quiz based on your preferences
      </Text>

      <View style={styles.formSection}>
        <Text style={styles.sectionTitle}>Quiz Type</Text>
        <View style={styles.optionGrid}>
          <TouchableOpacity style={styles.optionCard}>
            <Ionicons name="flash" size={32} color="#0066cc" />
            <Text style={styles.optionTitle}>Quick Practice</Text>
            <Text style={styles.optionDescription}>5-10 questions, 15 minutes</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.optionCard}>
            <Ionicons name="school" size={32} color="#28a745" />
            <Text style={styles.optionTitle}>Assessment</Text>
            <Text style={styles.optionDescription}>15-25 questions, 45 minutes</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.formSection}>
        <Text style={styles.sectionTitle}>Difficulty Level</Text>
        <View style={styles.difficultySlider}>
          <TouchableOpacity style={[styles.difficultyOption, styles.active]}>
            <Text style={[styles.difficultyText, styles.activeText]}>Easy</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.difficultyOption}>
            <Text style={styles.difficultyText}>Medium</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.difficultyOption}>
            <Text style={styles.difficultyText}>Hard</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.difficultyOption}>
            <Text style={styles.difficultyText}>Mixed</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.formSection}>
        <Text style={styles.sectionTitle}>Topics</Text>
        <View style={styles.topicsList}>
          {['Data Structures', 'Algorithms', 'System Design', 'Databases', 'Networks'].map((topic) => (
            <TouchableOpacity key={topic} style={styles.topicOption}>
              <Ionicons name="checkbox-outline" size={20} color="#666" />
              <Text style={styles.topicOptionText}>{topic}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <CustomButton
        title="Generate Quiz with AI"
        onPress={() => {}}
        variant="primary"
        size="large"
        style={styles.generateButton}
      />
    </ScrollView>
  );

  if (isLoading && quizzes.length === 0) {
    return <LoadingSpinner message="Loading quizzes..." />;
  }

  return (
    <View style={styles.container}>
      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'available' && styles.activeTab]}
          onPress={() => setActiveTab('available')}
        >
          <Text style={[styles.tabText, activeTab === 'available' && styles.activeTabText]}>
            Available Quizzes
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'create' && styles.activeTab]}
          onPress={() => setActiveTab('create')}
        >
          <Text style={[styles.tabText, activeTab === 'create' && styles.activeTabText]}>
            Create Quiz
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {activeTab === 'available' ? (
        <FlatList
          data={quizzes}
          renderItem={renderQuiz}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="document-text-outline" size={64} color="#ccc" />
              <Text style={styles.emptyTitle}>No Quizzes Available</Text>
              <Text style={styles.emptySubtitle}>
                Create your first quiz or check back later
              </Text>
            </View>
          }
        />
      ) : (
        renderCreateQuizForm()
      )}
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
  listContainer: {
    padding: 16,
  },
  quizCard: {
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
  quizHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  quizMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typeTag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  typeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#fff',
  },
  aiTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    backgroundColor: '#fff3cd',
    borderRadius: 8,
  },
  aiText: {
    fontSize: 10,
    color: '#856404',
    marginLeft: 4,
  },
  favoriteButton: {
    padding: 4,
  },
  quizTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  quizDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  quizStats: {
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
  topicsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  topicTag: {
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 4,
  },
  topicText: {
    fontSize: 10,
    color: '#666',
  },
  moreTopics: {
    fontSize: 10,
    color: '#0066cc',
    fontStyle: 'italic',
  },
  quizFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 12,
    color: '#999',
  },
  createForm: {
    flex: 1,
    padding: 16,
  },
  createTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  createSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
  },
  formSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  optionGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  optionCard: {
    flex: 0.48,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  optionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginTop: 8,
    marginBottom: 4,
  },
  optionDescription: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  difficultySlider: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 4,
  },
  difficultyOption: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  active: {
    backgroundColor: '#0066cc',
  },
  difficultyText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeText: {
    color: '#fff',
  },
  topicsList: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
  },
  topicOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  topicOptionText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
  },
  generateButton: {
    marginTop: 16,
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

export default QuizScreen; 