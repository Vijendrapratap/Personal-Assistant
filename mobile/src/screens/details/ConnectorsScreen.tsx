/**
 * ConnectorsScreen - Tool Connectors & Integrations
 * Connects Alfred to various APIs and services
 */

import React, { useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { Text, Card } from '../../components/common';

interface ConnectorsScreenProps {
  navigation: any;
}

interface ConnectorItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  connected: boolean;
  category: 'apps' | 'custom_api' | 'custom_mcp';
}

const CONNECTORS: ConnectorItem[] = [
  // LLM Providers
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'Leverage GPT models for intelligent text generation.',
    icon: '🤖',
    color: '#10A37F',
    connected: true,
    category: 'apps',
  },
  {
    id: 'google_gemini',
    name: 'Google Gemini',
    description: 'Process multimodal content including text and images.',
    icon: '✨',
    color: '#4285F4',
    connected: false,
    category: 'apps',
  },
  // Productivity Apps
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Read emails and draft replies automatically.',
    icon: '📧',
    color: '#EA4335',
    connected: false,
    category: 'apps',
  },
  {
    id: 'outlook',
    name: 'Outlook',
    description: 'Manage your calendar and enterprise email.',
    icon: '📬',
    color: '#0078D4',
    connected: false,
    category: 'apps',
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Access workspaces, pages, and databases.',
    icon: '📝',
    color: '#000000',
    connected: false,
    category: 'apps',
  },
  {
    id: 'trello',
    name: 'Trello',
    description: 'Manage boards, lists, and cards.',
    icon: '📋',
    color: '#0079BF',
    connected: false,
    category: 'apps',
  },
  {
    id: 'clickup',
    name: 'ClickUp',
    description: 'One app to replace them all. Task management.',
    icon: '✅',
    color: '#7B68EE',
    connected: false,
    category: 'apps',
  },
  {
    id: 'jira',
    name: 'Jira',
    description: 'Issue tracking and agile project management.',
    icon: '🎯',
    color: '#0052CC',
    connected: false,
    category: 'apps',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Connect to channels and send messages.',
    icon: '💬',
    color: '#4A154B',
    connected: false,
    category: 'apps',
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Access repos, issues, and pull requests.',
    icon: '🐙',
    color: '#181717',
    connected: false,
    category: 'apps',
  },
];

