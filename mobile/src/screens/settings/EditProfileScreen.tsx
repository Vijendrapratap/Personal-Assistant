/**
 * EditProfileScreen - Edit user profile details
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { Text, Card, Button } from '../../components/common';
import { profileApi } from '../../api/services';

interface EditProfileScreenProps {
  navigation: any;
}

interface Profile {
  name?: string;
  email?: string;
  bio?: string;
  work_type?: string;
  personality_prompt?: string;
  interaction_type?: string;
  morning_briefing_time?: string;
  evening_review_time?: string;
}

export default function EditProfileScreen({ navigation }: EditProfileScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<Profile>({
    name: '',
    bio: '',
    work_type: '',
    personality_prompt: '',
    interaction_type: 'formal',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await profileApi.get();
      setProfile(data);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await profileApi.update({
        bio: profile.bio,
        work_type: profile.work_type,
        personality_prompt: profile.personality_prompt,
        interaction_type: profile.interaction_type,
      });
      Alert.alert('Success', 'Profile updated successfully.');
      navigation.goBack();
    } catch (err) {
      Alert.alert('Error', 'Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field: keyof Profile, value: string) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const interactionTypes = [
    { value: 'formal', label: 'Formal', desc: 'Professional & respectful' },
    { value: 'casual', label: 'Casual', desc: 'Friendly & relaxed' },
    { value: 'concise', label: 'Concise', desc: 'Brief & to the point' },
  ];

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          {
            paddingTop: insets.top + 12,
            backgroundColor: theme.colors.bg,
            borderBottomColor: theme.colors.border,
          },
        ]}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={[styles.backText, { color: theme.colors.primary }]}>
            Cancel
          </Text>
        </TouchableOpacity>
        <Text variant="h3" style={styles.headerTitle}>
          Edit Profile
        </Text>
        <TouchableOpacity
          style={styles.saveButton}
          onPress={handleSave}
          disabled={saving}
        >
          <Text
            style={[
              styles.saveText,
              { color: saving ? theme.colors.textDisabled : theme.colors.primary },
            ]}
          >
            {saving ? 'Saving...' : 'Save'}
          </Text>
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Basic Info */}
          <View style={styles.section}>
            <Text variant="label" color="secondary" style={styles.sectionLabel}>
              ABOUT YOU
            </Text>
            <Card padding="none" style={styles.formCard}>
              <View
                style={[styles.inputRow, { borderBottomWidth: 1, borderBottomColor: theme.colors.border }]}
              >
                <Text variant="body" style={styles.inputLabel}>
                  Name
                </Text>
                <TextInput
                  style={[styles.input, { color: theme.colors.textPrimary }]}
                  value={profile.name}
                  onChangeText={(value) => updateField('name', value)}
                  placeholder="Your name"
                  placeholderTextColor={theme.colors.textTertiary}
                />
              </View>
              <View style={styles.inputRowMulti}>
                <Text variant="body" style={styles.inputLabel}>
                  Bio
                </Text>
                <TextInput
                  style={[
                    styles.inputMulti,
                    {
                      color: theme.colors.textPrimary,
                      backgroundColor: theme.colors.bgHover,
                    },
                  ]}
                  value={profile.bio}
                  onChangeText={(value) => updateField('bio', value)}
                  placeholder="Tell Alfred a bit about yourself..."
                  placeholderTextColor={theme.colors.textTertiary}
                  multiline
                  numberOfLines={3}
                  textAlignVertical="top"
                />
              </View>
            </Card>
          </View>

          {/* Work Info */}
          <View style={styles.section}>
            <Text variant="label" color="secondary" style={styles.sectionLabel}>
              WORK CONTEXT
            </Text>
            <Card padding="none" style={styles.formCard}>
              <View style={styles.inputRowMulti}>
                <Text variant="body" style={styles.inputLabel}>
                  What you do
                </Text>
                <TextInput
                  style={[
                    styles.inputMulti,
                    {
                      color: theme.colors.textPrimary,
                      backgroundColor: theme.colors.bgHover,
                    },
                  ]}
                  value={profile.work_type}
                  onChangeText={(value) => updateField('work_type', value)}
                  placeholder="e.g., Software engineer at a startup, managing multiple projects..."
                  placeholderTextColor={theme.colors.textTertiary}
                  multiline
                  numberOfLines={2}
                  textAlignVertical="top"
                />
              </View>
            </Card>
          </View>

          {/* Alfred's Personality */}
          <View style={styles.section}>
            <Text variant="label" color="secondary" style={styles.sectionLabel}>
              ALFRED'S PERSONALITY
            </Text>
            <Card padding="none" style={styles.formCard}>
              <View
                style={[styles.inputRowMulti, { borderBottomWidth: 1, borderBottomColor: theme.colors.border }]}
              >
                <Text variant="body" style={styles.inputLabel}>
                  Personality Style
                </Text>
                <TextInput
                  style={[
                    styles.inputMulti,
                    {
                      color: theme.colors.textPrimary,
                      backgroundColor: theme.colors.bgHover,
                    },
                  ]}
                  value={profile.personality_prompt}
                  onChangeText={(value) => updateField('personality_prompt', value)}
                  placeholder="e.g., Witty butler, Motivational coach, Calm advisor..."
                  placeholderTextColor={theme.colors.textTertiary}
                  multiline
                  numberOfLines={2}
                  textAlignVertical="top"
                />
              </View>
              <View style={styles.interactionSection}>
                <Text variant="body" style={styles.inputLabel}>
                  Communication Style
                </Text>
                <View style={styles.interactionOptions}>
                  {interactionTypes.map((type) => (
                    <TouchableOpacity
                      key={type.value}
                      style={[
                        styles.interactionOption,
                        {
                          backgroundColor:
                            profile.interaction_type === type.value
                              ? theme.colors.primary
                              : theme.colors.bgHover,
                          borderColor:
                            profile.interaction_type === type.value
                              ? theme.colors.primary
                              : theme.colors.border,
                        },
                      ]}
                      onPress={() => updateField('interaction_type', type.value)}
                    >
                      <Text
                        style={[
                          styles.interactionLabel,
                          {
                            color:
                              profile.interaction_type === type.value
                                ? '#FFFFFF'
                                : theme.colors.textPrimary,
                          },
                        ]}
                      >
                        {type.label}
                      </Text>
                      <Text
                        style={[
                          styles.interactionDesc,
                          {
                            color:
                              profile.interaction_type === type.value
                                ? 'rgba(255,255,255,0.7)'
                                : theme.colors.textTertiary,
                          },
                        ]}
                      >
                        {type.desc}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </Card>
          </View>

          {/* Save Button */}
          <View style={styles.section}>
            <Button
              title={saving ? 'Saving...' : 'Save Changes'}
              onPress={handleSave}
              loading={saving}
              fullWidth
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 70,
  },
  backText: {
    fontSize: 15,
    fontWeight: '500',
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
  },
  saveButton: {
    width: 70,
    alignItems: 'flex-end',
  },
  saveText: {
    fontSize: 15,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    marginBottom: 12,
  },
  formCard: {
    overflow: 'hidden',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  inputRowMulti: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  inputLabel: {
    width: 80,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    flex: 1,
    fontSize: 15,
    paddingVertical: 4,
  },
  inputMulti: {
    fontSize: 15,
    padding: 12,
    borderRadius: 8,
    minHeight: 60,
  },
  interactionSection: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  interactionOptions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 8,
  },
  interactionOption: {
    flex: 1,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  interactionLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  interactionDesc: {
    fontSize: 11,
    textAlign: 'center',
  },
});
