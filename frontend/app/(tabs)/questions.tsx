import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
  RefreshControl,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import CustomButton from '../../components/common/CustomButton';

interface Question {
  id: string;
  title: string;
  question_text: string;
  question_type: string;
  difficulty_level: string;
  answer_options?: any;
  correct_answer?: string;
  answer_explanation?: string;
  created_at: string;
}

const QuestionsScreen: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [selectedType, setSelectedType] = useState('all');

  const difficulties = [
    { label: 'All', value: 'all' },
    { label: 'Easy', value: 'easy' },
    { label: 'Intermediate', value: 'intermediate' },
    { label: 'Hard', value: 'hard' },
  ];

  const questionTypes = [
    { label: 'All', value: 'all' },
    { label: 'Multiple Choice', value: 'multiple_choice' },
    { label: 'Short Answer', value: 'short_answer' },
    { label: 'Essay', value: 'essay' },
  ];

  const loadQuestions = async () => {
    setIsLoading(true);
    try {
      // TODO: Implement API call
      // const response = await questionService.getQuestions({
      //   search: searchQuery,
      //   difficulty: selectedDifficulty !== 'all' ? selectedDifficulty : undefined,
      //   type: selectedType !== 'all' ? selectedType : undefined,
      // });

      // Mock data for now
      setTimeout(() => {
        const mockQuestions: Question[] = [
          {
            id: '1',
            title: 'Array Traversal',
            question_text: 'What is the time complexity of traversing an array of n elements?',
            question_type: 'multiple_choice',
            difficulty_level: 'easy',
            answer_options: {
              A: 'O(1)',
              B: 'O(n)',
              C: 'O(n²)',
              D: 'O(log n)',
            },
            correct_answer: 'B',
            answer_explanation: 'Array traversal requires visiting each element once.',
            created_at: '2025-06-22T10:00:00Z',
          },
          {
            id: '2',
            title: 'Binary Search Implementation',
            question_text: 'Explain how binary search works and provide its time complexity.',
            question_type: 'short_answer',
            difficulty_level: 'intermediate',
            created_at: '2025-06-22T09:00:00Z',
          },
          {
            id: '3',
            title: 'Advanced Algorithm Design',
            question_text: 'Design an algorithm to find the longest palindromic subsequence in a string.',
            question_type: 'essay',
            difficulty_level: 'hard',
            created_at: '2025-06-22T08:00:00Z',
          },
        ];

        // Filter questions based on search and filters
        let filteredQuestions = mockQuestions;
        
        if (searchQuery) {
          filteredQuestions = filteredQuestions.filter(q =>
            q.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            q.question_text.toLowerCase().includes(searchQuery.toLowerCase())
          );
        }
        
        if (selectedDifficulty !== 'all') {
          filteredQuestions = filteredQuestions.filter(q =>
            q.difficulty_level === selectedDifficulty
          );
        }
        
        if (selectedType !== 'all') {
          filteredQuestions = filteredQuestions.filter(q =>
            q.question_type === selectedType
          );
        }

        setQuestions(filteredQuestions);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load questions:', error);
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadQuestions();
    setRefreshing(false);
  };

  useEffect(() => {
    loadQuestions();
  }, [searchQuery, selectedDifficulty, selectedType]);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '#28a745';
      case 'intermediate': return '#ffc107';
      case 'hard': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'multiple_choice': return 'list';
      case 'short_answer': return 'text';
      case 'essay': return 'document-text';
      default: return 'help-circle';
    }
  };

  const renderQuestion = ({ item }: { item: Question }) => (
    <TouchableOpacity style={styles.questionCard}>
      <View style={styles.questionHeader}>
        <View style={styles.questionMeta}>
          <View style={[
            styles.difficultyTag,
            { backgroundColor: getDifficultyColor(item.difficulty_level) }
          ]}>
            <Text style={styles.difficultyText}>
              {item.difficulty_level.toUpperCase()}
            </Text>
          </View>
          <View style={styles.typeTag}>
            <Ionicons 
              name={getTypeIcon(item.question_type) as any} 
              size={14} 
              color="#666" 
            />
            <Text style={styles.typeText}>
              {item.question_type.replace('_', ' ')}
            </Text>
          </View>
        </View>
        <TouchableOpacity style={styles.favoriteButton}>
          <Ionicons name="heart-outline" size={20} color="#666" />
        </TouchableOpacity>
      </View>

      <Text style={styles.questionTitle}>{item.title}</Text>
      <Text style={styles.questionText} numberOfLines={3}>
        {item.question_text}
      </Text>

      {item.answer_options && (
        <View style={styles.optionsPreview}>
          <Text style={styles.optionsLabel}>Options:</Text>
          {Object.entries(item.answer_options).slice(0, 2).map(([key, value]) => (
            <Text key={key} style={styles.optionText}>
              {key}. {value as string}
            </Text>
          ))}
          {Object.keys(item.answer_options).length > 2 && (
            <Text style={styles.moreOptions}>
              +{Object.keys(item.answer_options).length - 2} more...
            </Text>
          )}
        </View>
      )}

      <View style={styles.questionFooter}>
        <Text style={styles.dateText}>
          {new Date(item.created_at).toLocaleDateString()}
        </Text>
        <View style={styles.actionButtons}>
          <CustomButton
            title="Practice"
            onPress={() => {}}
            variant="outline"
            size="small"
            style={styles.practiceButton}
          />
          <CustomButton
            title="View"
            onPress={() => {}}
            variant="primary"
            size="small"
          />
        </View>
      </View>
    </TouchableOpacity>
  );

  if (isLoading && questions.length === 0) {
    return <LoadingSpinner message="Loading questions..." />;
  }

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color="#666" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search questions..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#999"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close" size={20} color="#666" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Filters */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
        contentContainerStyle={styles.filtersContent}
      >
        {/* Difficulty Filter */}
        <View style={styles.filterGroup}>
          <Text style={styles.filterLabel}>Difficulty:</Text>
          {difficulties.map((diff) => (
            <TouchableOpacity
              key={diff.value}
              style={[
                styles.filterChip,
                selectedDifficulty === diff.value && styles.filterChipActive
              ]}
              onPress={() => setSelectedDifficulty(diff.value)}
            >
              <Text style={[
                styles.filterChipText,
                selectedDifficulty === diff.value && styles.filterChipTextActive
              ]}>
                {diff.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Type Filter */}
        <View style={styles.filterGroup}>
          <Text style={styles.filterLabel}>Type:</Text>
          {questionTypes.map((type) => (
            <TouchableOpacity
              key={type.value}
              style={[
                styles.filterChip,
                selectedType === type.value && styles.filterChipActive
              ]}
              onPress={() => setSelectedType(type.value)}
            >
              <Text style={[
                styles.filterChipText,
                selectedType === type.value && styles.filterChipTextActive
              ]}>
                {type.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Questions List */}
      <FlatList
        data={questions}
        renderItem={renderQuestion}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={64} color="#ccc" />
            <Text style={styles.emptyTitle}>No Questions Found</Text>
            <Text style={styles.emptySubtitle}>
              Try adjusting your search criteria or filters
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
  searchContainer: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#333',
  },
  filtersContainer: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e1e1',
  },
  filtersContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  filterGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 20,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginRight: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f8f9fa',
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: '#0066cc',
  },
  filterChipText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: '#fff',
  },
  listContainer: {
    padding: 16,
  },
  questionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  questionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  questionMeta: {
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
  typeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
  },
  typeText: {
    fontSize: 10,
    color: '#666',
    marginLeft: 4,
    textTransform: 'capitalize',
  },
  favoriteButton: {
    padding: 4,
  },
  questionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  questionText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  optionsPreview: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  optionsLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  optionText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  moreOptions: {
    fontSize: 12,
    color: '#0066cc',
    fontStyle: 'italic',
  },
  questionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 12,
    color: '#999',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  practiceButton: {
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

export default QuestionsScreen; 