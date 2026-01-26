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
import { projectsApi, Project } from '../../api/services';

const ROLE_COLORS: Record<string, string> = {
    founder: '#9c27b0',
    coo: '#1a73e8',
    pm: '#4caf50',
    developer: '#ff9800',
    contributor: '#607d8b',
};

const ROLE_LABELS: Record<string, string> = {
    founder: 'Founder',
    coo: 'COO',
    pm: 'PM',
    developer: 'Developer',
    contributor: 'Contributor',
};

interface Props {
    navigation: any;
}

export default function ProjectsScreen({ navigation }: Props) {
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [projects, setProjects] = useState<Project[]>([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showUpdateModal, setShowUpdateModal] = useState(false);
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);

    // Form states
    const [newProject, setNewProject] = useState({
        name: '',
        organization: '',
        role: 'pm',
        description: '',
    });
    const [updateContent, setUpdateContent] = useState('');

    const loadProjects = async () => {
        try {
            const data = await projectsApi.list();
            setProjects(data.projects);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadProjects();
    }, []);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        loadProjects();
    }, []);

    const handleCreateProject = async () => {
        if (!newProject.name.trim()) {
            Alert.alert('Error', 'Project name is required');
            return;
        }

        try {
            await projectsApi.create(newProject);
            setShowAddModal(false);
            setNewProject({ name: '', organization: '', role: 'pm', description: '' });
            loadProjects();
        } catch (err) {
            Alert.alert('Error', 'Failed to create project');
        }
    };

    const handleAddUpdate = async () => {
        if (!selectedProject || !updateContent.trim()) {
            Alert.alert('Error', 'Update content is required');
            return;
        }

        try {
            await projectsApi.addUpdate(selectedProject.project_id, {
                content: updateContent,
                update_type: 'progress',
            });
            setShowUpdateModal(false);
            setUpdateContent('');
            setSelectedProject(null);
            loadProjects();
            Alert.alert('Success', 'Update logged successfully');
        } catch (err) {
            Alert.alert('Error', 'Failed to add update');
        }
    };

    const getHealthColor = (score: number) => {
        if (score >= 80) return '#4caf50';
        if (score >= 50) return '#ff9800';
        return '#d32f2f';
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
                        <Text style={styles.statNumber}>{projects.filter(p => p.status === 'active').length}</Text>
                        <Text style={styles.statLabel}>Active</Text>
                    </View>
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>
                            {projects.reduce((sum, p) => sum + (p.task_count - p.completed_task_count), 0)}
                        </Text>
                        <Text style={styles.statLabel}>Tasks</Text>
                    </View>
                </View>

                {/* Projects List */}
                {projects.map((project) => (
                    <TouchableOpacity
                        key={project.project_id}
                        style={styles.projectCard}
                        onPress={() => {
                            setSelectedProject(project);
                            setShowUpdateModal(true);
                        }}
                    >
                        <View style={styles.projectHeader}>
                            <View style={styles.projectTitleRow}>
                                <Text style={styles.projectName}>{project.name}</Text>
                                <View style={[styles.roleBadge, { backgroundColor: ROLE_COLORS[project.role] || '#607d8b' }]}>
                                    <Text style={styles.roleText}>{ROLE_LABELS[project.role] || project.role}</Text>
                                </View>
                            </View>
                            {project.organization && (
                                <Text style={styles.projectOrg}>{project.organization}</Text>
                            )}
                        </View>

                        {/* Health Bar */}
                        <View style={styles.healthSection}>
                            <View style={styles.healthBar}>
                                <View
                                    style={[
                                        styles.healthFill,
                                        {
                                            width: `${project.health_score}%`,
                                            backgroundColor: getHealthColor(project.health_score)
                                        }
                                    ]}
                                />
                            </View>
                            <Text style={styles.healthText}>{Math.round(project.health_score)}%</Text>
                        </View>

                        {/* Tasks Progress */}
                        <View style={styles.projectMeta}>
                            <Text style={styles.taskProgress}>
                                {project.completed_task_count}/{project.task_count} tasks completed
                            </Text>
                            <Text style={styles.statusBadge}>{project.status}</Text>
                        </View>

                        {project.description && (
                            <Text style={styles.projectDesc} numberOfLines={2}>
                                {project.description}
                            </Text>
                        )}
                    </TouchableOpacity>
                ))}

                {projects.length === 0 && (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No projects yet</Text>
                        <Text style={styles.emptySubtext}>Tap + to add your first project</Text>
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

            {/* Add Project Modal */}
            <Modal
                visible={showAddModal}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowAddModal(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>New Project</Text>

                        <Text style={styles.inputLabel}>Project Name *</Text>
                        <TextInput
                            style={styles.input}
                            value={newProject.name}
                            onChangeText={(text) => setNewProject({ ...newProject, name: text })}
                            placeholder="e.g., Muay Thai Tickets"
                        />

                        <Text style={styles.inputLabel}>Organization</Text>
                        <TextInput
                            style={styles.input}
                            value={newProject.organization}
                            onChangeText={(text) => setNewProject({ ...newProject, organization: text })}
                            placeholder="e.g., Codesstellar"
                        />

                        <Text style={styles.inputLabel}>Your Role</Text>
                        <View style={styles.roleSelector}>
                            {Object.entries(ROLE_LABELS).map(([key, label]) => (
                                <TouchableOpacity
                                    key={key}
                                    style={[
                                        styles.roleOption,
                                        newProject.role === key && { backgroundColor: ROLE_COLORS[key] }
                                    ]}
                                    onPress={() => setNewProject({ ...newProject, role: key })}
                                >
                                    <Text style={[
                                        styles.roleOptionText,
                                        newProject.role === key && { color: '#fff' }
                                    ]}>
                                        {label}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={styles.inputLabel}>Description</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            value={newProject.description}
                            onChangeText={(text) => setNewProject({ ...newProject, description: text })}
                            placeholder="Brief description..."
                            multiline
                            numberOfLines={3}
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
                                onPress={handleCreateProject}
                            >
                                <Text style={styles.createButtonText}>Create</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>
            </Modal>

            {/* Add Update Modal */}
            <Modal
                visible={showUpdateModal}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowUpdateModal(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>
                            Update: {selectedProject?.name}
                        </Text>

                        <Text style={styles.inputLabel}>What's the latest?</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            value={updateContent}
                            onChangeText={setUpdateContent}
                            placeholder="e.g., Completed the booking flow. Blocked on payment integration..."
                            multiline
                            numberOfLines={5}
                        />

                        <View style={styles.modalButtons}>
                            <TouchableOpacity
                                style={styles.cancelButton}
                                onPress={() => {
                                    setShowUpdateModal(false);
                                    setSelectedProject(null);
                                    setUpdateContent('');
                                }}
                            >
                                <Text style={styles.cancelButtonText}>Cancel</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={styles.createButton}
                                onPress={handleAddUpdate}
                            >
                                <Text style={styles.createButtonText}>Log Update</Text>
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
    statsHeader: {
        flexDirection: 'row',
        backgroundColor: '#1a73e8',
        padding: 20,
        justifyContent: 'space-around',
    },
    statItem: {
        alignItems: 'center',
    },
    statNumber: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#fff',
    },
    statLabel: {
        fontSize: 12,
        color: 'rgba(255,255,255,0.8)',
        marginTop: 4,
    },
    projectCard: {
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
    projectHeader: {
        marginBottom: 12,
    },
    projectTitleRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    projectName: {
        fontSize: 18,
        fontWeight: '600',
        color: '#333',
        flex: 1,
    },
    roleBadge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
    },
    roleText: {
        color: '#fff',
        fontSize: 11,
        fontWeight: '600',
    },
    projectOrg: {
        fontSize: 13,
        color: '#666',
        marginTop: 4,
    },
    healthSection: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
    },
    healthBar: {
        flex: 1,
        height: 6,
        backgroundColor: '#e0e0e0',
        borderRadius: 3,
        marginRight: 10,
    },
    healthFill: {
        height: '100%',
        borderRadius: 3,
    },
    healthText: {
        fontSize: 12,
        fontWeight: '600',
        color: '#666',
        width: 40,
    },
    projectMeta: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    taskProgress: {
        fontSize: 12,
        color: '#666',
    },
    statusBadge: {
        fontSize: 10,
        color: '#4caf50',
        textTransform: 'uppercase',
        fontWeight: '600',
    },
    projectDesc: {
        fontSize: 13,
        color: '#888',
        marginTop: 10,
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
        maxHeight: '80%',
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
        height: 100,
        textAlignVertical: 'top',
    },
    roleSelector: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginBottom: 16,
    },
    roleOption: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: '#ddd',
        marginRight: 8,
        marginBottom: 8,
    },
    roleOptionText: {
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
