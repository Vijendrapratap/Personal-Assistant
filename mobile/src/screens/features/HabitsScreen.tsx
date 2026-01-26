import React, { useState, useEffect, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
    TextInput,
    Modal,
    Alert,
    ActivityIndicator,
} from 'react-native';
import { habitsApi, Habit } from '../../api/services';

const CATEGORY_COLORS: Record<string, string> = {
    fitness: '#4caf50',
    productivity: '#1a73e8',
    learning: '#9c27b0',
    health: '#00bcd4',
    mindfulness: '#ff9800',
    social: '#e91e63',
    other: '#607d8b',
};

const FREQUENCY_LABELS: Record<string, string> = {
    daily: 'Daily',
    weekly: 'Weekly',
    weekdays: 'Weekdays',
    custom: 'Custom',
};

interface Props {
    navigation: any;
}

export default function HabitsScreen({ navigation }: Props) {
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [habits, setHabits] = useState<Habit[]>([]);
    const [todayPending, setTodayPending] = useState<Habit[]>([]);
    const [todayCompleted, setTodayCompleted] = useState<Habit[]>([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showAllHabits, setShowAllHabits] = useState(false);

    // Form state
    const [newHabit, setNewHabit] = useState({
        name: '',
        description: '',
        frequency: 'daily',
        time_preference: '',
        motivation: '',
        category: 'productivity',
    });

    const loadData = async () => {
        try {
            const [allHabits, todayData] = await Promise.all([
                habitsApi.list(true),
                habitsApi.getToday(),
            ]);
            setHabits(allHabits.habits);
            setTodayPending(todayData.pending);
            setTodayCompleted(todayData.completed);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        loadData();
    }, []);

    const handleCreateHabit = async () => {
        if (!newHabit.name.trim()) {
            Alert.alert('Error', 'Habit name is required');
            return;
        }

        try {
            await habitsApi.create(newHabit);
            setShowAddModal(false);
            setNewHabit({
                name: '',
                description: '',
                frequency: 'daily',
                time_preference: '',
                motivation: '',
                category: 'productivity',
            });
            loadData();
            Alert.alert('Success', 'Habit created! Stay consistent!');
        } catch (err) {
            Alert.alert('Error', 'Failed to create habit');
        }
    };

    const handleLogHabit = async (habitId: string) => {
        try {
            const result = await habitsApi.log(habitId);
            loadData();
            Alert.alert(
                'Well Done!',
                `${result.current_streak} day streak! Keep it up!`
            );
        } catch (err) {
            Alert.alert('Error', 'Failed to log habit');
        }
    };

    const getTotalStreaks = () => {
        return habits.reduce((sum, h) => sum + h.current_streak, 0);
    };

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#1a73e8" />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <ScrollView
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
            >
                {/* Stats Header */}
                <View style={styles.statsHeader}>
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>{todayCompleted.length}/{todayPending.length + todayCompleted.length}</Text>
                        <Text style={styles.statLabel}>Today</Text>
                    </View>
                    <View style={styles.statDivider} />
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>{getTotalStreaks()}</Text>
                        <Text style={styles.statLabel}>Total Streaks</Text>
                    </View>
                    <View style={styles.statDivider} />
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>{habits.length}</Text>
                        <Text style={styles.statLabel}>Active</Text>
                    </View>
                </View>

                {/* Toggle View */}
                <View style={styles.toggleContainer}>
                    <TouchableOpacity
                        style={[styles.toggleButton, !showAllHabits && styles.toggleActive]}
                        onPress={() => setShowAllHabits(false)}
                    >
                        <Text style={[styles.toggleText, !showAllHabits && styles.toggleTextActive]}>
                            Today
                        </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.toggleButton, showAllHabits && styles.toggleActive]}
                        onPress={() => setShowAllHabits(true)}
                    >
                        <Text style={[styles.toggleText, showAllHabits && styles.toggleTextActive]}>
                            All Habits
                        </Text>
                    </TouchableOpacity>
                </View>

                {!showAllHabits ? (
                    <>
                        {/* Pending Today */}
                        {todayPending.length > 0 && (
                            <View style={styles.section}>
                                <Text style={styles.sectionTitle}>Pending</Text>
                                {todayPending.map((habit) => (
                                    <HabitCard
                                        key={habit.habit_id}
                                        habit={habit}
                                        completed={false}
                                        onLog={() => handleLogHabit(habit.habit_id)}
                                    />
                                ))}
                            </View>
                        )}

                        {/* Completed Today */}
                        {todayCompleted.length > 0 && (
                            <View style={styles.section}>
                                <Text style={styles.sectionTitle}>Completed</Text>
                                {todayCompleted.map((habit) => (
                                    <HabitCard
                                        key={habit.habit_id}
                                        habit={habit}
                                        completed={true}
                                        onLog={() => {}}
                                    />
                                ))}
                            </View>
                        )}

                        {todayPending.length === 0 && todayCompleted.length === 0 && (
                            <View style={styles.emptyState}>
                                <Text style={styles.emptyEmoji}>🎯</Text>
                                <Text style={styles.emptyText}>No habits for today</Text>
                                <Text style={styles.emptySubtext}>Create habits to start tracking</Text>
                            </View>
                        )}
                    </>
                ) : (
                    <View style={styles.section}>
                        {habits.map((habit) => (
                            <View key={habit.habit_id} style={styles.habitDetailCard}>
                                <View style={styles.habitHeader}>
                                    <View style={[styles.categoryDot, { backgroundColor: CATEGORY_COLORS[habit.category] || CATEGORY_COLORS.other }]} />
                                    <Text style={styles.habitName}>{habit.name}</Text>
                                    <View style={styles.frequencyBadge}>
                                        <Text style={styles.frequencyText}>
                                            {FREQUENCY_LABELS[habit.frequency] || habit.frequency}
                                        </Text>
                                    </View>
                                </View>

                                {habit.description && (
                                    <Text style={styles.habitDescription}>{habit.description}</Text>
                                )}

                                <View style={styles.streakRow}>
                                    <View style={styles.streakItem}>
                                        <Text style={styles.streakNumber}>{habit.current_streak}</Text>
                                        <Text style={styles.streakLabel}>Current</Text>
                                    </View>
                                    <View style={styles.streakItem}>
                                        <Text style={styles.streakNumber}>{habit.best_streak}</Text>
                                        <Text style={styles.streakLabel}>Best</Text>
                                    </View>
                                    <View style={styles.streakItem}>
                                        <Text style={styles.streakNumber}>{habit.total_completions}</Text>
                                        <Text style={styles.streakLabel}>Total</Text>
                                    </View>
                                </View>

                                {habit.motivation && (
                                    <Text style={styles.motivation}>"{habit.motivation}"</Text>
                                )}
                            </View>
                        ))}

                        {habits.length === 0 && (
                            <View style={styles.emptyState}>
                                <Text style={styles.emptyEmoji}>📝</Text>
                                <Text style={styles.emptyText}>No habits yet</Text>
                                <Text style={styles.emptySubtext}>Tap + to create your first habit</Text>
                            </View>
                        )}
                    </View>
                )}

                <View style={{ height: 100 }} />
            </ScrollView>

            {/* FAB */}
            <TouchableOpacity
                style={styles.fab}
                onPress={() => setShowAddModal(true)}
            >
                <Text style={styles.fabText}>+</Text>
            </TouchableOpacity>

            {/* Add Habit Modal */}
            <Modal
                visible={showAddModal}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowAddModal(false)}
            >
                <View style={styles.modalOverlay}>
                    <ScrollView style={styles.modalContent}>
                        <Text style={styles.modalTitle}>New Habit</Text>

                        <Text style={styles.inputLabel}>Habit Name *</Text>
                        <TextInput
                            style={styles.input}
                            value={newHabit.name}
                            onChangeText={(text) => setNewHabit({ ...newHabit, name: text })}
                            placeholder="e.g., Daily Workout"
                        />

                        <Text style={styles.inputLabel}>Description</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            value={newHabit.description}
                            onChangeText={(text) => setNewHabit({ ...newHabit, description: text })}
                            placeholder="What does this habit involve?"
                            multiline
                            numberOfLines={2}
                        />

                        <Text style={styles.inputLabel}>Category</Text>
                        <View style={styles.categorySelector}>
                            {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
                                <TouchableOpacity
                                    key={cat}
                                    style={[
                                        styles.categoryOption,
                                        newHabit.category === cat && { backgroundColor: color }
                                    ]}
                                    onPress={() => setNewHabit({ ...newHabit, category: cat })}
                                >
                                    <Text style={[
                                        styles.categoryOptionText,
                                        newHabit.category === cat && { color: '#fff' }
                                    ]}>
                                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={styles.inputLabel}>Frequency</Text>
                        <View style={styles.frequencySelector}>
                            {Object.entries(FREQUENCY_LABELS).map(([key, label]) => (
                                <TouchableOpacity
                                    key={key}
                                    style={[
                                        styles.frequencyOption,
                                        newHabit.frequency === key && styles.frequencyOptionActive
                                    ]}
                                    onPress={() => setNewHabit({ ...newHabit, frequency: key })}
                                >
                                    <Text style={[
                                        styles.frequencyOptionText,
                                        newHabit.frequency === key && { color: '#1a73e8' }
                                    ]}>
                                        {label}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={styles.inputLabel}>Preferred Time</Text>
                        <TextInput
                            style={styles.input}
                            value={newHabit.time_preference}
                            onChangeText={(text) => setNewHabit({ ...newHabit, time_preference: text })}
                            placeholder="e.g., 07:00"
                        />

                        <Text style={styles.inputLabel}>Why is this important to you?</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            value={newHabit.motivation}
                            onChangeText={(text) => setNewHabit({ ...newHabit, motivation: text })}
                            placeholder="Your motivation..."
                            multiline
                            numberOfLines={2}
                        />

                        <View style={styles.modalButtons}>
                            <TouchableOpacity
                                style={styles.cancelButton}
                                onPress={() => setShowAddModal(false)}
                            >
                                <Text style={styles.cancelButtonText}>Cancel</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={styles.createButton}
                                onPress={handleCreateHabit}
                            >
                                <Text style={styles.createButtonText}>Create</Text>
                            </TouchableOpacity>
                        </View>

                        <View style={{ height: 40 }} />
                    </ScrollView>
                </View>
            </Modal>
        </View>
    );
}

// Habit Card Component
function HabitCard({ habit, completed, onLog }: {
    habit: Habit;
    completed: boolean;
    onLog: () => void;
}) {
    return (
        <View style={[styles.habitCard, completed && styles.habitCardCompleted]}>
            <TouchableOpacity
                style={[styles.checkbox, completed && styles.checkboxChecked]}
                onPress={onLog}
                disabled={completed}
            >
                {completed && <Text style={styles.checkmark}>✓</Text>}
            </TouchableOpacity>
            <View style={styles.habitInfo}>
                <Text style={[styles.habitCardName, completed && styles.habitCardNameCompleted]}>
                    {habit.name}
                </Text>
                <View style={styles.habitMeta}>
                    <View style={[styles.categoryBadge, { backgroundColor: CATEGORY_COLORS[habit.category] || CATEGORY_COLORS.other }]}>
                        <Text style={styles.categoryBadgeText}>{habit.category}</Text>
                    </View>
                    <Text style={styles.streakText}>
                        🔥 {habit.current_streak}
                    </Text>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    statsHeader: {
        flexDirection: 'row',
        backgroundColor: '#4caf50',
        padding: 20,
        justifyContent: 'space-around',
        alignItems: 'center',
    },
    statItem: {
        alignItems: 'center',
    },
    statNumber: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#fff',
    },
    statLabel: {
        fontSize: 12,
        color: 'rgba(255,255,255,0.8)',
        marginTop: 4,
    },
    statDivider: {
        width: 1,
        height: 40,
        backgroundColor: 'rgba(255,255,255,0.3)',
    },
    toggleContainer: {
        flexDirection: 'row',
        margin: 15,
        backgroundColor: '#e0e0e0',
        borderRadius: 10,
        padding: 4,
    },
    toggleButton: {
        flex: 1,
        paddingVertical: 10,
        alignItems: 'center',
        borderRadius: 8,
    },
    toggleActive: {
        backgroundColor: '#fff',
    },
    toggleText: {
        fontSize: 14,
        color: '#666',
        fontWeight: '600',
    },
    toggleTextActive: {
        color: '#333',
    },
    section: {
        marginHorizontal: 15,
        marginBottom: 15,
    },
    sectionTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#666',
        marginBottom: 10,
    },
    habitCard: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 10,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    habitCardCompleted: {
        backgroundColor: '#e8f5e9',
    },
    checkbox: {
        width: 28,
        height: 28,
        borderRadius: 14,
        borderWidth: 2,
        borderColor: '#4caf50',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 14,
    },
    checkboxChecked: {
        backgroundColor: '#4caf50',
    },
    checkmark: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 16,
    },
    habitInfo: {
        flex: 1,
    },
    habitCardName: {
        fontSize: 16,
        fontWeight: '500',
        color: '#333',
        marginBottom: 4,
    },
    habitCardNameCompleted: {
        textDecorationLine: 'line-through',
        color: '#666',
    },
    habitMeta: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    categoryBadge: {
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 10,
        marginRight: 10,
    },
    categoryBadgeText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: '600',
        textTransform: 'capitalize',
    },
    streakText: {
        fontSize: 12,
        color: '#ff9800',
    },
    habitDetailCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    habitHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    categoryDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 10,
    },
    habitName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
        flex: 1,
    },
    frequencyBadge: {
        backgroundColor: '#e3f2fd',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 10,
    },
    frequencyText: {
        fontSize: 11,
        color: '#1976d2',
        fontWeight: '500',
    },
    habitDescription: {
        fontSize: 14,
        color: '#666',
        marginBottom: 12,
    },
    streakRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        backgroundColor: '#fafafa',
        borderRadius: 8,
        padding: 12,
        marginBottom: 10,
    },
    streakItem: {
        alignItems: 'center',
    },
    streakNumber: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
    },
    streakLabel: {
        fontSize: 11,
        color: '#888',
        marginTop: 2,
    },
    motivation: {
        fontSize: 13,
        fontStyle: 'italic',
        color: '#888',
        textAlign: 'center',
    },
    emptyState: {
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyEmoji: {
        fontSize: 48,
        marginBottom: 15,
    },
    emptyText: {
        fontSize: 18,
        color: '#666',
    },
    emptySubtext: {
        fontSize: 14,
        color: '#999',
        marginTop: 8,
    },
    fab: {
        position: 'absolute',
        right: 20,
        bottom: 30,
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: '#4caf50',
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
        elevation: 6,
    },
    fabText: {
        fontSize: 28,
        color: '#fff',
        fontWeight: '300',
    },
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'flex-end',
    },
    modalContent: {
        backgroundColor: '#fff',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        padding: 20,
        maxHeight: '90%',
    },
    modalTitle: {
        fontSize: 20,
        fontWeight: '600',
        marginBottom: 20,
        color: '#333',
    },
    inputLabel: {
        fontSize: 14,
        fontWeight: '600',
        color: '#555',
        marginBottom: 8,
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        marginBottom: 16,
        backgroundColor: '#fafafa',
    },
    textArea: {
        height: 70,
        textAlignVertical: 'top',
    },
    categorySelector: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginBottom: 16,
    },
    categoryOption: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: '#ddd',
        marginRight: 8,
        marginBottom: 8,
    },
    categoryOptionText: {
        fontSize: 13,
        color: '#666',
    },
    frequencySelector: {
        flexDirection: 'row',
        marginBottom: 16,
    },
    frequencyOption: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: '#ddd',
        marginRight: 8,
    },
    frequencyOptionActive: {
        borderColor: '#1a73e8',
        backgroundColor: '#e3f2fd',
    },
    frequencyOptionText: {
        fontSize: 13,
        color: '#666',
    },
    modalButtons: {
        flexDirection: 'row',
        marginTop: 10,
    },
    cancelButton: {
        flex: 1,
        padding: 14,
        alignItems: 'center',
        marginRight: 10,
    },
    cancelButtonText: {
        color: '#666',
        fontSize: 16,
    },
    createButton: {
        flex: 1,
        backgroundColor: '#4caf50',
        padding: 14,
        borderRadius: 8,
        alignItems: 'center',
    },
    createButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
});
