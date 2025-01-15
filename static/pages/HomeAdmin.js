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
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="chapter in subject.chapters" :key="chapter.id">
              <td>{{ chapter.name }}</td>
              <td>
                <button class="btn btn-sm btn-primary mr-2" @click="handleEditChapter(chapter.id)">Edit</button>
                <button class="btn btn-sm btn-danger" @click="handleDeleteChapter(chapter.id)">Delete</button>
              </td>
            </tr>
            <tr>
              <td colspan="2">
                <button class="btn btn-sm btn-success" @click="handleAddChapter(subject.name)">Add Chapter</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <button class="btn btn-primary" @click="handleAddSubject">Add Subject</button>
    </div>
  `,
  data() {
    return {
      subjects: [],
    };
  },
  mounted() {
    this.fetchSubjects();
  },
  methods: {
    async fetchSubjects() {
      try {
        const response = await fetch('/api/subjects');
        const data = await response.json();
        this.subjects = data;
      } catch (error) {
        console.error('Error fetching subjects:', error);
      }
    },
    handleEditChapter(chapterId) {
      // Implement edit chapter logic
      console.log('Edit chapter:', chapterId);
    },
    handleDeleteChapter(chapterId) {
      // Implement delete chapter logic
      console.log('Delete chapter:', chapterId);
    },
    handleAddChapter(subjectName) {
      // Implement add chapter logic
      console.log('Add chapter to:', subjectName);
    },
      handleAddSubject() {
          // Implement add subject logic
          console.log('Add subject');
      }
  },
};

export default HomeAdmin;