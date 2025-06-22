import React, { useEffect } from 'react';
import { router } from 'expo-router';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        console.log('Index: User authenticated, navigating to tabs');
        router.replace('/(tabs)' as any);
      } else {
        console.log('Index: User not authenticated, navigating to login');
        router.replace('/login' as any);
      }
    }
  }, [isAuthenticated, isLoading]);

  return <LoadingSpinner message="Loading..." />;
}
