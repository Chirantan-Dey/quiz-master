const Question = {
  template: `
    <tr>
      <td>{{ text }}</td>
      <td>{{ quiz }}</td>
      <td>{{ creator }}</td>
    </tr>
  `,
  props: {
    text: {
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
