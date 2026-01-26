import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    View,
    Text,
    StyleSheet,
    FlatList,
    RefreshControl,
    TouchableOpacity,
    TextInput,
    Modal,
    Alert,
    ActivityIndicator,
    ListRenderItem
} from 'react-native';
import { tasksApi, projectsApi, Task, Project } from '../../api/services';

const PRIORITY_COLORS: Record<string, string> = {
    high: '#d32f2f',
    medium: '#ff9800',
    low: '#1976d2',
};

const STATUS_COLORS: Record<string, string> = {
    pending: '#9e9e9e',
    in_progress: '#1a73e8',
    blocked: '#d32f2f',
    completed: '#4caf50',
};

interface Props {
    navigation: any;
}

type FilterType = 'all' | 'pending' | 'in_progress' | 'blocked' | 'completed';

// Memoized Item Component for Performance
const TaskItem = React.memo(({
    task,
    onStart,
    onBlock,
    onComplete
}: {
    task: Task;
    onStart: (id: string) => void;
    onBlock: (id: string) => void;
    onComplete: (id: string) => void;
}) => (
    <View style={styles.taskCard}>
        <View style={styles.taskHeader}>
            <View style={[styles.priorityDot, { backgroundColor: PRIORITY_COLORS[task.priority] }]} />
            <Text style={styles.taskTitle}>{task.title}</Text>
        </View>

        {task.description && (
            <Text style={styles.taskDescription} numberOfLines={2}>
                {task.description}
            </Text>
        )}

        <View style={styles.taskMeta}>
            {task.project_name && (
                <View style={styles.projectTag}>
                    <Text style={styles.projectTagText}>{task.project_name}</Text>
                </View>
            )}
            <View style={[styles.statusBadge, { backgroundColor: STATUS_COLORS[task.status] + '20' }]}>
                <Text style={[styles.statusText, { color: STATUS_COLORS[task.status] }]}>
                    {task.status.replace('_', ' ')}
                </Text>
            </View>
            {task.due_date && (
                <Text style={styles.dueDate}>
                    Due: {new Date(task.due_date).toLocaleDateString()}
                </Text>
            )}
        </View>

        {/* Action Buttons */}
        <View style={styles.actionRow}>
            {task.status === 'pending' && (
                <TouchableOpacity
                    style={[styles.actionButton, styles.startButton]}
                    onPress={() => onStart(task.task_id)}
                >
                    <Text style={styles.startButtonText}>Start</Text>
                </TouchableOpacity>
            )}
            {(task.status === 'pending' || task.status === 'in_progress') && (
                <>
                    <TouchableOpacity
                        style={[styles.actionButton, styles.blockButton]}
                        onPress={() => onBlock(task.task_id)}
                    >
                        <Text style={styles.blockButtonText}>Block</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.actionButton, styles.completeButton]}
                        onPress={() => onComplete(task.task_id)}
                    >
                        <Text style={styles.completeButtonText}>Complete</Text>
                    </TouchableOpacity>
                </>
            )}
        </View>
    </View>
));

