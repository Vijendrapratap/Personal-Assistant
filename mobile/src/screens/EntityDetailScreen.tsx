/**
 * EntityDetailScreen - Shows detailed information about a person or company entity
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { useTheme } from '../theme';
import { knowledgeApi, Entity } from '../api/services';

type RouteParams = {
  EntityDetail: {
    entityId: string;
    entityType: 'person' | 'company' | 'topic';
    name: string;
  };
};

interface PropertyRowProps {
  label: string;
  value: string;
  theme: any;
}

const PropertyRow: React.FC<PropertyRowProps> = ({ label, value, theme }) => (
  <View style={styles.propertyRow}>
    <Text style={[styles.propertyLabel, { color: theme.colors.textSecondary }]}>
      {label}
    </Text>
    <Text style={[styles.propertyValue, { color: theme.colors.textPrimary }]}>
      {value}
    </Text>
  </View>
);

interface RelationshipItemProps {
  relationship: { type: string; target_id: string; target_name: string };
  onPress: () => void;
  theme: any;
}

const RelationshipItem: React.FC<RelationshipItemProps> = ({
  relationship,
  onPress,
  theme,
}) => {
  const formatRelationType = (type: string) => {
    return type
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <TouchableOpacity
      style={[styles.relationshipItem, { backgroundColor: theme.colors.bgSurface }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.relationshipContent}>
        <Text style={[styles.relationshipType, { color: theme.colors.textTertiary }]}>
          {formatRelationType(relationship.type)}
        </Text>
        <Text style={[styles.relationshipName, { color: theme.colors.textPrimary }]}>
          {relationship.target_name}
        </Text>
      </View>
      <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
    </TouchableOpacity>
  );
};

export default function EntityDetailScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation<any>();
  const route = useRoute<RouteProp<RouteParams, 'EntityDetail'>>();

  const { entityId, entityType, name } = route.params;

  const [entity, setEntity] = useState<Entity | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEntity = useCallback(async () => {
    try {
      setError(null);
      const data = await knowledgeApi.getEntity(entityId);
      setEntity(data);
    } catch (err) {
      console.error('Failed to fetch entity:', err);
      setError('Failed to load details');
      // Mock data for demo
      const mockEntity: Entity = {
        entity_id: entityId,
        entity_type: entityType,
        name: name,
        properties:
          entityType === 'person'
            ? {
                role: 'Engineering Manager',
                company: 'TechCorp',
                email: 'sarah@techcorp.com',
                notes: 'Met at conference in 2024. Expert in distributed systems.',
              }
            : {
                industry: 'Technology',
                size: '500+ employees',
                website: 'techcorp.com',
                notes: 'Enterprise software company. Main client for Project Alpha.',
              },
        relationships:
          entityType === 'person'
            ? [
                { type: 'works_at', target_id: 'c1', target_name: 'TechCorp' },
                { type: 'knows', target_id: '3', target_name: 'Elena Rodriguez' },
              ]
            : [
                { type: 'employs', target_id: '1', target_name: 'Sarah Chen' },
                { type: 'employs', target_id: '4', target_name: 'David Kim' },
              ],
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
      };
      setEntity(mockEntity);
    }
  }, [entityId, entityType, name]);

  useEffect(() => {
    fetchEntity().finally(() => setLoading(false));
  }, [fetchEntity]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchEntity();
    setRefreshing(false);
  };

  const handleRelationshipPress = (rel: { type: string; target_id: string; target_name: string }) => {
    // Determine entity type from relationship
    const isCompany = rel.type.includes('works_at') || rel.type.includes('employs');
    const targetType = isCompany && rel.type.includes('works_at') ? 'company' : 'person';

    navigation.push('EntityDetail', {
      entityId: rel.target_id,
      entityType: targetType,
      name: rel.target_name,
    });
  };

  const getIcon = () => {
    if (entityType === 'person') return '👤';
    if (entityType === 'company') return '🏢';
    return '📝';
  };

  const getInitials = (name: string) => {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Properties to display (filter out internal ones)
  const displayProperties = entity?.properties
    ? Object.entries(entity.properties).filter(
        ([key]) => !['entity_id', 'user_id', 'created_at', 'updated_at'].includes(key)
      )
    : [];

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
            Loading...
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
        <Text
          style={[styles.headerTitle, { color: theme.colors.textPrimary }]}
          numberOfLines={1}
        >
          {entityType === 'person' ? 'Person' : entityType === 'company' ? 'Company' : 'Entity'}
        </Text>
        <View style={styles.headerRight} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={theme.colors.primary}
          />
        }
      >
        {/* Entity Header */}
        <View style={[styles.entityHeader, { backgroundColor: theme.colors.bgElevated }]}>
          {entityType === 'person' ? (
            <View style={[styles.avatar, { backgroundColor: theme.colors.primarySoft }]}>
              <Text style={[styles.avatarText, { color: theme.colors.primary }]}>
                {getInitials(entity?.name || name)}
              </Text>
            </View>
          ) : (
            <View style={[styles.iconBox, { backgroundColor: theme.colors.bgSurface }]}>
              <Text style={styles.entityIcon}>{getIcon()}</Text>
            </View>
          )}
          <Text style={[styles.entityName, { color: theme.colors.textPrimary }]}>
            {entity?.name || name}
          </Text>
          {entity?.properties?.role && (
            <Text style={[styles.entitySubtitle, { color: theme.colors.textSecondary }]}>
              {entity.properties.role}
              {entity.properties.company ? ` at ${entity.properties.company}` : ''}
            </Text>
          )}
          {entity?.properties?.industry && (
            <Text style={[styles.entitySubtitle, { color: theme.colors.textSecondary }]}>
              {entity.properties.industry}
              {entity.properties.size ? ` • ${entity.properties.size}` : ''}
            </Text>
          )}
        </View>

        {/* Quick Facts */}
        {displayProperties.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
              DETAILS
            </Text>
            <View style={[styles.propertiesCard, { backgroundColor: theme.colors.bgElevated }]}>
              {displayProperties.map(([key, value], index) => (
                <React.Fragment key={key}>
                  {index > 0 && (
                    <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
                  )}
                  <PropertyRow
                    label={key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    value={String(value)}
                    theme={theme}
                  />
                </React.Fragment>
              ))}
            </View>
          </View>
        )}

        {/* Relationships */}
        {entity?.relationships && entity.relationships.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
              CONNECTIONS
            </Text>
            <View style={styles.relationshipsList}>
              {entity.relationships.map((rel, index) => (
                <RelationshipItem
                  key={`${rel.target_id}-${index}`}
                  relationship={rel}
                  onPress={() => handleRelationshipPress(rel)}
                  theme={theme}
                />
              ))}
            </View>
          </View>
        )}

        {/* Metadata */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            ABOUT THIS ENTRY
          </Text>
          <View style={[styles.metadataCard, { backgroundColor: theme.colors.bgElevated }]}>
            {entity?.created_at && (
              <>
                <PropertyRow
                  label="First mentioned"
                  value={formatDate(entity.created_at)}
                  theme={theme}
                />
                <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
              </>
            )}
            {entity?.updated_at && (
              <PropertyRow
                label="Last updated"
                value={formatDate(entity.updated_at)}
                theme={theme}
              />
            )}
          </View>
        </View>

        {/* Alfred's Note */}
        <View style={[styles.alfredNote, { backgroundColor: theme.colors.primaryGlow }]}>
          <Text style={styles.alfredNoteIcon}>🤖</Text>
          <Text style={[styles.alfredNoteText, { color: theme.colors.textSecondary }]}>
            Alfred learns about people and companies from your conversations.
            Mention someone in a chat to add more details.
          </Text>
        </View>
      </ScrollView>
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
  headerTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '600',
    textAlign: 'center',
  },
  headerRight: {
    width: 40,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  entityHeader: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 24,
    marginHorizontal: 16,
    marginBottom: 24,
    borderRadius: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 28,
    fontWeight: '600',
  },
  iconBox: {
    width: 80,
    height: 80,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  entityIcon: {
    fontSize: 40,
  },
  entityName: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
    textAlign: 'center',
  },
  entitySubtitle: {
    fontSize: 15,
    textAlign: 'center',
  },
  section: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
    marginLeft: 4,
  },
  propertiesCard: {
    borderRadius: 12,
    padding: 16,
  },
  propertyRow: {
    paddingVertical: 8,
  },
  propertyLabel: {
    fontSize: 13,
    marginBottom: 4,
  },
  propertyValue: {
    fontSize: 15,
    fontWeight: '500',
  },
  divider: {
    height: 1,
    marginVertical: 4,
  },
  relationshipsList: {
    gap: 8,
  },
  relationshipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  relationshipContent: {
    flex: 1,
  },
  relationshipType: {
    fontSize: 12,
    marginBottom: 2,
  },
  relationshipName: {
    fontSize: 15,
    fontWeight: '600',
  },
  chevron: {
    fontSize: 24,
    fontWeight: '300',
    marginLeft: 8,
  },
  metadataCard: {
    borderRadius: 12,
    padding: 16,
  },
  alfredNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginHorizontal: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
  },
  alfredNoteIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  alfredNoteText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
});
