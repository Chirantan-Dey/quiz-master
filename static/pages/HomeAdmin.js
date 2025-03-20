import store from '../utils/store.js';
import { api } from '../utils/api.js';

const HomeAdmin = {
    template: `
        <div class="container">
            <h1>Admin Home</h1>
            <div v-for="subject in subjects" :key="subject.name" class="mb-4">
                <h2>{{ subject.name }}</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Chapter Name</th>
                            <th>Description</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="chapter in subject.chapters" :key="chapter.id">
                            <td>{{ chapter.name }}</td>
                            <td>{{ chapter.description }}</td>
                            <td>
                                <button class="btn btn-sm btn-primary mr-2" @click="openEditChapterModal(chapter)">Edit</button>
                                <button class="btn btn-sm btn-danger" @click="handleDeleteChapter(chapter.id)">Delete</button>
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
            <button class="btn btn-primary" @click="openAddSubjectModal">Add Subject</button>

            <div class="modal" :class="{ 'show d-block': isChapterModalActive }">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" v-if="editingChapter">Edit Chapter</h5>
                            <h5 class="modal-title" v-else>Add Chapter</h5>
                            <button type="button" class="close" @click="closeChapterModal" data-dismiss="modal"> &times; </button>
                        </div>
                        <div class="modal-body">
                            <input type="text" class="form-control mb-2" v-model="chapterName" placeholder="Chapter Name">
                            <input type="text" class="form-control" v-model="chapterDescription" placeholder="Chapter Description">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" @click="saveChapter">Save</button>
                            <button type="button" class="btn btn-secondary" @click="closeChapterModal">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="modal" :class="{ 'show d-block': isSubjectModalActive }" style="background-color: rgba(0, 0, 0, 0.5);">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Add Subject</h5>
                            <button type="button" class="close" @click="closeSubjectModal" data-dismiss="modal"> &times; </button>
                        </div>
                        <div class="modal-body">
                            <input type="text" class="form-control mb-2" v-model="subjectName" placeholder="Subject Name">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" @click="saveSubject">Save</button>
                            <button type="button" class="btn btn-secondary" @click="closeSubjectModal">Cancel</button>
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
        };
    },
    mounted() {
        this.fetchSubjects();
    },
    methods: {
        async fetchSubjects() {
            try {
                const data = await api.get('/api/subjects');
                this.subjects = data;
            } catch (error) {
                console.error('Error fetching subjects:', error);
            }
        },
        openEditChapterModal(chapter) {
            this.editingChapter = chapter;
            this.chapterName = chapter.name;
            this.chapterDescription = chapter.description || '';
            this.isChapterModalActive = true;
            document.body.classList.add('modal-open');
        },
        openAddChapterModal(subjectName) {
            console.log('openAddChapterModal called');
            this.editingChapter = null;
            this.chapterName = '';
            this.chapterDescription = '';
            this.selectedSubjectName = subjectName;
            this.isChapterModalActive = true;
            console.log('isChapterModalActive:', this.isChapterModalActive);
            document.body.classList.add('modal-open');
        },
        closeChapterModal() {
            this.isChapterModalActive = false;
            document.body.classList.remove('modal-open');
        },
        openAddSubjectModal() {
            this.subjectName = '';
            this.subjectDescription = '';
            this.isSubjectModalActive = true;
            document.body.classList.add('modal-open');
        },
        closeSubjectModal() {
            this.isSubjectModalActive = false;
            document.body.classList.remove('modal-open');
        },
        async saveChapter() {
            console.log('saveChapter called');
            try {
                const chapterData = {
                    name: this.chapterName,
                    description: this.chapterDescription,
                    subject_name: this.selectedSubjectName
                };

                if (this.editingChapter) {
                    await api.put(`/api/chapters/${this.editingChapter.id}`, chapterData);
                } else {
                    await api.post('/api/chapters', chapterData);
                }

                await this.fetchSubjects();
                this.closeChapterModal();
            } catch (error) {
                console.error('Error saving chapter:', error);
            }
        },
        async handleDeleteChapter(chapterId) {
            try {
                if (!confirm('Are you sure you want to delete this chapter?')) {
                    return;
                }
                await api.delete(`/api/chapters/${chapterId}`);
                await this.fetchSubjects();
            } catch (error) {
                console.error('Error deleting chapter:', error);
            }
        },
        async saveSubject() {
            try {
                await api.post('/api/subjects', {
                    name: this.subjectName,
                });
                await this.fetchSubjects();
                this.closeSubjectModal();
            } catch (error) {
                console.error('Error saving subject:', error);
            }
        }
    }
};

export default HomeAdmin;