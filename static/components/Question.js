const Question = {
  template: `
    <tr>
      <td>{{ question.id }}</td>
      <td>{{ question.question_statement }}</td>
      <td>{{ question.option1 }}</td>
      <td>{{ question.option2 }}</td>
      <td>{{ question.correct_answer }}</td>
      <td v-if="isAdmin">
        <button class="btn btn-sm btn-primary mr-2" @click="$emit('edit', question)">Edit</button>
        <button class="btn btn-sm btn-danger" @click="$emit('delete', question.id)">Delete</button>
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
