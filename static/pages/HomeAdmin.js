import store from '../utils/store.js';

const HomeAdmin = {
    template: `
        <div class="container">
            <h1>Admin Home</h1>
            <div v-if="filteredSubjects.length === 0" class="alert alert-info">
                No matches found
            </div>
            <div v-for="subject in filteredSubjects" :key="subject.name" class="mb-4">
                <h2>{{ subject.name }}</h2>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Chapter Name</th>
                                <th class="d-none d-md-table-cell">Description</th>
                                <th>Questions</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="chapter in subject.chapters" :key="chapter.id">
                                <td>
                                    {{ chapter.name }}
                                    <div class="d-md-none text-muted small">{{ chapter.description }}</div>
                                </td>
                                <td class="d-none d-md-table-cell">{{ chapter.description }}</td>
                                <td>{{ chapter.question_count }}</td>
                                <td>
                                    <div class="btn-group">
                                        <button class="btn btn-sm btn-primary" @click="openEditChapterModal(chapter)">Edit</button>
                                        <button class="btn btn-sm btn-danger" @click="handleDeleteChapter(chapter.id)">Delete</button>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <button class="btn btn-sm btn-success" @click="openAddChapterModal(subject.name)">Add Chapter</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <button class="btn btn-primary" @click="openAddSubjectModal">Add Subject</button>

            <div class="modal fade" id="chapterModal" tabindex="-1" aria-labelledby="chapterModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="chapterModalLabel" v-if="editingChapter">Edit Chapter</h5>
                            <h5 class="modal-title" id="chapterModalLabel" v-else>Add Chapter</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <input type="text" class="form-control mb-2" v-model="chapterName" placeholder="Chapter Name">
                            <input type="text" class="form-control" v-model="chapterDescription" placeholder="Chapter Description">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" @click="saveChapter">Save</button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="modal fade" id="subjectModal" tabindex="-1" aria-labelledby="subjectModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="subjectModalLabel">Add Subject</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <input type="text" class="form-control mb-2" v-model="subjectName" placeholder="Subject Name">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" @click="saveSubject">Save</button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            subjects: [],
            isChapterModalActive: false,
            isSubjectModalActive: false,
            editingChapter: null,
            chapterName: '',
            chapterDescription: '',
            subjectName: '',
            subjectDescription: '',
            selectedSubjectName: '',
            chapterModal: null,
            subjectModal: null
        };
    },
    computed: {
        filteredSubjects() {
            const query = this.$store.state.search.query.toLowerCase();
            if (!query) return this.subjects;
            
            return this.subjects.map(subject => {
                const subjectMatches = subject.name.toLowerCase().includes(query);
                
                const filteredChapters = subject.chapters.filter(chapter =>
                    chapter.name.toLowerCase().includes(query) ||
                    (chapter.description && chapter.description.toLowerCase().includes(query))
                );
                
                if (subjectMatches || filteredChapters.length > 0) {
                    return {
                        ...subject,
                        chapters: filteredChapters
                    };
                }
                return null;
            }).filter(Boolean);
        }
    },
    mounted() {
        this.fetchSubjects();
        this.$nextTick(() => {
            try {
                const chapterModalEl = document.getElementById('chapterModal');
                const subjectModalEl = document.getElementById('subjectModal');
                
                if (chapterModalEl && typeof bootstrap !== 'undefined') {
                    this.chapterModal = new bootstrap.Modal(chapterModalEl);
                }
                if (subjectModalEl && typeof bootstrap !== 'undefined') {
                    this.subjectModal = new bootstrap.Modal(subjectModalEl);
                }
            } catch (error) {
                console.error('Modal initialization error:', error);
            }
        });
    },
    methods: {
        async fetchSubjects() {
            try {
                const response = await fetch('/api/subjects', {
                    headers: {
                        'Authentication-Token': store.state.authToken
                    }
                });
                const data = await response.json();
                this.subjects = data;
            } catch (error) {
                console.error('Error fetching subjects:', error);
            }
        },
        openEditChapterModal(chapter) {
            this.editingChapter = chapter;
            this.chapterName = chapter.name;
            this.chapterDescription = chapter.description;
            this.isChapterModalActive = true;
            this.chapterModal.show();
        },
        openAddChapterModal(subjectName) {
            this.editingChapter = null;
            this.chapterName = '';
            this.chapterDescription = '';
            this.selectedSubjectName = subjectName;
            this.isChapterModalActive = true;
            this.chapterModal.show();
        },
        closeChapterModal() {
            this.isChapterModalActive = false;
            this.chapterModal.hide();
        },
        openAddSubjectModal() {
            this.subjectName = '';
            this.subjectDescription = '';
            this.isSubjectModalActive = true;
            this.subjectModal.show();
        },
        closeSubjectModal() {
            this.isSubjectModalActive = false;
            this.subjectModal.hide();
        },
        async saveChapter() {
            try {
                const chapterData = {
                    name: this.chapterName,
                    description: this.chapterDescription,
                    subject_name: this.selectedSubjectName
                };

                const url = this.editingChapter
                    ? `/api/chapters/${this.editingChapter.id}`
                    : '/api/chapters';
                const method = this.editingChapter ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authentication-Token': store.state.authToken
                    },
                    body: JSON.stringify(chapterData)
                });

                if (response.ok) {
                    await this.fetchSubjects();
                    this.closeChapterModal();
                } else {
                    console.error('Failed to save chapter:', response.status, response.statusText, await response.json());
                }

            } catch (error) {
                console.error('Error saving chapter:', error);
            }
        },
        async handleDeleteChapter(chapterId) {
            try {
                const response = await fetch(`/api/chapters/${chapterId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authentication-Token': store.state.authToken
                    }
                });
                if (response.ok) {
                    this.fetchSubjects();
                } else {
                    console.error('Failed to delete chapter:', response);
                }
            } catch (error) {
                console.error('Error deleting chapter:', error);
            }
        },
        async saveSubject() {
            try {
                const response = await fetch('/api/subjects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authentication-Token': store.state.authToken
                    },
                    body: JSON.stringify({
                        name: this.subjectName,
                    })
                });

                if (response.ok) {
                    await this.fetchSubjects();
                    this.closeSubjectModal();
                } else {
                    const errorData = await response.json();
                    console.error('Failed to save subject:', response.status, response.statusText, errorData);
                    if (errorData && errorData.message) {
                        alert(errorData.message);
                    }
                }
            } catch (error) {
                console.error('Error saving subject:', error);
            }
        }
    }
};

export default HomeAdmin;