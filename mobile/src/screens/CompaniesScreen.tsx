/**
 * CompaniesScreen - Browse and manage company entities in Alfred's knowledge graph
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

interface CompanyItemProps {
  company: Entity;
  onPress: () => void;
  theme: any;
}

const CompanyItem: React.FC<CompanyItemProps> = ({ company, onPress, theme }) => {
  const properties = company.properties || {};
  const industry = properties.industry || properties.sector || '';
  const size = properties.size || properties.employees || '';
  const relationshipCount = company.relationships?.length || 0;

  // Get company icon based on industry
  const getIcon = () => {
    const ind = (industry || '').toLowerCase();
    if (ind.includes('tech') || ind.includes('software')) return '💻';
    if (ind.includes('finance') || ind.includes('bank')) return '🏦';
    if (ind.includes('health') || ind.includes('medical')) return '🏥';
    if (ind.includes('retail') || ind.includes('commerce')) return '🛍️';
    if (ind.includes('media') || ind.includes('entertainment')) return '🎬';
    if (ind.includes('education')) return '🎓';
    if (ind.includes('food') || ind.includes('restaurant')) return '🍽️';
    return '🏢';
  };

  return (
    <TouchableOpacity
      style={[styles.companyItem, { backgroundColor: theme.colors.bgElevated }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.iconContainer, { backgroundColor: theme.colors.bgSurface }]}>
        <Text style={styles.companyIcon}>{getIcon()}</Text>
      </View>

      <View style={styles.companyInfo}>
        <Text style={[styles.companyName, { color: theme.colors.textPrimary }]}>
          {company.name}
        </Text>
        {industry && (
          <Text style={[styles.companyIndustry, { color: theme.colors.textSecondary }]}>
            {industry}
            {size ? ` • ${size}` : ''}
          </Text>
        )}
        {relationshipCount > 0 && (
          <Text style={[styles.companyMeta, { color: theme.colors.textTertiary }]}>
            {relationshipCount} known contact{relationshipCount !== 1 ? 's' : ''}
          </Text>
        )}
      </View>

      <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
    </TouchableOpacity>
  );
};

export default function CompaniesScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation<any>();

  const [companies, setCompanies] = useState<Entity[]>([]);
  const [filteredCompanies, setFilteredCompanies] = useState<Entity[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCompanies = useCallback(async () => {
    try {
      setError(null);
      const response = await knowledgeApi.getCompanies(100);
      setCompanies(response.entities || []);
      setFilteredCompanies(response.entities || []);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
      setError('Failed to load companies');
      // Use mock data for demo
      const mockCompanies: Entity[] = [
        {
          entity_id: 'c1',
          entity_type: 'company',
          name: 'TechCorp',
          properties: { industry: 'Technology', size: '500+ employees' },
          relationships: [
            { type: 'employs', target_id: '1', target_name: 'Sarah Chen' },
            { type: 'employs', target_id: '4', target_name: 'David Kim' },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: 'c2',
          entity_type: 'company',
          name: 'StartupX',
          properties: { industry: 'SaaS', size: '10-50 employees' },
          relationships: [
            { type: 'led_by', target_id: '3', target_name: 'Elena Rodriguez' },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: 'c3',
          entity_type: 'company',
          name: 'DesignStudio',
          properties: { industry: 'Design Agency', size: '10-50 employees' },
          relationships: [
            { type: 'employs', target_id: '2', target_name: 'Marcus Johnson' },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: 'c4',
          entity_type: 'company',
          name: 'VentureCapital',
          properties: { industry: 'Finance', size: '50-100 employees' },
          relationships: [
            { type: 'employs', target_id: '5', target_name: 'Lisa Wang' },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          entity_id: 'c5',
          entity_type: 'company',
          name: 'HealthFirst',
          properties: { industry: 'Healthcare', size: '1000+ employees' },
          relationships: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];
      setCompanies(mockCompanies);
      setFilteredCompanies(mockCompanies);
    }
  }, []);

  useEffect(() => {
    fetchCompanies().finally(() => setLoading(false));
  }, [fetchCompanies]);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredCompanies(companies);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredCompanies(
        companies.filter(
          (c) =>
            c.name.toLowerCase().includes(query) ||
            (c.properties?.industry || '').toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, companies]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchCompanies();
    setRefreshing(false);
  };

  const handleCompanyPress = (company: Entity) => {
    navigation.navigate('EntityDetail', {
      entityId: company.entity_id,
      entityType: 'company',
      name: company.name,
    });
  };

  const renderCompany = ({ item }: { item: Entity }) => (
    <CompanyItem
      company={item}
      onPress={() => handleCompanyPress(item)}
      theme={theme}
    />
  );

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
            Loading companies...
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
        <Text style={[styles.title, { color: theme.colors.textPrimary }]}>Companies</Text>
        <View style={styles.headerRight}>
          <Text style={[styles.countBadge, { color: theme.colors.textSecondary }]}>
            {companies.length}
          </Text>
        </View>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={[styles.searchInput, { backgroundColor: theme.colors.bgElevated }]}>
          <Text style={[styles.searchIcon, { color: theme.colors.textTertiary }]}>🔍</Text>
          <TextInput
            style={[styles.searchText, { color: theme.colors.textPrimary }]}
            placeholder="Search companies..."
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
          Organizations and companies Alfred knows about from your work and conversations.
        </Text>
      </View>

      {/* Companies List */}
      <FlatList
        data={filteredCompanies}
        keyExtractor={(item) => item.entity_id}
        renderItem={renderCompany}
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
            <Text style={styles.emptyIcon}>🏢</Text>
            <Text style={[styles.emptyTitle, { color: theme.colors.textPrimary }]}>
              {searchQuery ? 'No matches found' : 'No companies yet'}
            </Text>
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
              {searchQuery
                ? 'Try a different search term'
                : 'Alfred will learn about companies as you chat'}
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
  companyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  companyIcon: {
    fontSize: 24,
  },
  companyInfo: {
    flex: 1,
  },
  companyName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  companyIndustry: {
    fontSize: 14,
    marginBottom: 2,
  },
  companyMeta: {
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
