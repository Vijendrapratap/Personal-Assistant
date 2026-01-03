/**
 * PeopleScreen - Browse and manage people entities in Alfred's knowledge graph
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../theme';
import { knowledgeApi, Entity } from '../api/services';

interface PersonItemProps {
  person: Entity;
  onPress: () => void;
  theme: any;
}

const PersonItem: React.FC<PersonItemProps> = ({ person, onPress, theme }) => {
  const properties = person.properties || {};
  const role = properties.role || properties.title || '';
  const company = properties.company || properties.organization || '';
  const relationshipCount = person.relationships?.length || 0;

  // Get initials for avatar
  const getInitials = (name: string) => {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <TouchableOpacity
      style={[styles.personItem, { backgroundColor: theme.colors.bgElevated }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.avatar, { backgroundColor: theme.colors.primarySoft }]}>
        <Text style={[styles.avatarText, { color: theme.colors.primary }]}>
          {getInitials(person.name)}
        </Text>
      </View>

      <View style={styles.personInfo}>
        <Text style={[styles.personName, { color: theme.colors.textPrimary }]}>
          {person.name}
        </Text>
        {(role || company) && (
          <Text style={[styles.personRole, { color: theme.colors.textSecondary }]}>
            {role}{role && company ? ' at ' : ''}{company}
          </Text>
        )}
        {relationshipCount > 0 && (
          <Text style={[styles.personMeta, { color: theme.colors.textTertiary }]}>
            {relationshipCount} connection{relationshipCount !== 1 ? 's' : ''}
          </Text>
        )}
      </View>

      <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
    </TouchableOpacity>
  );
};

export default function PeopleScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation<any>();

  const [people, setPeople] = useState<Entity[]>([]);
  const [filteredPeople, setFilteredPeople] = useState<Entity[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPeople = useCallback(async () => {
    try {
      setError(null);
      const response = await knowledgeApi.getPeople(100);
      setPeople(response.entities || []);
      setFilteredPeople(response.entities || []);
    } catch (err) {
      console.error('Failed to fetch people:', err);
      setError('Failed to load people');
      // Use mock data for demo
      const mockPeople: Entity[] = [
        {
          entity_id: '1',
          entity_type: 'person',
          name: 'Sarah Chen',
          properties: { role: 'Engineering Manager', company: 'TechCorp' },
          relationships: [{ type: 'works_at', target_id: 'c1', target_name: 'TechCorp' }],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: '2',
          entity_type: 'person',
          name: 'Marcus Johnson',
          properties: { role: 'Product Designer', company: 'DesignStudio' },
          relationships: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: '3',
          entity_type: 'person',
          name: 'Elena Rodriguez',
          properties: { role: 'CEO', company: 'StartupX' },
          relationships: [
            { type: 'leads', target_id: 'c2', target_name: 'StartupX' },
            { type: 'knows', target_id: '1', target_name: 'Sarah Chen' },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: '4',
          entity_type: 'person',
          name: 'David Kim',
          properties: { role: 'Software Engineer', company: 'TechCorp' },
          relationships: [{ type: 'works_at', target_id: 'c1', target_name: 'TechCorp' }],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: '5',
          entity_type: 'person',
          name: 'Lisa Wang',
          properties: { role: 'Investor', company: 'VentureCapital' },
          relationships: [
            { type: 'invested_in', target_id: 'c2', target_name: 'StartupX' },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];
      setPeople(mockPeople);
      setFilteredPeople(mockPeople);
    }
  }, []);

  useEffect(() => {
    fetchPeople().finally(() => setLoading(false));
  }, [fetchPeople]);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredPeople(people);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredPeople(
        people.filter(
          (p) =>
            p.name.toLowerCase().includes(query) ||
            (p.properties?.role || '').toLowerCase().includes(query) ||
            (p.properties?.company || '').toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, people]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchPeople();
    setRefreshing(false);
  };

  const handlePersonPress = (person: Entity) => {
    navigation.navigate('EntityDetail', {
      entityId: person.entity_id,
      entityType: 'person',
      name: person.name,
    });
  };

  const renderPerson = ({ item }: { item: Entity }) => (
    <PersonItem
      person={item}
      onPress={() => handlePersonPress(item)}
      theme={theme}
    />
  );

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
            Loading people...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={[styles.backIcon, { color: theme.colors.textPrimary }]}>‹</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: theme.colors.textPrimary }]}>People</Text>
        <View style={styles.headerRight}>
          <Text style={[styles.countBadge, { color: theme.colors.textSecondary }]}>
            {people.length}
          </Text>
        </View>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={[styles.searchInput, { backgroundColor: theme.colors.bgElevated }]}>
          <Text style={[styles.searchIcon, { color: theme.colors.textTertiary }]}>🔍</Text>
          <TextInput
            style={[styles.searchText, { color: theme.colors.textPrimary }]}
            placeholder="Search people..."
            placeholderTextColor={theme.colors.textTertiary}
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={[styles.clearIcon, { color: theme.colors.textTertiary }]}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Description */}
      <View style={styles.descriptionContainer}>
        <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
          People Alfred knows about from your conversations and interactions.
        </Text>
      </View>

      {/* People List */}
      <FlatList
        data={filteredPeople}
        keyExtractor={(item) => item.entity_id}
        renderItem={renderPerson}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={theme.colors.primary}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>👤</Text>
            <Text style={[styles.emptyTitle, { color: theme.colors.textPrimary }]}>
              {searchQuery ? 'No matches found' : 'No people yet'}
            </Text>
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
              {searchQuery
                ? 'Try a different search term'
                : 'Alfred will learn about people as you chat'}
            </Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: -8,
  },
  backIcon: {
    fontSize: 32,
    fontWeight: '300',
  },
  title: {
    flex: 1,
    fontSize: 24,
    fontWeight: '700',
    marginLeft: 4,
  },
  headerRight: {
    paddingHorizontal: 8,
  },
  countBadge: {
    fontSize: 15,
    fontWeight: '600',
  },
  searchContainer: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  searchInput: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 44,
  },
  searchIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  searchText: {
    flex: 1,
    fontSize: 15,
  },
  clearIcon: {
    fontSize: 14,
    padding: 4,
  },
  descriptionContainer: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  description: {
    fontSize: 13,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  personItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  avatarText: {
    fontSize: 16,
    fontWeight: '600',
  },
  personInfo: {
    flex: 1,
  },
  personName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  personRole: {
    fontSize: 14,
    marginBottom: 2,
  },
  personMeta: {
    fontSize: 12,
  },
  chevron: {
    fontSize: 24,
    fontWeight: '300',
    marginLeft: 8,
  },
  separator: {
    height: 8,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 32,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
  },
});
