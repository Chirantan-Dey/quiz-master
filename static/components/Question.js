const Question = {
  template: `
    <tr>
      <td>{{ text }}</td>
      <td>{{ option1 }}</td>
      <td>{{ option2 }}</td>
      <td>{{ correctAnswer }}</td>
      <td>{{ quiz }}</td>
      <td>{{ creator }}</td>
    </tr>
  `,
  props: {
    text: {
      type: String,
      required: true,
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
};

export default Question;