export default function ConnectorsScreen({ navigation }: ConnectorsScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'apps' | 'custom_api' | 'custom_mcp'>('apps');
  const [connectors, setConnectors] = useState(CONNECTORS);

  const filteredConnectors = connectors.filter(
    (c) =>
      c.category === activeTab &&
      (c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleConnect = (connector: ConnectorItem) => {
    if (connector.connected) {
      Alert.alert(
        'Disconnect',
        `Are you sure you want to disconnect ${connector.name}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Disconnect',
            style: 'destructive',
            onPress: () => {
              setConnectors((prev) =>
                prev.map((c) =>
                  c.id === connector.id ? { ...c, connected: false } : c
                )
              );
            },
          },
        ]
      );
    } else {
      // Navigate to connection flow or show modal
      Alert.alert(
        `Connect ${connector.name}`,
        'This will open the authentication flow.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Connect',
            onPress: () => {
              // Simulate connection
              setConnectors((prev) =>
                prev.map((c) =>
                  c.id === connector.id ? { ...c, connected: true } : c
                )
              );
            },
          },
        ]
      );
    }
  };

  const tabs = [
    { id: 'apps', label: 'Apps' },
    { id: 'custom_api', label: 'Custom API' },
    { id: 'custom_mcp', label: 'Custom MCP' },
  ] as const;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.colors.textPrimary }]}>
          Connectors
        </Text>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={[styles.closeButton, { color: theme.colors.textTertiary }]}>✕</Text>
        </TouchableOpacity>
      </View>

      {/* Description */}
      <View style={styles.descriptionContainer}>
        <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
          Let Alfred access your favorite tools to enable smarter capabilities and automate your workflow.
        </Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tab,
              activeTab === tab.id && { backgroundColor: theme.colors.primary },
              activeTab !== tab.id && { backgroundColor: theme.colors.bgSurface },
            ]}
            onPress={() => setActiveTab(tab.id)}
          >
            <Text
              style={[
                styles.tabText,
                {
                  color: activeTab === tab.id ? '#FFFFFF' : theme.colors.textSecondary,
                },
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <TextInput
          style={[
            styles.searchInput,
            {
              backgroundColor: theme.colors.bgSurface,
              color: theme.colors.textPrimary,
              borderColor: theme.colors.border,
            },
          ]}
          placeholder="Search integrations..."
          placeholderTextColor={theme.colors.textTertiary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Connectors List */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.listContent, { paddingBottom: insets.bottom + 20 }]}
        showsVerticalScrollIndicator={false}
      >
        {filteredConnectors.map((connector) => (
          <View
            key={connector.id}
            style={[styles.connectorCard, { backgroundColor: theme.colors.bgSurface }]}
          >
            <View style={styles.connectorLeft}>
              <View
                style={[
                  styles.connectorIcon,
                  { backgroundColor: connector.color + '20' },
                ]}
              >
                <Text style={styles.connectorIconText}>{connector.icon}</Text>
              </View>
              <View style={styles.connectorInfo}>
                <Text style={[styles.connectorName, { color: theme.colors.textPrimary }]}>
                  {connector.name}
                </Text>
                <Text
                  style={[styles.connectorDescription, { color: theme.colors.textSecondary }]}
                  numberOfLines={2}
                >
                  {connector.description}
                </Text>
              </View>
            </View>
            <TouchableOpacity
              style={[
                styles.connectButton,
                connector.connected
                  ? { backgroundColor: theme.colors.success }
                  : { backgroundColor: theme.colors.primary },
              ]}
              onPress={() => handleConnect(connector)}
            >
              <Text style={styles.connectButtonText}>
                {connector.connected ? 'Connected' : 'Connect'}
              </Text>
            </TouchableOpacity>
          </View>
        ))}

        {activeTab === 'custom_api' && (
          <TouchableOpacity
            style={[styles.addCustomCard, { borderColor: theme.colors.border }]}
          >
            <Text style={[styles.addCustomIcon, { color: theme.colors.primary }]}>+</Text>
            <Text style={[styles.addCustomText, { color: theme.colors.textPrimary }]}>
              Add Custom API
            </Text>
            <Text style={[styles.addCustomDescription, { color: theme.colors.textSecondary }]}>
              Connect any REST API with custom authentication
            </Text>
          </TouchableOpacity>
        )}

        {activeTab === 'custom_mcp' && (
          <TouchableOpacity
            style={[styles.addCustomCard, { borderColor: theme.colors.border }]}
          >
            <Text style={[styles.addCustomIcon, { color: theme.colors.primary }]}>+</Text>
            <Text style={[styles.addCustomText, { color: theme.colors.textPrimary }]}>
              Add MCP Server
            </Text>
            <Text style={[styles.addCustomDescription, { color: theme.colors.textSecondary }]}>
              Connect to Model Context Protocol servers
            </Text>
          </TouchableOpacity>
        )}

        {filteredConnectors.length === 0 && activeTab === 'apps' && (
          <View style={styles.emptyState}>
            <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
              No connectors found matching "{searchQuery}"
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
  },
  closeButton: {
    fontSize: 20,
    padding: 8,
  },
  descriptionContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
  },
  tabsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 8,
    marginBottom: 16,
  },
  tab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
  },
  searchContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  searchInput: {
    height: 44,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 15,
    borderWidth: 1,
  },
  scrollView: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: 20,
    gap: 12,
  },
  connectorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 16,
  },
  connectorLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  connectorIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  connectorIconText: {
    fontSize: 24,
  },
  connectorInfo: {
    flex: 1,
    marginLeft: 12,
    marginRight: 12,
  },
  connectorName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  connectorDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  connectButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  connectButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  addCustomCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 2,
    borderStyle: 'dashed',
    alignItems: 'center',
  },
  addCustomIcon: {
    fontSize: 32,
    fontWeight: '300',
    marginBottom: 8,
  },
  addCustomText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  addCustomDescription: {
    fontSize: 13,
    textAlign: 'center',
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 15,
    textAlign: 'center',
  },
});