export default function TasksScreen({ navigation }: Props) {
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [filter, setFilter] = useState<FilterType>('pending');
    const [showAddModal, setShowAddModal] = useState(false);

    // Form state
    const [newTask, setNewTask] = useState({
        title: '',
        description: '',
        priority: 'medium',
        project_id: '',
        due_date: '',
    });

    const loadData = async () => {
        try {
            const [tasksData, projectsData] = await Promise.all([
                tasksApi.list({ status: filter === 'all' ? undefined : filter }),
                projectsApi.list('active'),
            ]);
            setTasks(tasksData.tasks);
            setProjects(projectsData.projects);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [filter]);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        loadData();
    }, [filter]);

    const handleCreateTask = async () => {
        if (!newTask.title.trim()) {
            Alert.alert('Error', 'Task title is required');
            return;
        }

        try {
            await tasksApi.create({
                title: newTask.title,
                description: newTask.description,
                priority: newTask.priority,
                project_id: newTask.project_id || undefined,
                due_date: newTask.due_date || undefined,
            });
            setShowAddModal(false);
            setNewTask({ title: '', description: '', priority: 'medium', project_id: '', due_date: '' });
            loadData();
        } catch (err) {
            Alert.alert('Error', 'Failed to create task');
        }
    };

    // Memoize handlers to keep renderItem stable
    const handleCompleteTask = useCallback(async (taskId: string) => {
        try {
            await tasksApi.complete(taskId);
            // Optimistic update or reload? Reload simpler for now.
            // Ideally should filter out or update local state
            setTasks(prev => prev.filter(t => t.task_id !== taskId));
            Alert.alert('Done', 'Task completed!');
        } catch (err) {
            Alert.alert('Error', 'Failed to complete task');
            loadData(); // Revert on error
        }
    }, []);

    const handleStartTask = useCallback(async (taskId: string) => {
        try {
            await tasksApi.start(taskId);
            loadData();
        } catch (err) {
            Alert.alert('Error', 'Failed to start task');
        }
    }, []);

    const handleBlockTask = useCallback(async (taskId: string) => {
        Alert.prompt(
            'Block Task',
            'What is blocking this task?',
            async (blocker) => {
                if (blocker) {
                    try {
                        await tasksApi.block(taskId, blocker);
                        loadData();
                    } catch (err) {
                        Alert.alert('Error', 'Failed to block task');
                    }
                }
            }
        );
    }, []);

    const renderItem: ListRenderItem<Task> = useCallback(({ item }) => (
        <TaskItem
            task={item}
            onStart={handleStartTask}
            onBlock={handleBlockTask}
            onComplete={handleCompleteTask}
        />
    ), [handleStartTask, handleBlockTask, handleCompleteTask]);

    const keyExtractor = useCallback((item: Task) => item.task_id, []);

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#1a73e8" />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            {/* Filter Tabs */}
            <View style={styles.filterContainer}>
                <FlatList
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    data={['pending', 'in_progress', 'blocked', 'completed'] as FilterType[]}
                    keyExtractor={(item) => item}
                    renderItem={({ item: f }) => (
                        <TouchableOpacity
                            style={[styles.filterTab, filter === f && styles.filterTabActive]}
                            onPress={() => setFilter(f)}
                        >
                            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
                                {f.replace('_', ' ').toUpperCase()}
                            </Text>
                        </TouchableOpacity>
                    )}
                />
            </View>

            <FlatList
                data={tasks}
                renderItem={renderItem}
                keyExtractor={keyExtractor}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
                ListFooterComponent={<View style={{ height: 100 }} />}
                ListEmptyComponent={
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No {filter} tasks</Text>
                        <Text style={styles.emptySubtext}>Tap + to add a new task</Text>
                    </View>
                }
            />

            {/* FAB */}
            <TouchableOpacity
                style={styles.fab}
                onPress={() => setShowAddModal(true)}
            >
                <Text style={styles.fabText}>+</Text>
            </TouchableOpacity>

            {/* Add Task Modal */}
            <Modal
                visible={showAddModal}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowAddModal(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>New Task</Text>

                        <Text style={styles.inputLabel}>Title *</Text>
                        <TextInput
                            style={styles.input}
                            value={newTask.title}
                            onChangeText={(text) => setNewTask({ ...newTask, title: text })}
                            placeholder="What needs to be done?"
                        />

                        <Text style={styles.inputLabel}>Description</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            value={newTask.description}
                            onChangeText={(text) => setNewTask({ ...newTask, description: text })}
                            placeholder="Add details..."
                            multiline
                            numberOfLines={3}
                        />

                        <Text style={styles.inputLabel}>Priority</Text>
                        <View style={styles.prioritySelector}>
                            {['high', 'medium', 'low'].map((p) => (
                                <TouchableOpacity
                                    key={p}
                                    style={[
                                        styles.priorityOption,
                                        newTask.priority === p && { backgroundColor: PRIORITY_COLORS[p] }
                                    ]}
                                    onPress={() => setNewTask({ ...newTask, priority: p })}
                                >
                                    <Text style={[
                                        styles.priorityOptionText,
                                        newTask.priority === p && { color: '#fff' }
                                    ]}>
                                        {p.toUpperCase()}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={styles.inputLabel}>Project (Optional)</Text>
                        <FlatList
                            horizontal
                            showsHorizontalScrollIndicator={false}
                            style={styles.projectSelector}
                            data={[null, ...projects]}
                            keyExtractor={(item) => item ? item.project_id : 'none'}
                            renderItem={({ item: project }) => (
                                <TouchableOpacity
                                    style={[
                                        styles.projectOption,
                                        ((!project && !newTask.project_id) || (project && newTask.project_id === project.project_id)) && styles.projectOptionActive
                                    ]}
                                    onPress={() => setNewTask({ ...newTask, project_id: project ? project.project_id : '' })}
                                >
                                    <Text style={[
                                        styles.projectOptionText,
                                        ((!project && !newTask.project_id) || (project && newTask.project_id === project.project_id)) && { color: '#1a73e8' }
                                    ]}>
                                        {project ? project.name : 'None'}
                                    </Text>
                                </TouchableOpacity>
                            )}
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
                                onPress={handleCreateTask}
                            >
                                <Text style={styles.createButtonText}>Create</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>
            </Modal>
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
    filterContainer: {
        backgroundColor: '#fff',
        paddingVertical: 10,
        paddingHorizontal: 10,
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
        height: 60,
    },
    filterTab: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        marginRight: 8,
        borderRadius: 20,
        backgroundColor: '#f0f0f0',
        height: 36,
        justifyContent: 'center'
    },
    filterTabActive: {
        backgroundColor: '#1a73e8',
    },
    filterText: {
        fontSize: 12,
        fontWeight: '600',
        color: '#666',
    },
    filterTextActive: {
        color: '#fff',
    },
    taskCard: {
        backgroundColor: '#fff',
        marginHorizontal: 15,
        marginTop: 15,
        borderRadius: 12,
        padding: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    taskHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    priorityDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 10,
    },
    taskTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
        flex: 1,
    },
    taskDescription: {
        fontSize: 14,
        color: '#666',
        marginBottom: 10,
        marginLeft: 20,
    },
    taskMeta: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        alignItems: 'center',
        marginBottom: 10,
    },
    projectTag: {
        backgroundColor: '#e3f2fd',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        marginRight: 8,
    },
    projectTagText: {
        fontSize: 11,
        color: '#1976d2',
        fontWeight: '500',
    },
    statusBadge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        marginRight: 8,
    },
    statusText: {
        fontSize: 11,
        fontWeight: '600',
        textTransform: 'uppercase',
    },
    dueDate: {
        fontSize: 11,
        color: '#888',
    },
    actionRow: {
        flexDirection: 'row',
        justifyContent: 'flex-end',
        marginTop: 5,
    },
    actionButton: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 6,
        marginLeft: 8,
    },
    startButton: {
        backgroundColor: '#e3f2fd',
    },
    startButtonText: {
        color: '#1976d2',
        fontSize: 13,
        fontWeight: '600',
    },
    blockButton: {
        backgroundColor: '#ffebee',
    },
    blockButtonText: {
        color: '#d32f2f',
        fontSize: 13,
        fontWeight: '600',
    },
    completeButton: {
        backgroundColor: '#4caf50',
    },
    completeButtonText: {
        color: '#fff',
        fontSize: 13,
        fontWeight: '600',
    },
    emptyState: {
        alignItems: 'center',
        paddingVertical: 60,
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
        backgroundColor: '#1a73e8',
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
        maxHeight: '85%',
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
        height: 80,
        textAlignVertical: 'top',
    },
    prioritySelector: {
        flexDirection: 'row',
        marginBottom: 16,
    },
    priorityOption: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: '#ddd',
        marginRight: 8,
    },
    priorityOptionText: {
        fontSize: 13,
        color: '#666',
        fontWeight: '600',
    },
    projectSelector: {
        marginBottom: 16,
        height: 40,
    },
    projectOption: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: '#ddd',
        marginRight: 8,
        height: 36,
    },
    projectOptionActive: {
        borderColor: '#1a73e8',
        backgroundColor: '#e3f2fd',
    },
    projectOptionText: {
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
        backgroundColor: '#1a73e8',
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
