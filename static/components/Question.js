const Question = {
  template: `
    <tr>
      <td>{{ question.id }}</td>
      <td>
        {{ question.question_statement }}
        <div class="d-md-none">
          <small class="text-muted d-block">Option 1: {{ question.option1 }}</small>
          <small class="text-muted d-block">Option 2: {{ question.option2 }}</small>
          <small class="text-muted d-block">Answer: {{ question.correct_answer }}</small>
        </div>
      </td>
      <td class="d-none d-md-table-cell">{{ question.option1 }}</td>
      <td class="d-none d-md-table-cell">{{ question.option2 }}</td>
      <td class="d-none d-md-table-cell">{{ question.correct_answer }}</td>
      <td v-if="isAdmin">
        <div class="btn-group btn-group-sm">
          <button class="btn btn-primary" @click="$emit('edit', question)">Edit</button>
          <button class="btn btn-danger" @click="$emit('delete', question.id)">Delete</button>
        </div>
      </td>
    </tr>
  `,
  props: {
    question: {
      type: Object,
      required: true,
      validator: function(obj) {
        return obj.hasOwnProperty('id') &&
               obj.hasOwnProperty('question_statement') &&
               obj.hasOwnProperty('option1') &&
               obj.hasOwnProperty('option2') &&
               obj.hasOwnProperty('correct_answer')
      }
    },
    isAdmin: {
      type: Boolean,
      default: false
    }
  }
};

export default Question;
