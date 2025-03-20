const Question = {
  template: `
<<<<<<< Updated upstream
    <tr>
      <td>{{ text }}</td>
      <td>{{ option1 }}</td>
      <td>{{ option2 }}</td>
      <td>{{ correctAnswer }}</td>
      <td>{{ quiz }}</td>
      <td>{{ creator }}</td>
=======
    <tr :class="{ 'table-active': isLoading }">
      <td>{{ question.id }}</td>
      <td>
        <div class="d-flex flex-column">
          <span>{{ question.question_statement }}</span>
          <small v-if="error" class="text-danger">{{ error }}</small>
        </div>
      </td>
      <td>{{ question.option1 }}</td>
      <td>{{ question.option2 }}</td>
      <td>{{ question.correct_answer }}</td>
      <td v-if="isAdmin" class="text-nowrap">
        <button 
          class="btn btn-sm btn-primary me-2" 
          @click="handleEdit"
          :disabled="isLoading"
        >
          {{ isLoading ? 'Loading...' : 'Edit' }}
        </button>
        <button 
          class="btn btn-sm btn-danger" 
          @click="handleDelete"
          :disabled="isLoading"
        >
          {{ isLoading ? 'Loading...' : 'Delete' }}
        </button>
      </td>
>>>>>>> Stashed changes
    </tr>
  `,
  props: {
    text: {
      type: String,
      required: true,
<<<<<<< Updated upstream
    },
    option1: {
      type: String,
      required: true,
    },
    option2: {
      type: String,
      required: true,
    },
    correctAnswer: {
        type: String,
        required: true,
    },
    quiz: {
      type: String,
      required: true,
    },
    creator: {
      type: String,
      required: true,
    },
  },
=======
      validator: function(obj) {
        // Required fields
        const requiredFields = [
          'id',
          'question_statement',
          'option1',
          'option2',
          'correct_answer'
        ];

        // Check if all required fields exist and have valid values
        return requiredFields.every(field => {
          return obj.hasOwnProperty(field) && 
                 obj[field] !== null && 
                 obj[field] !== undefined &&
                 (typeof obj[field] === 'string' || typeof obj[field] === 'number');
        });
      }
    },
    isAdmin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isLoading: false,
      error: null
    };
  },
  methods: {
    handleEdit() {
      this.error = null;
      this.isLoading = true;
      try {
        this.$emit('edit', this.question);
      } catch (error) {
        this.error = 'Failed to edit question';
        console.error('Edit error:', error);
      } finally {
        this.isLoading = false;
      }
    },
    async handleDelete() {
      if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
        return;
      }

      this.error = null;
      this.isLoading = true;
      try {
        this.$emit('delete', this.question.id);
      } catch (error) {
        this.error = 'Failed to delete question';
        console.error('Delete error:', error);
      } finally {
        this.isLoading = false;
      }
    }
  }
>>>>>>> Stashed changes
};

export default Question;
