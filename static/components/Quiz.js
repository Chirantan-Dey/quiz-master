const Quiz = {
  template: `
    <tr>
      <td>{{ name }}</td>
      <td>{{ description }}</td>
      <td>{{ creator }}</td>
    </tr>
  `,
  props: {
    name: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: true,
    },
    creator: {
      type: String,
      required: true,
    },
  },
};

export default Quiz;
